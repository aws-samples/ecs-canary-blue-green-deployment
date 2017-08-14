from __future__ import print_function

import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import os 

# ENV Variable: TRIGGER_CONTAINERS = 'green-app'
# ENV Variable: STEP_FUNCTION = Arn_of_StepFunction


client = boto3.client('route53')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') # dynamodb.us-east-1.amazonaws.com
table = dynamodb.Table('CanaryTable')
    
def start_stepfunction(data):
    print("data is " + data)
    stepFunction = os.environ['STEP_FUNCTION']
    print("stepfunction is " + stepFunction)
    client = boto3.client('stepfunctions')
    r = client.start_execution(
        stateMachineArn = stepFunction,
        input = json.dumps({ 'target' : data }))
    # print(r)
    return

def record_execution(target):
    # Change Execution status of variable 'Triggered' to true, so that the Canary will not be started more than once
    try:
        response = table.update_item(
            Key={ 'NewContainerName': target },
            UpdateExpression = 'SET Triggered = :val1',
            ExpressionAttributeValues = {
                ':val1' : True
            },
            ReturnValues='ALL_NEW'
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print(response)
        return
        
def running(target):
    # Has the container tripped a canary execution already?
    try:
        response = table.get_item(
            Key={ 'NewContainerName': target },
            ConsistentRead = True
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        item = response['Item']
        # print(json.dumps(item, indent=4))
        return item['Triggered']
    
def lambda_handler(event, context):
    triggers = os.environ['TRIGGER_CONTAINERS']
    triggered = False
    containers = []
    matches = []

    # For debugging so you can see raw event format.
    print('Here is the event:')
    print(json.dumps(event))

    if event["source"] != "aws.ecs":
       raise ValueError("Function only supports input from events with a source type of: aws.ecs")

    if not (event["detail-type"] == "ECS Task State Change" and \
        event["detail"]["desiredStatus"] == "RUNNING" and \
        event["detail"]["lastStatus"] == "RUNNING"):
        raise ValueError("Function only supports input from events that are Task State Changes and are RUNNING")
    
    # I know my app has two linked containers, so I need to grab the name of the first 2
    if len(event["detail"]["containers"]) == 2:
        containers.append(event["detail"]["containers"][0]["name"]) 
        containers.append(event["detail"]["containers"][1]["name"])

        # Cross reference running containers with TRIGGER containers that we are looking to execute a canary
        for item in containers:
            if item in triggers: 
                matches.append(item)
                triggered = True
    
    if not triggered:
        return
        
    # Kick off blue-green canary change, as long as it has not been kicked off earlier
    for item in matches:
        if not running(item):
            record_execution(item)   # update DB, flip value of Triggered to true
            start_stepfunction(item)
    return