output "state_machine_arn" { value = module.sfn.state_machine_arn }
output "event_queue_url" { value = module.event_queue.queue_url }
output "notification_queue_url" { value = module.notification_queue.queue_url }
output "enricher_lambda" { value = module.enricher_lambda.function_name }
output "notifier_lambda" { value = module.notifier_lambda.function_name }
