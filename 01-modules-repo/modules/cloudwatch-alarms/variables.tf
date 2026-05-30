variable "name" {
  type = string
}
variable "tags" {
  type = map(string)
  default = {}
}
variable "queue_name" {
  type = string
}

variable "dlq_name" {
  type = string
}

variable "max_receive_count" {
  type    = number
  default = 3
}

variable "visibility_timeout_seconds" {
  type    = number
  default = 30
}

variable "message_retention_seconds" {
  type    = number
  default = 345600
}

