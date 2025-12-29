"""Run a user query through the Abu Orchestrator Assistant and execute tool calls.

Flujo:
1. Crea una Run con el mensaje del usuario.
2. Itera mientras el estado sea requires_action -> ejecuta cada tool_call:
   - Llama al endpoint real (Abu o Lilly) vía requests.
   - Envía output como tool_outputs.
3. Cuando la Run finaliza, imprime el contenido final.

IMPORTANTE: Para 'interpret_astrological_data' se supone que llamamos al
endpoint Lilly /api/ai/interpret, NO dejamos que el modelo genere interpretación
sin datos. El Assistant debe haber recolectado datos antes.
"""
from __future__ import annotations

import os
import time
import json
from pathlib import Path
from typing import Any, Dict
import requests
from openai import OpenAI

def load_env_from_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env_from_dotenv()

ABU_BASE = os.getenv("ABU_URL", "https://abu-engine-bbrsyawaca-uc.a.run.app")
LILLY_BASE = os.getenv("LILLY_URL", "https://lilly-engine-503488473965.us-central1.run.app")


def call_endpoint(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch tool call to real HTTP endpoint and return JSON."""
    if name == "get_chart":
        r = requests.get(f"{ABU_BASE}/api/astro/chart", params=args, timeout=60)
        r.raise_for_status()
        return r.json()
    if name == "get_forecast":
        r = requests.get(f"{ABU_BASE}/api/astro/forecast", params=args, timeout=120)
        r.raise_for_status()
        return r.json()
    if name == "get_life_cycles":
        r = requests.get(f"{ABU_BASE}/api/astro/life-cycles", params=args, timeout=60)
        r.raise_for_status()
        return r.json()
    if name == "get_solar_return":
        r = requests.get(f"{ABU_BASE}/api/astro/solar-return", params=args, timeout=60)
        r.raise_for_status()
        return r.json()
    if name == "optimize_sr_locations":
        payload = {
            "birth_profile": {
                "birthDate": args["birthDate"],
                "lat": args["lat"],
                "lon": args["lon"],
            },
            "target_year": args["target_year"],
        }
        r = requests.post(f"{ABU_BASE}/api/rs/optimize", json=payload, timeout=180)
        r.raise_for_status()
        return r.json()
    if name == "interpret_astrological_data":
        # Directly call Lilly interpret endpoint
        r = requests.post(f"{LILLY_BASE}/api/ai/interpret", json=args, timeout=120)
        r.raise_for_status()
        return r.json()
    return {"error": f"Unknown function {name}"}


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    if not api_key or not assistant_id:
        raise SystemExit("Faltan OPENAI_API_KEY u OPENAI_ASSISTANT_ID en entorno.")

    client = OpenAI(api_key=api_key)

    user_question = os.getenv("USER_QUESTION", "¿Cuál es mi enfoque evolutivo este año?")

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_question,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "requires_action":
            tool_outputs = []
            for tc in run.required_action.submit_tool_outputs.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                print(f"[tool] Ejecutando {name} con args={args}")
                try:
                    result = call_endpoint(name, args)
                except Exception as e:  # noqa: BLE001
                    result = {"error": str(e)}
                tool_outputs.append({"tool_call_id": tc.id, "output": json.dumps(result, ensure_ascii=False)})
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs,
            )
        elif run.status in {"completed", "failed", "cancelled", "expired"}:
            break
        else:
            time.sleep(2)

    if run.status != "completed":
        print("Run terminó con estado:", run.status)
        return

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    # Último mensaje del assistant
    printed = False
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            for content in msg.content:
                # Compatibilidad segun SDK: 'text' o 'output_text'
                if getattr(content, "type", None) in {"text", "output_text"}:
                    txt = getattr(getattr(content, "text", None), "value", None)
                    if not txt and hasattr(content, "text"):
                        # En algunas versiones, content.text es str
                        txt = content.text if isinstance(content.text, str) else None
                    if txt:
                        print("\n[RESULTADO]\n" + txt)
                        printed = True
            if not printed:
                # Volcado crudo (debug)
                try:
                    from json import dumps
                    print("\n[RESULTADO RAW]\n" + dumps(msg.model_dump(), ensure_ascii=False, indent=2))
                except Exception:
                    print("\n[RESULTADO]\n<No printable text content>")
            break


if __name__ == "__main__":
    main()
