# Script de diagnóstico para BrainLens Deployment
Write-Host "🔍 Diagnóstico de BrainLens Deployment" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Función para imprimir con color
function Write-Status {
    param(
        [string]$Message,
        [bool]$IsSuccess
    )
    
    if ($IsSuccess) {
        Write-Host "✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
    }
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "1. Verificando configuración de Terraform..." -ForegroundColor White
if (Test-Path "infra/terraform/main.tf") {
    Write-Status "Archivo main.tf encontrado" $true
} else {
    Write-Status "Archivo main.tf NO encontrado" $false
    exit 1
}

Write-Host ""
Write-Host "2. Verificando variables de entorno..." -ForegroundColor White
if (Test-Path ".env") {
    Write-Status "Archivo .env encontrado" $true
    
    $envContent = Get-Content ".env" -Raw
    
    # Verificar variables críticas
    if ($envContent -match "MONGODB_URL") {
        Write-Status "MONGODB_URL configurado" $true
    } else {
        Write-Warning "MONGODB_URL no encontrado en .env"
    }
    
    if ($envContent -match "JWT_SECRET_KEY") {
        Write-Status "JWT_SECRET_KEY configurado" $true
    } else {
        Write-Warning "JWT_SECRET_KEY no encontrado en .env"
    }
    
    if ($envContent -match "ENVIRONMENT") {
        Write-Status "ENVIRONMENT configurado" $true
    } else {
        Write-Warning "ENVIRONMENT no encontrado en .env"
    }
} else {
    Write-Warning "Archivo .env no encontrado - copia env.example a .env"
}

Write-Host ""
Write-Host "3. Verificando servicios..." -ForegroundColor White
$services = @("auth-service", "image-service", "annotation-service", "colab-service", "frontend-service")

foreach ($service in $services) {
    $mainFile = "services/$service/src/main.py"
    $mainTsxFile = "services/$service/src/main.tsx"
    
    if ((Test-Path $mainFile) -or (Test-Path $mainTsxFile)) {
        Write-Status "$service encontrado" $true
    } else {
        Write-Status "$service NO encontrado" $false
    }
}

Write-Host ""
Write-Host "4. Verificando health endpoints..." -ForegroundColor White

# Verificar auth service
$authContent = Get-Content "services/auth-service/src/main.py" -Raw -ErrorAction SilentlyContinue
if ($authContent -match "/api/v1/auth/health") {
    Write-Status "Auth service health endpoint configurado" $true
} else {
    Write-Status "Auth service health endpoint NO configurado" $false
}

# Verificar image service
$imageContent = Get-Content "services/image-service/src/main.py" -Raw -ErrorAction SilentlyContinue
if ($imageContent -match "/api/v1/images/health") {
    Write-Status "Image service health endpoint configurado" $true
} else {
    Write-Status "Image service health endpoint NO configurado" $false
}

# Verificar annotation service
$annotationContent = Get-Content "services/annotation-service/src/main.py" -Raw -ErrorAction SilentlyContinue
if ($annotationContent -match "/api/v1/annotations/health") {
    Write-Status "Annotation service health endpoint configurado" $true
} else {
    Write-Status "Annotation service health endpoint NO configurado" $false
}

# Verificar colab service
$colabContent = Get-Content "services/colab-service/src/main.py" -Raw -ErrorAction SilentlyContinue
if ($colabContent -match "/health") {
    Write-Status "Colab service health endpoint configurado" $true
} else {
    Write-Status "Colab service health endpoint NO configurado" $false
}

Write-Host ""
Write-Host "5. Verificando configuración CORS..." -ForegroundColor White

# Verificar que todos los servicios tengan configuración CORS dinámica
foreach ($service in $services) {
    if ($service -eq "frontend-service") {
        continue  # Frontend no necesita CORS
    }
    
    $mainFile = "services/$service/src/main.py"
    $configFile = "services/$service/src/config.py"
    
    $hasCors = $false
    if (Test-Path $mainFile) {
        $content = Get-Content $mainFile -Raw -ErrorAction SilentlyContinue
        if ($content -match "get_cors_origins|ALLOW_ORIGINS") {
            $hasCors = $true
        }
    }
    
    if (Test-Path $configFile) {
        $content = Get-Content $configFile -Raw -ErrorAction SilentlyContinue
        if ($content -match "ALLOW_ORIGINS") {
            $hasCors = $true
        }
    }
    
    if ($hasCors) {
        Write-Status "$service CORS configurado" $true
    } else {
        Write-Status "$service CORS NO configurado" $false
    }
}

Write-Host ""
Write-Host "6. Verificando GitHub Actions..." -ForegroundColor White
if (Test-Path ".github/workflows/ecr-publish.yml") {
    Write-Status "Workflow ECR encontrado" $true
} else {
    Write-Status "Workflow ECR NO encontrado" $false
}

Write-Host ""
Write-Host "7. Verificando Dockerfiles..." -ForegroundColor White
foreach ($service in $services) {
    if (Test-Path "services/$service/Dockerfile") {
        Write-Status "$service Dockerfile encontrado" $true
    } else {
        Write-Status "$service Dockerfile NO encontrado" $false
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "📋 Próximos pasos recomendados:" -ForegroundColor White
Write-Host ""
Write-Host "1. Si hay errores ❌, corrígelos primero" -ForegroundColor Yellow
Write-Host "2. Configura las variables de GitHub Actions:" -ForegroundColor Yellow
Write-Host "   - Ve a Settings > Secrets and variables > Actions" -ForegroundColor Gray
Write-Host "   - Añade las variables y secrets necesarios" -ForegroundColor Gray
Write-Host "3. Ejecuta: terraform plan -var='mongo_url=tu_mongodb_url'" -ForegroundColor Yellow
Write-Host "4. Ejecuta: terraform apply -var='mongo_url=tu_mongodb_url'" -ForegroundColor Yellow
Write-Host "5. Haz push a main para trigger el deploy" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para mas ayuda, revisa DEPLOY_PRODUCTION.md" -ForegroundColor Cyan
