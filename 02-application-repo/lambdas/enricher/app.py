import json
import os
import boto3
from datetime import datetime
from openai import OpenAI

sqs = boto3.client("sqs")
sfn = boto3.client("stepfunctions")
s3 = boto3.client("s3")

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

NOTIFIER_QUEUE_URL = os.environ["NOTIFIER_QUEUE_URL"]


def safe_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def parse_json(value):
    if not value:
        return {}

    if isinstance(value, dict):
        return value

    if isinstance(value, list):
        return value

    try:
        return json.loads(value)
    except Exception:
        return {}


def find_config_location(data):
    """
    Finds config location anywhere in input/output payload.

    Supported examples:
    {
      "dynamic-config": "s3://bucket/path/config.json"
    }

    {
      "dynamicConfig": {
        "bucket": "my-bucket",
        "key": "path/config.json"
      }
    }

    {
      "metadata": {
        "configLocation": "s3://bucket/path/config.json"
      }
    }
    """

    config_keys = {
        "dynamic-config",
        "dynamicconfig",
        "configlocation",
        "configurationlocation",
        "s3configpath"
    }

    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() in config_keys:
                return value

            result = find_config_location(value)
            if result:
                return result

    elif isinstance(data, list):
        for item in data:
            result = find_config_location(item)
            if result:
                return result

    return None


def load_s3_config(config_location):
    """
    Loads JSON config from S3.

    Supported:
    "s3://bucket/key.json"

    or

    {
      "bucket": "bucket-name",
      "key": "path/key.json"
    }
    """

    if not config_location:
        return None

    try:
        bucket = None
        key = None

        if isinstance(config_location, str):
            if not config_location.startswith("s3://"):
                return None

            s3_path = config_location.replace("s3://", "")
            bucket, key = s3_path.split("/", 1)

        elif isinstance(config_location, dict):
            bucket = config_location.get("bucket")
            key = config_location.get("key")

        if not bucket or not key:
            return None

        response = s3.get_object(
            Bucket=bucket,
            Key=key
        )

        body = response["Body"].read().decode("utf-8")

        return json.loads(body)

    except Exception as e:
        print(f"Failed to load S3 config: {str(e)}")
        return None


def extract_business_context_with_ai(
    input_payload,
    output_payload,
    config_payload
):
    """
    Uses AI to identify business context from unknown schema payloads.

    Example config_payload may look like:
    {
      "batchRequirement": "FinCrime",
      "clientEmail": true,
      "unique_id": "1234-789...",
      "metadata": {...}
    }
    """

    try:
        prompt = f"""
                You are an enterprise AWS Step Functions payload analyst.
                
                Your task is to extract normalized business context from the provided payloads.
                
                Important rules:
                
                1. The unique identifier may appear anywhere in input, output, or config.
                2. The unique identifier may use field names like:
                   - uuid
                   - UUID
                   - uniqueId
                   - uniqueID
                   - uniqueid
                   - unique_id
                   - unique-id
                   - requestId
                   - applicationId
                   - customerReference
                3. There may be multiple IDs. Choose the most likely business identifier, not technical correlation IDs.
                4. The batchRequirement may appear anywhere in input, output, or config.
                5. batchRequirement may actually contain the product name.
                   Example:
                   "batchRequirement": "FinCrime"
                   means product = "FinCrime".
                   5.1batch requirement may also be expressed as "product" or "batch_requirement" or "BatchRequirement".
                6. clientEmail is a client mail id.
                7. The payload may be an object, deeply nested object, or list of objects.
                8. If dynamic config is available, use it as additional product/configuration context.
                9. Return ONLY valid JSON. Do not include explanation outside JSON.
                
                Return JSON in this exact structure:
                
                {{
                  "unique_id": "",
                  "unique_id_field": "",
                  "clientEmailId": "",
                  "batchRequirement": "",
                  "correlationId": "",
                  "customerId": "",
                  "environment": "",
                  "confidence": "low|medium|high",
                  "reasoning": ""
                }}
                
                Step Function Input:
                {json.dumps(input_payload, indent=2, default=str)}
                
                Step Function Output:
                {json.dumps(output_payload, indent=2, default=str)}
                
                Dynamic Config:
                {json.dumps(config_payload, indent=2, default=str)}
                """

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured business context from enterprise JSON payloads."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content.strip()

        return json.loads(content)

    except Exception as e:
        print(f"AI context extraction failed: {str(e)}")

        return {
            "businessId": "",
            "businessIdField": "",
            "product": "",
            "productField": "",
            "clientEmailRequired": False,
            "batchRequirement": "",
            "correlationId": "",
            "customerId": "",
            "environment": "",
            "confidence": "low",
            "reasoning": "AI extraction failed; fallback context used."
        }


