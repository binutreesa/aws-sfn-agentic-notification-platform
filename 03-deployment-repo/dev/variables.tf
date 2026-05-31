variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "project" {
  type    = string
  default = "sfn-agentic-notification"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "from_email" {
  type = string
}

variable "to_email" {
  type = string
}
variable "project_name" {
  type    = string
  default = "eu-west-1"
}
variable "alarm_email" {
  type = string
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}
