# AI Oracle - Cloud Run Deployment Guide

## Prerequisitos

1. **Google Cloud CLI instalado**
   ```powershell
   # Verificar instalación
   gcloud --version
   ```
   Si no está instalado: https://cloud.google.com/sdk/docs/install

2. **Autenticado en Google Cloud**
   ```powershell
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Proyecto de Google Cloud**
   - Crear en: https://console.cloud.google.com/projectcreate
   - Habilitar billing (tarjeta de crédito)
   - Google Cloud ofrece $300 USD en créditos gratis para nuevos usuarios

4. **OpenAI API Key**
   - Obtener en: https://platform.openai.com/api-keys
   - Asegurar que tenga créditos disponibles

## Deployment Automático

### Opción 1: Script PowerShell (Recomendado)

1. **Editar variables en `deploy-cloud-run.ps1`**:
   ```powershell
   $PROJECT_ID = "tu-proyecto-id"  # Cambiar por tu project ID real
   $REGION = "us-central1"          # O la región más cercana
   ```

2. **Ejecutar script**:
   ```powershell
   cd D:\projects\AI_Oracle
   .\deploy-cloud-run.ps1
   ```

3. **Seguir prompts**:
   - Ingresar OpenAI API Key cuando se solicite
   - Esperar ~5-10 minutos para el deployment completo

### Opción 2: Deployment Manual

Si prefieres control total, sigue estos pasos:

#### 1. Configurar proyecto
```powershell
gcloud config set project TU-PROJECT-ID
gcloud config set run/region us-central1
```

#### 2. Habilitar APIs
```powershell
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

#### 3. Crear secreto para OpenAI Key
```powershell
# Opción A: Desde consola (más seguro)
echo "sk-tu-openai-key" | gcloud secrets create openai-api-key --data-file=- --replication-policy="automatic"

# Opción B: Desde archivo
echo "sk-tu-openai-key" > temp-key.txt
gcloud secrets create openai-api-key --data-file=temp-key.txt --replication-policy="automatic"
Remove-Item temp-key.txt
```

#### 4. Desplegar Abu Engine
```powershell
cd abu_engine
gcloud run deploy abu-engine `
    --source . `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 10
```

**Esperar ~3-5 minutos**. Cloud Build creará la imagen y la desplegará.

#### 5. Obtener URL de Abu
```powershell
$ABU_URL = gcloud run services describe abu-engine --region us-central1 --format "value(status.url)"
Write-Host "Abu URL: $ABU_URL"
```

#### 6. Desplegar Lilly Engine
```powershell
cd ..\lilly_engine
gcloud run deploy lilly-engine `
    --source . `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 10 `
    --set-secrets OPENAI_API_KEY=openai-api-key:latest `
    --set-env-vars "ABU_URL=$ABU_URL,DEFAULT_LANGUAGE=es,USE_ASSISTANT_API=false"
```

#### 7. Obtener URL de Lilly
```powershell
$LILLY_URL = gcloud run services describe lilly-engine --region us-central1 --format "value(status.url)"
Write-Host "Lilly URL: $LILLY_URL"
```

## Verificación

### 1. Probar Abu Engine
```powershell
# Health check
curl "$ABU_URL/health"

# Documentación interactiva
Start-Process "$ABU_URL/docs"
```

### 2. Probar Lilly Engine
```powershell
# Health check
curl "$LILLY_URL/health"

# Documentación interactiva
Start-Process "$LILLY_URL/docs"
```

### 3. Test end-to-end
```powershell
# Obtener carta natal
curl "$ABU_URL/api/astro/chart?date=1990-01-15T10:30:00Z&lat=40.7128&lon=-74.0060"

# Interpretación con Lilly
$body = @{
    events = @(
        @{
            cycle = "Saturn Return"
            planet = "Saturn"
        }
    )
    language = "es"
} | ConvertTo-Json

curl -X POST "$LILLY_URL/api/ai/interpret" `
    -H "Content-Type: application/json" `
    -d $body
```

