output "app_public_ip" {
  description = "IP pública de la instancia EC2"
  value       = aws_instance.app.public_ip
}

output "db_endpoint" {
  description = "Endpoint de conexión a RDS"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "ecr_repository_url" {
  description = "URL del repositorio ECR para subir la imagen Docker"
  value       = aws_ecr_repository.app.repository_url
}
