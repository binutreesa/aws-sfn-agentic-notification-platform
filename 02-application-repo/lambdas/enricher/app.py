import json
import os
import boto3

sqs = boto3.client("sqs")

NOTIFIER_QUEUE_URL = os.environ["NOTIFIER_QUEUE_URL"]


def lambda_handler(event, context):
    """Consumes Step Functions status-change events from SQS, enriches them, and forwards to notifier queue."""
    for record in event.get("Records", []):
        raw_event = json.loads(record["body"])
        detail = raw_event.get("detail", {})

        enriched = {
            "notificationType": "STEP_FUNCTION_EXECUTION_STATUS_CHANGE",
            "status": detail.get("status"),
            "stateMachineArn": detail.get("stateMachineArn"),
            "executionArn": detail.get("executionArn"),
            "name": detail.get("name"),
            "startDate": detail.get("startDate"),
            "stopDate": detail.get("stopDate"),
            "error": detail.get("error"),
            "cause": detail.get("cause"),
            "summary": f"Step Function execution {detail.get('name')} finished with status {detail.get('status')}",
            "agenticSummary": "Placeholder. Agentic AI/MCP root-cause summary will be added in the next phase."
        }

        sqs.send_message(
            QueueUrl=NOTIFIER_QUEUE_URL,
            MessageBody=json.dumps(enriched)
        )

    return {"statusCode": 200, "processed": len(event.get("Records", []))}
