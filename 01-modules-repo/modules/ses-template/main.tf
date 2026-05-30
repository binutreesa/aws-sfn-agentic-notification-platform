resource "aws_ses_template" "this" {
  name    = var.template_name
  subject = var.subject
  html    = var.html
  text    = var.text
}
