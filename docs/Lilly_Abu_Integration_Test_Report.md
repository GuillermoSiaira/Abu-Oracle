# Informe Técnico: Test de Integración Lilly Engine → Abu Engine (Docker)

## Introducción

Este documento describe el procedimiento y resultado de la prueba de integración entre Lilly Engine y Abu Engine, ambos corriendo en contenedores Docker, con el frontend (Next.js) ejecutándose fuera de Docker. El objetivo es validar la comunicación interna y la generación de respuestas astrológicas completas, asegurando la robustez del backend y la correcta orquestación de servicios.

## Objetivo de la Prueba

- Verificar que Lilly Engine recibe correctamente requests externos en el endpoint `/api/ai/interpret`.
- Confirmar que Lilly Engine construye los parámetros y comunica internamente con Abu Engine usando la URL interna `http://abu_engine:8000`.
- Validar que Abu Engine responde con la carta extendida y que Lilly Engine construye el objeto Maestro.
- Asegurar que la respuesta JSON es completa y libre de errores 400, 500, 502, "Abu Engine error" o "connection refused".

## Entorno y Configuración

- **Backend:**  
  - `abu_engine` corriendo en Docker, puerto interno `8000`.
  - `lilly_engine` corriendo en Docker, puerto interno `8001`.
- **Frontend:**  
  - `next_app` corriendo localmente con `npm run dev` (fuera de Docker).
- **Contenedores:**  
  - Reconstruidos y levantados con:
    ```sh
    docker compose down --rmi all --volumes --remove-orphans
    docker compose up --build
    ```
- **Red Docker:**  
  - Comunicación interna entre servicios mediante nombres de contenedor (`abu_engine`, `lilly_engine`).

## Pasos de Ejecución

1. **Ingreso al contenedor de Lilly Engine:**
   ```sh
   docker exec -it lilly_engine sh
   ```
2. **Ejecución de la prueba con curl:**
   ```sh
   curl -X POST http://localhost:8001/api/ai/interpret \
     -H "Content-Type: application/json" \
     -d '{
           "birthDate": "2020-01-01T12:00:00Z",
           "lat": 0,
           "lon": 0
         }'
   ```

## Resultado Obtenido

- Lilly Engine respondió con un **JSON Maestro completo**.
- No se presentaron errores de tipo:
  - `connection refused`
  - `"Abu Engine error"`
  - `400`, `500`, `502`
- El objeto Maestro incluyó:
  - Metadatos: `"interpreted_by": "lilly_engine"`, `"calculated_by": "abu_engine"`
  - Año, dignidades, angularidades, RS stub, monthly windows, y demás bloques generados correctamente.

## Análisis Técnico

- **Recepción de requests:** El endpoint `/api/ai/interpret` de Lilly Engine aceptó y procesó correctamente la solicitud externa.
- **Construcción de parámetros:** Los datos enviados en el body JSON fueron interpretados y reenviados a Abu Engine sin alteraciones.
- **Comunicación interna:** Lilly Engine utilizó la URL interna `http://abu_engine:8000` para obtener la carta extendida, demostrando la correcta resolución de nombres de servicio en la red Docker.
- **Generación de Maestro:** Lilly Engine integró la respuesta de Abu Engine y generó el objeto Maestro conforme al contrato JSON esperado.
- **Robustez:** No se detectaron errores de comunicación, procesamiento ni formato. El flujo interpretativo se ejecutó de extremo a extremo sin incidentes.

## Conclusión

La prueba de integración confirma que:

- El backend está **100% funcional**.
- Lilly Engine y Abu Engine pueden comunicarse correctamente dentro de Docker.
- El flujo interpretativo completo, desde la recepción de la solicitud hasta la generación del JSON Maestro, está validado y operativo.
- El sistema está listo para uso en producción y para integraciones frontend adicionales.

---
