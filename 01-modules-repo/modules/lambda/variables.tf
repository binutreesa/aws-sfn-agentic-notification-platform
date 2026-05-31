variable "function_name" {
  type = string
}

variable "handler" {
  type    = string
  default = "app.lambda_handler"
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

variable "source_file" {
  type    = string
  default = null
}

variable "source_dir" {
  type    = string
  default = null
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "policy_json" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "create_custom_policy" {
  type    = bool
  default = false
}

