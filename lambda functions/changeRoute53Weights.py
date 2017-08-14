from __future__ import print_function

import boto3
import json
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


client = boto3.client('route53')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') # dynamodb.us-east-1.amazonaws.com

def change_weights(blue_weight, green_weight, HostedZoneID, LBZoneID, ServiceName, fromDNS, toDNS): 
    response = client.change_resource_record_sets(
  
            HostedZoneId = HostedZoneID,
            ChangeBatch={
                'Comment': 'alter Route53 records sets for canary blue-green deployment',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': ServiceName,
                            'Type': 'A',
                            'SetIdentifier': 'blue',
                            'Weight': blue_weight,
                            'AliasTarget': {
                                'HostedZoneId': LBZoneID,
                                'DNSName': fromDNS,
                                'EvaluateTargetHealth': False
                                }
                            }
                        },
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': ServiceName,
                            'Type': 'A',
                            'SetIdentifier': 'green',
                            'Weight': green_weight,
                            'AliasTarget': {
                                'HostedZoneId': LBZoneID, 
                                'DNSName': toDNS,
                                'EvaluateTargetHealth': False
                                }
                            }
                        },
                    ]
                }
            )
    return response

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
        print(json.dumps(item, indent=4))
        
        green_weight = event['weight']
        blue_weight = 100-event['weight']
        HostedZoneID = item['HostedZoneID']
        LBZoneID = item['LBZoneID']
        ServiceName = item['RecordName']
        fromDNS = item['OldLB']
        toDNS = item['NewLB']
    
        resp = change_weights(blue_weight, green_weight, HostedZoneID, LBZoneID, ServiceName, fromDNS, toDNS)
        return 'Route53 weight change pending'