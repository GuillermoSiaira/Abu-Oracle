# Lilly Engine – Troubleshooting: OpenAI Connection Error

## Problema identificado
**Síntoma**: Lilly Engine en Cloud Run siempre devuelve `"source": "fallback"` en lugar de usar el LLM de OpenAI.

**Error en logs**:
```
UserWarning: OpenAI API error: Connection error.. Falling back to archetypes.
```

## Diagnóstico realizado (2025-11-10)

### ✅ Confirmado funcionando
1. **OPENAI_API_KEY disponible**: Secret `openai-api-key` existe y tiene 164 caracteres (clave válida).
2. **Código correcto**: La lógica de detección de API key y construcción de cliente OpenAI está OK.
3. **Timeout configurado**: Se aumentó timeout a 60s total, 10s connect + 2 retries en `lilly_engine/core/llm.py`.
4. **Variables de entorno**: `USE_ASSISTANTS=false` (modo Chat Completions), `DEFAULT_LANGUAGE=es`, `ABU_URL` correctos.
5. **Permisos de secret**: Service account tiene rol `secretmanager.secretAccessor`.
6. **Variable directa probada**: Se probó pasar OPENAI_API_KEY como variable directa (sin secret) y el error persiste → **no es problema de secret mounting**.

### ❌ Causa raíz
**Conectividad de red bloqueada**: Cloud Run no puede establecer conexión HTTPS a `api.openai.com`.

Este error ocurre **antes** de que llegue cualquier respuesta de OpenAI (no es timeout de respuesta, es fallo al conectar el socket TCP/TLS).

## Posibles causas de red

### 1. VPC Connector sin egress configurado
Si el servicio está en VPC pero no tiene ruta de salida a internet.

**Verificar**:
```powershell
gcloud run services describe lilly-engine --region=us-central1 --format="value(spec.template.metadata.annotations)"
```
Si aparece `run.googleapis.com/vpc-access-connector`, revisar configuración de egress.

**Solución**: Configurar `run.googleapis.com/vpc-access-egress: all-traffic` o usar Cloud NAT.

### 2. Organization Policy bloqueando egress
Políticas a nivel de organización pueden restringir conexiones salientes.

**Verificar**:
```powershell
gcloud org-policies list --project=abu-oracle
gcloud org-policies describe constraints/compute.restrictCloudNATUsage --project=abu-oracle
```

**Solución**: Contactar admin de organización para ajustar políticas o crear excepción para el proyecto.

### 3. Firewall de VPC (si aplica)
Reglas de firewall pueden estar bloqueando puerto 443 saliente.

**Verificar**:
```powershell
gcloud compute firewall-rules list --project=abu-oracle --filter="direction=EGRESS"
```

**Solución**: Crear regla permitiendo egress HTTPS:
```powershell
gcloud compute firewall-rules create allow-openai-egress \
  --direction=EGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:443 \
  --destination-ranges=0.0.0.0/0
```

### 4. Problema temporal de infraestructura GCP
Menos probable, pero puede haber problemas regionales de conectividad.

**Verificar**: Desplegar en otra región (ej. `us-east1`) y probar.

**Solución**: Esperar resolución de Google o cambiar región.

## Pasos de resolución (checklist)

### Inmediato (mañana)
- [ ] Verificar si hay VPC connector configurado en el servicio
- [ ] Si hay VPC: confirmar que egress está configurado para `all-traffic` o que existe Cloud NAT
- [ ] Si no hay VPC: verificar organization policies que puedan bloquear egress
- [ ] Revisar firewall rules si el proyecto usa VPC custom

### Si VPC connector presente
```powershell
# Ver detalles del connector
gcloud compute networks vpc-access connectors describe CONNECTOR_NAME --region=us-central1

# Actualizar servicio para usar egress completo
gcloud run services update lilly-engine \
  --region=us-central1 \
  --vpc-egress=all-traffic
```

### Si no hay VPC connector
```powershell
# Confirmar que el servicio tiene acceso directo a internet
gcloud run services describe lilly-engine --region=us-central1 \
  --format="value(spec.template.spec.containers[0].resources)"

# Probar deploy en región diferente
gcloud run deploy lilly-engine-test \
  --image gcr.io/abu-oracle/lilly-engine:latest \
  --region us-east1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="DEFAULT_LANGUAGE=es,USE_ASSISTANTS=false,ABU_URL=https://abu-engine-bbrsyawaca-uc.a.run.app,OPENAI_API_KEY=..."
```

### Debugging avanzado
```powershell
# Agregar endpoint de health check en Lilly para probar conectividad
# Modificar main.py temporalmente:

@app.get("/debug/connectivity")
async def test_connectivity():
    import socket
    import ssl
    try:
        context = ssl.create_default_context()
        with socket.create_connection(("api.openai.com", 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname="api.openai.com") as ssock:
                return {"status": "ok", "openai_reachable": True}
    except Exception as e:
        return {"status": "error", "openai_reachable": False, "error": str(e)}

# Redeploy y probar:
curl https://lilly-engine-503488473965.us-central1.run.app/debug/connectivity
```

## Workarounds temporales (no recomendados para prod)

### Opción A: Proxy HTTP
Configurar un proxy HTTP con acceso a internet y usarlo en el cliente OpenAI:
```python
_client = OpenAI(
    api_key=_OPENAI_API_KEY,
    http_client=httpx.Client(proxy="http://your-proxy:8080")
)
```

### Opción B: Cloud Functions
Si Cloud Functions tiene mejor conectividad en tu proyecto, mover la llamada LLM a una función:
```python
# En Lilly: hacer request a Cloud Function
response = requests.post("https://region-project.cloudfunctions.net/openai-proxy", json=payload)
```

## Estado actual del deployment

**Revisión activa**: `lilly-engine-00001-4bp`
- API key configurada como variable directa (menos seguro, solo para debugging)
- Timeout configurado: 60s total, 10s connect, 2 retries
- Error persiste: `Connection error`

**URLs activas**:
- Lilly: `https://lilly-engine-503488473965.us-central1.run.app`
- Abu: `https://abu-engine-bbrsyawaca-uc.a.run.app`

## Impacto en el sistema

### ✅ Sin impacto
- Orquestador funciona completamente (6 tool calls ejecutados correctamente en tests)
- Abu Engine devuelve todos los datos astrológicos correctamente
- Lilly responde con fallback válido (archetype-based)

### ⚠️ Con impacto
- Interpretaciones son genéricas (basadas en arquetipos simples)
- No hay narrativa personalizada generada por LLM
- Experiencia de usuario limitada en calidad de interpretación

## Próximos pasos sugeridos

1. **Mañana**: Revisar configuración de red del proyecto (VPC/firewall/policies).
2. **Si VPC**: Configurar egress o Cloud NAT.
3. **Si no VPC**: Verificar organization policies o contactar soporte GCP.
4. **Validación**: Probar endpoint `/debug/connectivity` después de cambios.
5. **Rollback de seguridad**: Volver a usar secret en lugar de variable directa una vez resuelto.

## Referencias

- [Cloud Run VPC egress](https://cloud.google.com/run/docs/configuring/vpc-direct-vpc#egress-settings)
- [Cloud NAT setup](https://cloud.google.com/nat/docs/using-nat)
- [Organization policies](https://cloud.google.com/resource-manager/docs/organization-policy/overview)
- [Firewall rules](https://cloud.google.com/vpc/docs/firewalls)

---
**Última actualización**: 2025-11-10  
**Estado**: En investigación – código correcto, problema de infraestructura de red
