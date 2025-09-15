output "ecr_frontend_uri" {
  value = aws_ecr_repository.frontend.repository_url
}
output "ecr_image_uri" {
  value = aws_ecr_repository.image.repository_url
}
output "ecr_auth_uri" {
  value = aws_ecr_repository.auth.repository_url
}
output "ecr_colab_uri" {
  value = aws_ecr_repository.colab.repository_url
}
output "ecr_annotation_uri" {
  value = aws_ecr_repository.annotation.repository_url
}
output "alb_dns" {
  value = aws_lb.alb.dns_name
}

output "auth_url" {
  value = "http://${aws_lb.alb.dns_name}/api/v1/auth"
}

output "annotation_url" {
  value = "http://${aws_lb.alb.dns_name}/api/v1/annotations"
}

output "colab_url" {
  value = "http://${aws_lb.alb.dns_name}/api/v1/colab"
}

output "images_url" {
  value = "http://${aws_lb.alb.dns_name}/api/v1/images"
}

output "frontend_url" {
  value = "http://${aws_lb.alb.dns_name}"
  description = "URL del frontend"
}

output "alb_dns_name" {
  value = aws_lb.alb.dns_name
  description = "DNS name del Application Load Balancer"
}

