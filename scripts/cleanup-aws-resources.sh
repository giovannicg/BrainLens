#!/bin/bash

# Script para limpiar recursos de AWS cuando terraform destroy falla
# Uso: ./scripts/cleanup-aws-resources.sh

set -e

AWS_REGION="eu-north-1"
PROJECT_NAME="brainlens"

echo "🧹 Iniciando limpieza de recursos de AWS..."

# Función para verificar si AWS CLI está configurado
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo "❌ AWS CLI no está instalado"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "❌ AWS CLI no está configurado correctamente"
        exit 1
    fi
    
    echo "✅ AWS CLI configurado correctamente"
}

# Función para limpiar repositorios ECR
cleanup_ecr() {
    echo "🗑️ Limpiando repositorios ECR..."
    
    for repo in brainlens-auth brainlens-image brainlens-annotation brainlens-colab brainlens-frontend; do
        echo "Limpiando repositorio: $repo"
        
        # Listar todas las imágenes
        images=$(aws ecr list-images --repository-name $repo --region $AWS_REGION --query 'imageIds[*]' --output json 2>/dev/null || echo "[]")
        
        if [ "$images" != "[]" ]; then
            # Eliminar todas las imágenes
            aws ecr batch-delete-image --repository-name $repo --region $AWS_REGION --image-ids "$images" 2>/dev/null || true
            echo "  ✅ Imágenes eliminadas de $repo"
        else
            echo "  ℹ️ No hay imágenes en $repo"
        fi
        
        # Eliminar el repositorio
        aws ecr delete-repository --repository-name $repo --region $AWS_REGION --force 2>/dev/null || true
        echo "  ✅ Repositorio $repo eliminado"
    done
}

# Función para limpiar buckets S3
cleanup_s3() {
    echo "🗑️ Limpiando buckets S3..."
    
    # Buscar buckets que coincidan con el patrón del proyecto
    buckets=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '$PROJECT_NAME-')].Name" --output text 2>/dev/null || echo "")
    
    if [ -n "$buckets" ]; then
        for bucket in $buckets; do
            echo "Limpiando bucket: $bucket"
            
            # Eliminar todas las versiones de objetos
            aws s3api delete-objects --bucket $bucket --delete "$(aws s3api list-object-versions --bucket $bucket --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' --output json)" 2>/dev/null || true
            
            # Eliminar marcadores de eliminación
            aws s3api delete-objects --bucket $bucket --delete "$(aws s3api list-object-versions --bucket $bucket --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' --output json)" 2>/dev/null || true
            
            # Eliminar el bucket
            aws s3api delete-bucket --bucket $bucket --region $AWS_REGION 2>/dev/null || true
            echo "  ✅ Bucket $bucket eliminado"
        done
    else
        echo "  ℹ️ No se encontraron buckets para limpiar"
    fi
}

# Función para limpiar recursos de EKS
cleanup_eks() {
    echo "🗑️ Limpiando recursos de EKS..."
    
    # Verificar si el cluster existe
    if aws eks describe-cluster --name brainlens-eks --region $AWS_REGION &> /dev/null; then
        echo "  ⚠️ Cluster EKS 'brainlens-eks' existe. Elimínalo manualmente desde la consola de AWS."
        echo "  O ejecuta: aws eks delete-cluster --name brainlens-eks --region $AWS_REGION"
    else
        echo "  ℹ️ Cluster EKS no existe"
    fi
}

# Función para limpiar Load Balancers
cleanup_load_balancers() {
    echo "🗑️ Limpiando Load Balancers..."
    
    # ELB v2 (Application/Network Load Balancers)
    elb_v2_arns=$(aws elbv2 describe-load-balancers --region $AWS_REGION --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME')].LoadBalancerArn" --output text 2>/dev/null || echo "")
    
    if [ -n "$elb_v2_arns" ]; then
        for arn in $elb_v2_arns; do
            echo "Eliminando Load Balancer: $arn"
            aws elbv2 delete-load-balancer --load-balancer-arn $arn --region $AWS_REGION 2>/dev/null || true
        done
    fi
    
    # ELB v1 (Classic Load Balancers)
    elb_v1_names=$(aws elb describe-load-balancers --region $AWS_REGION --query "LoadBalancerDescriptions[?contains(LoadBalancerName, '$PROJECT_NAME')].LoadBalancerName" --output text 2>/dev/null || echo "")
    
    if [ -n "$elb_v1_names" ]; then
        for name in $elb_v1_names; do
            echo "Eliminando Classic Load Balancer: $name"
            aws elb delete-load-balancer --load-balancer-name $name --region $AWS_REGION 2>/dev/null || true
        done
    fi
}

# Función para limpiar Security Groups
cleanup_security_groups() {
    echo "🗑️ Limpiando Security Groups..."
    
    # Obtener security groups que no son por defecto y contienen el nombre del proyecto
    sg_ids=$(aws ec2 describe-security-groups --region $AWS_REGION --query "SecurityGroups[?GroupName != 'default' && contains(GroupName, '$PROJECT_NAME')].GroupId" --output text 2>/dev/null || echo "")
    
    if [ -n "$sg_ids" ]; then
        for sg_id in $sg_ids; do
            echo "Eliminando Security Group: $sg_id"
            aws ec2 delete-security-group --group-id $sg_id --region $AWS_REGION 2>/dev/null || true
        done
    else
        echo "  ℹ️ No se encontraron Security Groups para limpiar"
    fi
}

# Función para limpiar VPCs
cleanup_vpcs() {
    echo "🗑️ Limpiando VPCs..."
    
    # Obtener VPCs que contienen el nombre del proyecto
    vpc_ids=$(aws ec2 describe-vpcs --region $AWS_REGION --query "Vpcs[?contains(Tags[?Key=='Name'].Value, '$PROJECT_NAME')].VpcId" --output text 2>/dev/null || echo "")
    
    if [ -n "$vpc_ids" ]; then
        for vpc_id in $vpc_ids; do
            echo "⚠️ VPC $vpc_id encontrada. Elimínala manualmente desde la consola de AWS."
            echo "  Asegúrate de eliminar primero: subnets, internet gateways, route tables, etc."
        done
    else
        echo "  ℹ️ No se encontraron VPCs para limpiar"
    fi
}

# Función principal
main() {
    echo "🚀 Iniciando limpieza de recursos de AWS para el proyecto: $PROJECT_NAME"
    echo "📍 Región: $AWS_REGION"
    echo ""
    
    check_aws_cli
    echo ""
    
    cleanup_ecr
    echo ""
    
    cleanup_s3
    echo ""
    
    cleanup_load_balancers
    echo ""
    
    cleanup_security_groups
    echo ""
    
    cleanup_eks
    echo ""
    
    cleanup_vpcs
    echo ""
    
    echo "✅ Limpieza completada!"
    echo ""
    echo "⚠️ Recursos que pueden requerir limpieza manual:"
    echo "  - VPCs y sus componentes (subnets, internet gateways, route tables)"
    echo "  - Cluster EKS"
    echo "  - IAM roles y políticas"
    echo ""
    echo "💡 Después de la limpieza manual, ejecuta:"
    echo "  terraform destroy -auto-approve"
}

# Ejecutar función principal
main "$@"
