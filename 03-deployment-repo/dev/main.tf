data "aws_caller_identity" "current" {}

module "sfn" {
  source = "../../01-modules-repo/modules/step-function"
  name   = "${local.name_prefix}-demo-sfn"
  tags   = local.common_tags
}

module "event_queue" {
  source = "../../01-modules-repo/modules/sqs"
  name   = "${local.name_prefix}-sfn-events"
  tags   = local.common_tags
}

module "notification_queue" {
  source = "../../01-modules-repo/modules/sqs"
  name   = "${local.name_prefix}-notifications"
  tags   = local.common_tags
}

module "eventbridge" {
  source            = "../../01-modules-repo/modules/eventbridge-sfn-status"
  name              = "${local.name_prefix}-sfn-status-rule"
  state_machine_arn = module.sfn.state_machine_arn
  target_queue_arn  = module.event_queue.queue_arn
  target_queue_url  = module.event_queue.queue_url
  statuses          = ["FAILED", "TIMED_OUT", "SUCCEEDED"]
  tags              = local.common_tags
}

module "email_template" {
  source        = "../../01-modules-repo/modules/ses-template"
  template_name = "${local.name_prefix}-sfn-status-template"
  subject       = "Step Function {{status}}: {{executionName}}"
  html          = file("${path.module}/templates/sfn-status.html")
  text          = file("${path.module}/templates/sfn-status.txt")
}

resource "aws_iam_role_policy" "enricher_sqs_policy" {

  role = module.enricher_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [

      {
        Effect = "Allow"

        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]

        Resource = module.event_queue.queue_arn
      },

      {
        Effect = "Allow"

        Action = [
          "sqs:SendMessage"
        ]

        Resource = module.notification_queue.queue_arn
      }

    ]
  })
}

module "enricher_lambda" {
  source        = "../../01-modules-repo/modules/lambda"
  function_name = "${local.name_prefix}-enricher"
  source_file   = "../../02-application-repo/lambdas/enricher/app.py"
  create_custom_policy = true
  environment_variables = {
    NOTIFIER_QUEUE_URL = module.notification_queue.queue_url
  }

  tags = local.common_tags
}

resource "aws_iam_role_policy" "notifier_policy" {

  role = module.notifier_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [

      {
        Effect = "Allow"

        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]

        Resource = module.notification_queue.queue_arn
      },

      {
        Effect = "Allow"

        Action = [
          "ses:SendEmail",
          "ses:SendTemplatedEmail"
        ]

        Resource = [
          "arn:aws:ses:${var.aws_region}:${data.aws_caller_identity.current.account_id}:identity/${var.from_email}"
        ]
      }

    ]
  })
}

module "notifier_lambda" {
  source        = "../../01-modules-repo/modules/lambda"
  function_name = "${local.name_prefix}-notifier"
  source_file   = "../../02-application-repo/lambdas/notifier/app.py"

  environment_variables = {
    FROM_EMAIL    = var.from_email
    TO_EMAIL      = var.to_email
    TEMPLATE_NAME = module.email_template.template_name
  }

  tags = local.common_tags
}

resource "aws_lambda_event_source_mapping" "event_queue_to_enricher" {
  event_source_arn = module.event_queue.queue_arn
  function_name    = module.enricher_lambda.function_arn
  batch_size        = 10
}

resource "aws_lambda_event_source_mapping" "notification_queue_to_notifier" {
  event_source_arn = module.notification_queue.queue_arn
  function_name    = module.notifier_lambda.function_arn
  batch_size        = 10
}

resource "aws_iam_role_policy" "enricher_send_notification" {
  name = "${local.name_prefix}-enricher-send-notification"
  role = module.enricher_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = module.notification_queue.queue_arn
      }
    ]
  })
}
resource "aws_iam_role_policy" "notifier_send_email" {
  name = "${local.name_prefix}-notifier-send-email"
  role = module.notifier_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendTemplatedEmail"
        ]
        Resource = "*"
      }
    ]
  })
}
