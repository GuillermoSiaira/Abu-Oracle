# AI Oracle - Cloud Run Deployment Script
# Prerequisitos:
# 1. Google Cloud CLI instalado (gcloud)
# 2. Proyecto de Google Cloud creado
# 3. Billing habilitado
# 4. APIs habilitadas: Cloud Run, Cloud Build, Secret Manager

# Variables de configuración
$PROJECT_ID = "abu-oracle"       # Tu project ID de Google Cloud
$REGION = "us-central1"          # Región más cercana
$ABU_SERVICE = "abu-engine"
$LILLY_SERVICE = "lilly-engine"

Write-Host "=== AI Oracle - Cloud Run Deployment ===" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Configurar proyecto
Write-Host "1. Configurando proyecto..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Paso 2: Habilitar APIs necesarias
Write-Host "2. Habilitando APIs de Google Cloud..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Paso 3: Crear secreto para OpenAI API Key
Write-Host "3. Configurando secretos..." -ForegroundColor Yellow

# Leer OpenAI API Key desde .env
$envFile = Get-Content .env -ErrorAction SilentlyContinue
$OPENAI_KEY_PLAIN = ($envFile | Select-String "^OPENAI_API_KEY=(.+)$").Matches.Groups[1].Value

if (-not $OPENAI_KEY_PLAIN) {
    Write-Host "Error: No se encontró OPENAI_API_KEY en el archivo .env" -ForegroundColor Red
    Write-Host "Ingresa tu OpenAI API Key manualmente:" -ForegroundColor Green
    $OPENAI_KEY = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($OPENAI_KEY)
    $OPENAI_KEY_PLAIN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
} else {
    Write-Host "OpenAI API Key encontrada en .env" -ForegroundColor Green
}

# Crear secreto en Secret Manager
echo $OPENAI_KEY_PLAIN | gcloud secrets create openai-api-key --data-file=- --replication-policy="automatic" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Secreto ya existe, actualizando versión..." -ForegroundColor Yellow
    echo $OPENAI_KEY_PLAIN | gcloud secrets versions add openai-api-key --data-file=-
}

# Paso 4: Desplegar Abu Engine
Write-Host ""
Write-Host "4. Desplegando Abu Engine..." -ForegroundColor Yellow
Push-Location abu_engine
gcloud run deploy $ABU_SERVICE `
    --source . `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 10 `
    --min-instances 0
Pop-Location

# Obtener URL de Abu
$ABU_URL = gcloud run services describe $ABU_SERVICE --region $REGION --format "value(status.url)"
Write-Host "Abu Engine desplegado en: $ABU_URL" -ForegroundColor Green

# Paso 5: Desplegar Lilly Engine
Write-Host ""
Write-Host "5. Desplegando Lilly Engine..." -ForegroundColor Yellow
Push-Location lilly_engine
gcloud run deploy $LILLY_SERVICE `
    --source . `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 10 `
    --min-instances 0 `
    --set-secrets OPENAI_API_KEY=openai-api-key:latest `
    --set-env-vars "ABU_URL=$ABU_URL,DEFAULT_LANGUAGE=es,USE_ASSISTANT_API=false"
Pop-Location

# Obtener URL de Lilly
$LILLY_URL = gcloud run services describe $LILLY_SERVICE --region $REGION --format "value(status.url)"
Write-Host "Lilly Engine desplegado en: $LILLY_URL" -ForegroundColor Green

# Paso 6: Mostrar resumen
Write-Host ""
Write-Host "=== Deployment Completo ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Abu Engine URL:   $ABU_URL" -ForegroundColor Green
Write-Host "Lilly Engine URL: $LILLY_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Documentación interactiva:" -ForegroundColor Yellow
Write-Host "  Abu Swagger:  $ABU_URL/docs" -ForegroundColor White
Write-Host "  Lilly Swagger: $LILLY_URL/docs" -ForegroundColor White
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Probar endpoints en /docs" -ForegroundColor White
Write-Host "2. Crear OpenAI Assistant con Abu URL" -ForegroundColor White
Write-Host "3. Actualizar frontend con las nuevas URLs" -ForegroundColor White
Write-Host ""

# Guardar URLs en archivo
$OUTPUT_FILE = "cloud-run-urls.txt"
@"
Abu Engine: $ABU_URL
Lilly Engine: $LILLY_URL
Deployed: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@ | Out-File -FilePath $OUTPUT_FILE -Encoding UTF8

Write-Host "URLs guardadas en: $OUTPUT_FILE" -ForegroundColor Cyan