## Monitoreo y Logs

### Ver logs en tiempo real
```powershell
# Abu logs
gcloud run services logs tail abu-engine --region us-central1

# Lilly logs
gcloud run services logs tail lilly-engine --region us-central1
```

### Consola web
- https://console.cloud.google.com/run

## Costos Estimados

### Cloud Run (Pay-per-use)
- **Free tier**: 2 millones de requests/mes
- **Después del free tier**:
  - CPU: ~$0.00002400/vCPU-segundo
  - Memoria: ~$0.00000250/GiB-segundo
  - Requests: ~$0.40/millón

### Ejemplo de costo mensual (1,000 usuarios activos):
- 10,000 requests/día = 300,000/mes
- Promedio 2s por request
- **Costo estimado: $5-15/mes** (dentro del free tier inicialmente)

### OpenAI API
- GPT-4o-mini: ~$0.150/1M input tokens, ~$0.600/1M output tokens
- Promedio 500 tokens/request
- **Costo estimado: $50-100/mes** (1,000 usuarios, 10 requests/usuario)

**Total estimado: $55-115/mes** para 1,000 usuarios activos.

## Actualizar Deployments

### Redesplegar con cambios
```powershell
# Abu
cd abu_engine
gcloud run deploy abu-engine --source .

# Lilly
cd ..\lilly_engine
gcloud run deploy lilly-engine --source .
```

### Actualizar variables de entorno
```powershell
gcloud run services update lilly-engine `
    --region us-central1 `
    --set-env-vars "USE_ASSISTANT_API=true,OPENAI_ASSISTANT_ID=asst-xyz"
```

### Actualizar secretos
```powershell
# Crear nueva versión del secreto
echo "nueva-openai-key" | gcloud secrets versions add openai-api-key --data-file=-

# Cloud Run usará la nueva versión automáticamente
```

## Rollback

Si algo sale mal, puedes revertir a una revisión anterior:

```powershell
# Listar revisiones
gcloud run revisions list --service abu-engine --region us-central1

# Rollback a revisión anterior
gcloud run services update-traffic abu-engine `
    --region us-central1 `
    --to-revisions REVISION-NAME=100
```

## Seguridad

### Restringir acceso (opcional)
```powershell
# Remover acceso público
gcloud run services remove-iam-policy-binding abu-engine `
    --region us-central1 `
    --member="allUsers" `
    --role="roles/run.invoker"

# Permitir solo desde frontend (CORS ya configurado en FastAPI)
```

### HTTPS y Dominios Personalizados
```powershell
# Mapear dominio personalizado
gcloud run domain-mappings create --service abu-engine --domain api.tudominio.com
```

## Troubleshooting

### Error: "API not enabled"
```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### Error: "Permission denied"
```powershell
# Verificar rol de cuenta de servicio
gcloud projects add-iam-policy-binding TU-PROJECT-ID `
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"
```

### Error: Build timeout
```powershell
# Aumentar timeout de build
gcloud run deploy abu-engine --source . --timeout 15m
```

### Servicio no responde
```powershell
# Ver logs detallados
gcloud run services logs read abu-engine --region us-central1 --limit 50

# Revisar health check
curl https://tu-servicio.run.app/health
```

## Próximos Pasos

Una vez desplegados los servicios:

1. ✅ **Probar endpoints** en `/docs`
2. ✅ **Crear OpenAI Assistant** con las URLs de Cloud Run
3. ✅ **Actualizar frontend** con las nuevas URLs
4. ✅ **Configurar monitoreo** (Cloud Monitoring, alertas)
5. ✅ **Dominio personalizado** (opcional)
6. ✅ **CI/CD** con GitHub Actions (opcional)

## Referencias

- Cloud Run docs: https://cloud.google.com/run/docs
- Pricing calculator: https://cloud.google.com/products/calculator
- Free tier: https://cloud.google.com/free
- OpenAI pricing: https://openai.com/pricing
