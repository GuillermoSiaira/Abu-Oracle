import os
import json
from typing import Dict, Optional, Any
from openai import OpenAI
from core.memory_store import MemoryStore

# Configuración robusta por variables de entorno
OPENAI_MODEL = os.getenv("OPENAI_MODEL_ID", "gpt-4o") # Default seguro, pero overrideable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    # Fail fast: Si no hay key, el sistema no debe arrancar silenciosamente
    print("WARNING: OPENAI_API_KEY not found in environment.")

client = OpenAI(api_key=OPENAI_API_KEY)

# System Prompt enfocado en "Ground Truth" (Verdad basada en datos)
SYSTEM_PROMPT_TEMPLATE = """
ERES: Lilly, un Agente de Inteligencia Astrológica del protocolo Abu Oracle.
OBJETIVO: Interpretar determinísticamente los datos calculados por el motor Abu Engine.

FUENTE DE VERDAD (ABU JSON):
{astro_context}

REGLAS DE OPERACIÓN (STRICT MODE):
1. GROUNDING: Tu interpretación debe basarse EXCLUSIVAMENTE en el JSON proporcionado. Si el JSON dice "Sol en Casa 12", es Casa 12. No alucines posiciones.
2. INCERTIDUMBRE: Si el JSON (context) está vacío o es null, informa al usuario que necesitas calcular su carta primero.
3. ESTILO: Profesional, empático, preciso. No uses jerga mística vacía ("energías fluyendo") sin respaldo técnico en el JSON.
4. FORMATO: Usa Markdown para resaltar planetas o aspectos clave.

IDIOMA: Español neutro.
"""

class LillyAgent:
    def __init__(self, session_id: str):
        self.memory = MemoryStore(session_id)
        self.session_id = session_id

    def process_message(self, user_message: str, context: Optional[Dict[str, Any]]) -> str:
        # 1. Persistir input usuario
        self.memory.save_message("user", user_message)

        # 2. Preparar Prompt Contextual
        # Serialización segura del contexto de Abu
        context_str = json.dumps(context, ensure_ascii=False) if context else "NO DATA AVAILABLE via Abu Engine."
        
        system_instruction = SYSTEM_PROMPT_TEMPLATE.replace("{astro_context}", context_str)
        
        # Recuperar historial reciente (Short-term memory)
        recent_history = self.memory.get_context_window(limit=10)
        
        messages_payload = [{"role": "system", "content": system_instruction}] + recent_history

        try:
            # 3. Inferencia (LLM)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages_payload,
                temperature=0.7, # Creatividad controlada
                max_tokens=800
            )
            
            ai_content = response.choices[0].message.content
            
            # 4. Persistir output agente
            self.memory.save_message("assistant", ai_content)
            
            return ai_content

        except Exception as e:
            # Manejo de errores "Enterprise": Loguear el error real, devolver mensaje de servicio
            print(f"[ERROR] Session {self.session_id} - OpenAI Fail: {str(e)}")
            return "Error de servicio en el módulo cognitivo. Por favor intente nuevamente."