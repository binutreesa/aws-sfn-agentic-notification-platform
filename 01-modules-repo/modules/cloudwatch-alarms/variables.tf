variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_function_names" {
  type = list(string)
}

variable "queue_names" {
  type = list(string)
}

variable "dlq_names" {
  type = list(string)
}

variable "alarm_email" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
