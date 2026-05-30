# Deployment Guide

## 1. Configure AWS CLI
aws configure

## 2. Verify SES emails first
For SES sandbox accounts, both from_email and to_email must be verified.

## 3. Deploy
cd 03-deployment-repo/dev
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply

## 4. Test success
aws stepfunctions start-execution --state-machine-arn <output-state-machine-arn> --input '{}'

## 5. Test failure
aws stepfunctions start-execution --state-machine-arn <output-state-machine-arn> --input '{"shouldFail": true}'

## 6. Expected flow
Step Functions emits status change event to EventBridge.
EventBridge sends message to SQS.
Enricher Lambda consumes SQS event and creates notification payload.
Notifier Lambda sends SES template email.
