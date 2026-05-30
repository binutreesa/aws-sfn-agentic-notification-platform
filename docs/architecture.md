# Architecture

## Phase 1 AWS Backbone
Step Functions -> EventBridge Rule -> SQS Event Queue -> Enricher Lambda -> SQS Notification Queue -> Notifier Lambda -> SES Template

## Why this is enterprise-style
- Event-driven, not polling-based
- SQS decouples EventBridge and Lambda
- DLQ exists for failed messages
- Separate enrichment and notification responsibilities
- SES template externalizes email format
- Terraform modules isolate reusable infrastructure
- Environment folder separates dev/test/prod deployments

## Later Agentic AI / MCP Extension
The Enricher Lambda will call an Agent/MCP service to:
- Fetch execution details
- Query CloudWatch logs
- Search runbooks
- Generate root-cause summary
- Recommend next action