def generate_failure_summary(
    status,
    error,
    cause,
    business_context,
    input_payload
):
    if status != "FAILED":
        return f"Execution completed with status {status}."

    try:
        prompt = f"""
                You are an AWS Step Functions incident analyst.
                
                Analyze this Step Function failure and provide a short operational summary.
                
                Status:
                {status}
                
                Error:
                {error}
                
                Cause:
                {cause}
                
                Business Context:
                {json.dumps(business_context, indent=2, default=str)}
                
                Input Payload:
                {json.dumps(input_payload, indent=2, default=str)}
                
                Return a concise summary with:
                1. Root Cause
                2. Business Impact
                3. Recommended Actions
                
                Maximum 150 words.
                """

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AWS incident analyst."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"AI failure summary failed: {str(e)}")


        return (
            f"Execution failed. "
            f"Error={error}. "
            f"Cause={cause}. "
            f"BusinessId={business_context.get('businessId')}. "
            f"Product={business_context.get('product')}."
        )


def lambda_handler(event, context):
    processed = 0

    for record in event.get("Records", []):

        try:
            raw_event = json.loads(record["body"])
            detail = raw_event.get("detail", {})

            execution_arn = detail.get("executionArn")
            execution_details = {}

            if execution_arn:
                try:
                    execution_details = sfn.describe_execution(
                        executionArn=execution_arn
                    )
                except Exception as e:
                    print(
                        f"DescribeExecution failed for "
                        f"{execution_arn}: {str(e)}"
                    )

            status = detail.get("status")
            error = detail.get("error")
            cause = detail.get("cause")

            input_payload = parse_json(
                execution_details.get("input")
            )

            output_payload = parse_json(
                execution_details.get("output")
            )

            config_location = (
                find_config_location(input_payload)
                or find_config_location(output_payload)
            )

            config_payload = load_s3_config(config_location)

            business_context = extract_business_context_with_ai(
                input_payload=input_payload,
                output_payload=output_payload,
                config_payload=config_payload
            )

            agentic_summary = generate_failure_summary(
                status=status,
                error=error,
                cause=cause,
                business_context=business_context,
                input_payload=input_payload
            )

            enriched = {
                "notificationType": "STEP_FUNCTION_EXECUTION_STATUS_CHANGE",

                "status": status,
                "stateMachineArn": detail.get("stateMachineArn"),
                "executionArn": execution_arn,
                "executionName": detail.get("name"),

                "startDate": safe_datetime(
                    execution_details.get("startDate")
                ),
                "stopDate": safe_datetime(
                    execution_details.get("stopDate")
                ),

                "input": input_payload,
                "output": output_payload,

                "configLocation": config_location,
                "configLoaded": config_payload is not None,
                "config": config_payload,

                "businessContext": business_context,

                "uuid": (
                                business_context.get("businessId")
                                or business_context.get("unique_id")
                                or business_context.get("uniqueId")
                                or business_context.get("uuid")
                            ),
                "uuidField": (
                            business_context.get("businessIdField")
                            or business_context.get("unique_id_field")
                            or business_context.get("uniqueIdField")
                            or business_context.get("uuidField")
                        ),

                "product": (
                            business_context.get("product")
                            or business_context.get("batchRequirement")
                        ),
                "productField": business_context.get("productField"),

                "batchRequirement": business_context.get("batchRequirement"),

                "clientEmailRequired": business_context.get(
                    "clientEmailRequired"
                ),

                "correlationId": business_context.get("correlationId"),
                "customerId": business_context.get("customerId"),
                "environment": business_context.get("environment"),

                "confidence": business_context.get("confidence"),
                "reasoning": business_context.get("reasoning"),

                "error": error,
                "cause": cause,

                "summary": (
                    f"Step Function execution "
                    f"{detail.get('name')} "
                    f"finished with status {status}"
                ),

                "agenticSummary": agentic_summary
            }

            print(
                json.dumps(
                    enriched,
                    default=str
                )
            )

            sqs.send_message(
                QueueUrl=NOTIFIER_QUEUE_URL,
                MessageBody=json.dumps(
                    enriched,
                    default=str
                )
            )

            processed += 1

        except Exception as e:
            print(f"Failed processing record: {str(e)}")
            raise

    return {
        "statusCode": 200,
        "processed": processed
    }
