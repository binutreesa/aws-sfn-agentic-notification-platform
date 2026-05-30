variable "name" {
  type = string
}
variable "state_machine_arn" {
  type = string
}
variable "target_queue_arn" {
  type = string
}
variable "statuses" {
  type    = list(string)
  default = ["FAILED", "TIMED_OUT", "SUCCEEDED"]
}
variable "tags" {
  type    = map(string)
  default = {}
}
variable "target_queue_url" {
  type = string
}
