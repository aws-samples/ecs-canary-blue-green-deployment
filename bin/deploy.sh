#!/usr/bin/env bash
IFS= read -r -p "Enter S3Bucket to use: " S3Bucket
aws s3 cp canary-setup.yaml s3://"$S3Bucket"
aws s3 cp canary-deployment.yaml s3://"$S3Bucket"
aws s3 cp --recursive templates s3://"$S3Bucket"/templates
aws s3 cp --recursive lambdafunctions s3://"$S3Bucket"/lambdafunctions

aws cloudformation deploy --stack-name canary-setup \
--template-file canary-setup.yaml --capabilities CAPABILITY_NAMED_IAM \
--region us-east-1 \
--parameter-overrides RecordSetName=service1 HostedZoneName=test.io. \
 TemplateBucket="$S3Bucket"


#aws cloudformation deploy --stack-name canary-deployment \
#--template-file canary-deployment.yaml --capabilities CAPABILITY_NAMED_IAM \
#--region us-east-1 \
#--parameter-overrides SetupStackName=canary-setup TemplateBucket="$S3Bucket"