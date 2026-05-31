import json
import os
import boto3

ses = boto3.client("ses")

FROM_EMAIL = os.environ["FROM_EMAIL"]
TO_EMAIL = os.environ["TO_EMAIL"]
TEMPLATE_NAME = os.environ["TEMPLATE_NAME"]


def lambda_handler(event, context):
    processed = 0

    for record in event.get("Records", []):

        try:
            message = json.loads(record["body"])

            template_data = {
                "environment": str(message.get("environment", "")),
                "product": str(message.get("product", "")),

                "requestId": str(message.get("requestId", "")),
                "correlationId": str(message.get("correlationId", "")),
                "customerId": str(message.get("customerId", "")),
                "uuid": str(message.get("uuid", "")),

                "batchRequirement": str(
                    message.get("batchRequirement", "")
                ),

                "batchId": str(
                    message.get("batchId", "")
                ),

                "batchSize": str(
                    message.get("batchSize", "")
                ),

                "executionName": str(
                    message.get("executionName", "")
                ),

                "executionArn": str(
                    message.get("executionArn", "")
                ),

                "status": str(
                    message.get("status", "")
                ),

                "error": str(
                    message.get("error", "")
                ),

                "cause": str(
                    message.get("cause", "")
                ),

                "startDate": str(
                    message.get("startDate", "")
                ),

                "stopDate": str(
                    message.get("stopDate", "")
                ),

                "summary": str(
                    message.get("summary", "")
                ),

                "agenticSummary": str(
                    message.get("agenticSummary", "")
                )
            }

            print(
                json.dumps(
                    template_data,
                    indent=2
                )
            )

            ses.send_templated_email(
                Source=FROM_EMAIL,
                Destination={
                    "ToAddresses": [TO_EMAIL]
                },
                Template=TEMPLATE_NAME,
                TemplateData=json.dumps(
                    template_data
                )
            )

            processed += 1

        except Exception as e:
            print(
                f"Failed processing notification: {str(e)}"
            )
            raise

    return {
        "statusCode": 200,
        "processed": processed
    }
