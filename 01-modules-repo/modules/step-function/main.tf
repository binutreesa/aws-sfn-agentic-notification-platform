data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name               = "${var.name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = var.tags
}

resource "aws_sfn_state_machine" "this" {
  name     = var.name
  role_arn = aws_iam_role.this.arn

  definition = jsonencode({
    Comment = "Dummy state machine for status-change notification testing"
    StartAt = "CheckInput"
    States = {
      CheckInput = {
        Type = "Choice"
        Choices = [{
          Variable      = "$.shouldFail"
          BooleanEquals = true
          Next          = "FailState"
        }]
        Default = "SuccessState"
      }
      SuccessState = {
        Type = "Succeed"
      }
      FailState = {
        Type  = "Fail"
        Error = "DemoFailure"
        Cause = "Input requested failure"
      }
    }
  })

  tags = var.tags
}
