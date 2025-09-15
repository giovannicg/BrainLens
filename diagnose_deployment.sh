#!/bin/bash

# Script de diagnóstico para BrainLens Deployment
echo "🔍 Diagnóstico de BrainLens Deployment"
echo "======================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo ""
echo "1. Verificando configuración de Terraform..."
if [ -f "infra/terraform/main.tf" ]; then
    print_status "Archivo main.tf encontrado" 0
else
    print_status "Archivo main.tf NO encontrado" 1
    exit 1
fi

echo ""
echo "2. Verificando variables de entorno..."
if [ -f ".env" ]; then
    print_status "Archivo .env encontrado" 0
    
    # Verificar variables críticas
    if grep -q "MONGODB_URL" .env; then
        print_status "MONGODB_URL configurado" 0
    else
        print_warning "MONGODB_URL no encontrado en .env"
    fi
    
    if grep -q "JWT_SECRET_KEY" .env; then
        print_status "JWT_SECRET_KEY configurado" 0
    else
        print_warning "JWT_SECRET_KEY no encontrado en .env"
    fi
    
    if grep -q "ENVIRONMENT" .env; then
        print_status "ENVIRONMENT configurado" 0
    else
        print_warning "ENVIRONMENT no encontrado en .env"
    fi
else
    print_warning "Archivo .env no encontrado - copia env.example a .env"
fi

echo ""
echo "3. Verificando servicios..."
services=("auth-service" "image-service" "annotation-service" "colab-service" "frontend-service")

for service in "${services[@]}"; do
    if [ -f "services/$service/src/main.py" ] || [ -f "services/$service/src/main.tsx" ]; then
        print_status "$service encontrado" 0
    else
        print_status "$service NO encontrado" 1
    fi
done

echo ""
echo "4. Verificando health endpoints..."

# Verificar auth service
if grep -q "/api/v1/auth/health" services/auth-service/src/main.py; then
    print_status "Auth service health endpoint configurado" 0
else
    print_status "Auth service health endpoint NO configurado" 1
fi

# Verificar image service
if grep -q "/api/v1/images/health" services/image-service/src/main.py; then
    print_status "Image service health endpoint configurado" 0
else
    print_status "Image service health endpoint NO configurado" 1
fi

# Verificar annotation service
if grep -q "/api/v1/annotations/health" services/annotation-service/src/main.py; then
    print_status "Annotation service health endpoint configurado" 0
else
    print_status "Annotation service health endpoint NO configurado" 1
fi

# Verificar colab service
if grep -q "/health" services/colab-service/src/main.py; then
    print_status "Colab service health endpoint configurado" 0
else
    print_status "Colab service health endpoint NO configurado" 1
fi

echo ""
echo "5. Verificando configuración CORS..."

# Verificar que todos los servicios tengan configuración CORS dinámica
for service in "${services[@]}"; do
    if [ "$service" = "frontend-service" ]; then
        continue  # Frontend no necesita CORS
    fi
    
    if grep -q "get_cors_origins\|ALLOW_ORIGINS" "services/$service/src/main.py" 2>/dev/null || grep -q "ALLOW_ORIGINS" "services/$service/src/config.py" 2>/dev/null; then
        print_status "$service CORS configurado" 0
    else
        print_status "$service CORS NO configurado" 1
    fi
done

echo ""
echo "6. Verificando GitHub Actions..."
if [ -f ".github/workflows/ecr-publish.yml" ]; then
    print_status "Workflow ECR encontrado" 0
else
    print_status "Workflow ECR NO encontrado" 1
fi

echo ""
echo "7. Verificando Dockerfiles..."
for service in "${services[@]}"; do
    if [ -f "services/$service/Dockerfile" ]; then
        print_status "$service Dockerfile encontrado" 0
    else
        print_status "$service Dockerfile NO encontrado" 1
    fi
done

echo ""
echo "======================================"
echo "📋 Próximos pasos recomendados:"
echo ""
echo "1. Si hay errores ❌, corrígelos primero"
echo "2. Configura las variables de GitHub Actions:"
echo "   - Ve a Settings > Secrets and variables > Actions"
echo "   - Añade las variables y secrets necesarios"
echo "3. Ejecuta: terraform plan -var='mongo_url=tu_mongodb_url'"
echo "4. Ejecuta: terraform apply -var='mongo_url=tu_mongodb_url'"
echo "5. Haz push a main para trigger el deploy"
echo ""
echo "🔧 Para más ayuda, revisa DEPLOY_PRODUCTION.md"
