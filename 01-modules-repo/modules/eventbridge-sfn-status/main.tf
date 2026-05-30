resource "aws_cloudwatch_event_rule" "this" {
  name        = var.name
  description = "Routes Step Functions execution status changes to SQS"

  event_pattern = jsonencode({
    source        = ["aws.states"]
    "detail-type" = ["Step Functions Execution Status Change"]
    detail = {
      stateMachineArn = [var.state_machine_arn]
      status          = var.statuses
    }
  })

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "sqs" {
  rule      = aws_cloudwatch_event_rule.this.name
  target_id = "SendToSqs"
  arn       = var.target_queue_arn
}

data "aws_iam_policy_document" "sqs_policy" {
  statement {
    sid       = "AllowEventBridgeSendMessage"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [var.target_queue_arn]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.this.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "allow_eventbridge" {
  queue_url = var.target_queue_url
  policy    = data.aws_iam_policy_document.sqs_policy.json
}
