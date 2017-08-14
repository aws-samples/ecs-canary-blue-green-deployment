from __future__ import print_function

import boto3
import json
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


client = boto3.client('elbv2')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') # dynamodb.us-east-1.amazonaws.com

def lambda_handler(event, context):
    # For debugging so you can see raw event format.
    print('Here is the event:')
    print(json.dumps(event))
    
    table = dynamodb.Table('CanaryTable')
    target = event['target']
    
    try:
        response = table.get_item(
            Key={ 'NewContainerName': target }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        item = response['Item']
        print("GetItem succeeded:")
        # print(json.dumps(item, indent=4))
        
        targetGroup = item['TargetGroup']

        health = client.describe_target_health(
            TargetGroupArn = targetGroup
        )
        targetHealth = health['TargetHealthDescriptions'][0]['TargetHealth']['State']
        print(json.dumps(targetHealth, indent=4))

        return targetHealth