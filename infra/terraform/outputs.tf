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
# Application URLs (LoadBalancer will be created by ingress)
output "application_info" {
  value = {
    frontend_url = "LoadBalancer URL will be available after Kubernetes deployment"
    auth_url = "LoadBalancer URL will be available after Kubernetes deployment"
    image_url = "LoadBalancer URL will be available after Kubernetes deployment"
    annotation_url = "LoadBalancer URL will be available after Kubernetes deployment"
    colab_url = "LoadBalancer URL will be available after Kubernetes deployment"
  }
  description = "Application URLs (LoadBalancer created by Kubernetes ingress)"
}

