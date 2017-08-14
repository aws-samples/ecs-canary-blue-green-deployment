# https://aws.amazon.com/blogs/compute/monitor-cluster-state-with-amazon-ecs-event-stream/
import requests
import json
from requests_aws_sign import AWSV4Sign
from boto3 import session, client
from elasticsearch import Elasticsearch, RequestsHttpConnection

es_host = '<insert your own Amazon ElasticSearch endpoint here>'
sns_topic = '<insert your own SNS topic ARN here>'

def lambda_handler(event, context):
    # Establish credentials
    session_var = session.Session()
    credentials = session_var.get_credentials()
    region = session_var.region_name or 'us-east-1'

    # Check to see if this event is a task event and, if so, if it contains
    # information about an event failure. If so, send an SNS notification.
    if "detail-type" not in event:
        raise ValueError("ERROR: event object is not a valid CloudWatch Logs event")
    else:
        if event["detail-type"] == "ECS Task State Change":
            detail = event["detail"]
            if detail["lastStatus"] == "STOPPED":
                if detail["stoppedReason"] == "Essential container in task exited":
                  # Send an error status message.
                  sns_client = client('sns')
                  sns_client.publish(
                      TopicArn=sns_topic,
                      Subject="ECS task failure detected for container",
                      Message=json.dumps(detail)
                  )

    # Elasticsearch connection. Note that you must sign your requests in order
    # to call the Elasticsearch API anonymously. Use the requests_aws_sign
    # package for this.
    service = 'es'
    auth=AWSV4Sign(credentials, region, service)
    es_client = Elasticsearch(host=es_host,
                              port=443,
                              connection_class=RequestsHttpConnection,
                              http_auth=auth,
                              use_ssl=True,
                              verify_ssl=True)

    es_client.index(index="ecs-index", doc_type="eventstream", body=event)
