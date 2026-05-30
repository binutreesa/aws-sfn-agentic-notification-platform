import json
import os
import boto3

ses = boto3.client("ses")

FROM_EMAIL = os.environ["FROM_EMAIL"]
TO_EMAIL = os.environ["TO_EMAIL"]
TEMPLATE_NAME = os.environ["TEMPLATE_NAME"]


def lambda_handler(event, context):
    """Consumes enriched notification events and sends SES templated emails."""
    for record in event.get("Records", []):
        message = json.loads(record["body"])

        template_data = {
            "status": message.get("status", "UNKNOWN"),
            "executionName": message.get("name", "UNKNOWN"),
            "stateMachineArn": message.get("stateMachineArn", "UNKNOWN"),
            "executionArn": message.get("executionArn", "UNKNOWN"),
            "summary": message.get("summary", "No summary available"),
            "agenticSummary": message.get("agenticSummary", "Not available"),
            "error": message.get("error", ""),
            "cause": message.get("cause", "")
        }

        ses.send_templated_email(
            Source=FROM_EMAIL,
            Destination={"ToAddresses": [TO_EMAIL]},
            Template=TEMPLATE_NAME,
            TemplateData=json.dumps(template_data)
        )

    return {"statusCode": 200, "processed": len(event.get("Records", []))}
