import json
import os
import random
import re
import time


JUDGE_PRICING = {"input_per_m": 3.00, "output_per_m": 15.00}  # Sonnet 4.6


def _judge_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * JUDGE_PRICING["input_per_m"]
        + output_tokens * JUDGE_PRICING["output_per_m"]
    ) / 1_000_000


JUDGE_PROMPT_TEMPLATE = """
Eres un evaluador experto en astrologia helenistica clasica.
Evalua estas dos interpretaciones de carta natal en una escala del 1 al 5 para cada criterio.
NO sabes cual interpretacion fue generada con que metodo; evalua solo el contenido.

INTERPRETACION X:
{resp_x}

INTERPRETACION Y:
{resp_y}

Criterios (1=malo, 5=excelente):
1. coherencia_doctrinal: usa correctamente senorios y firdaria segun la doctrina clasica.
2. especificidad: menciona planetas, casas y fechas concretas.
3. multi_hop_reasoning: conecta senor del ano -> posicion natal -> dignidad -> implicancia.
4. ausencia_de_generico: evita frases vacias y lugares comunes.
5. sintesis: produce una lectura integrada, no una lista desconectada.

Responde SOLO con JSON, sin texto extra:
{{
  "x": {{"coherencia_doctrinal":N,"especificidad":N,"multi_hop_reasoning":N,"ausencia_de_generico":N,"sintesis":N,"total":N}},
  "y": {{"coherencia_doctrinal":N,"especificidad":N,"multi_hop_reasoning":N,"ausencia_de_generico":N,"sintesis":N,"total":N}}
}}
"""


def _text_from_response(response: object) -> str:
    content = getattr(response, "content", None) or []
    chunks: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            chunks.append(text)
    return "".join(chunks)


def _normalize_scores(scores: dict) -> dict:
    total = scores.get("total")
    if not isinstance(total, (int, float)):
        total = sum(
            value
            for key, value in scores.items()
            if key != "total" and isinstance(value, (int, float))
        )
        scores["total"] = total
    return scores


def evaluate_pair(ctx_a: str, ctx_b: str, resp_a: str, resp_b: str) -> dict:
    """
    Send an A/B pair to the judge LLM and return scores remapped to A/B.

    The ctx_* parameters are accepted for provenance and future judge prompts;
    the current blind judge intentionally evaluates only responses.
    """
    del ctx_a, ctx_b

    import anthropic

    x_is_a = random.random() < 0.5
    resp_x, resp_y = (resp_a, resp_b) if x_is_a else (resp_b, resp_a)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")

    client = anthropic.Anthropic(api_key=api_key)
    model = "claude-sonnet-4-6"
    t0 = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=512,
        system="Eres un evaluador experto en astrologia helenistica clasica. Responde siempre con JSON valido.",
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT_TEMPLATE.format(resp_x=resp_x, resp_y=resp_y),
            }
        ],
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)

    usage_obj = getattr(response, "usage", None)
    input_tokens = int(getattr(usage_obj, "input_tokens", 0) or 0) if usage_obj else 0
    output_tokens = int(getattr(usage_obj, "output_tokens", 0) or 0) if usage_obj else 0
    judge_usage = {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(_judge_cost(input_tokens, output_tokens), 6),
        "latency_ms": latency_ms,
    }

    raw = _text_from_response(response) or "{}"

    # Strip markdown code fences if Sonnet wrapped the JSON (it sometimes does).
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    # Fallback: extract the first {...} block if there's still extra text around.
    if not cleaned.startswith("{"):
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

    try:
        scores = json.loads(cleaned)
        x_scores = _normalize_scores(scores.get("x", {}))
        y_scores = _normalize_scores(scores.get("y", {}))
        scores_a = x_scores if x_is_a else y_scores
        scores_b = y_scores if x_is_a else x_scores
        return {
            "scores_a": scores_a,
            "scores_b": scores_b,
            "total_a": scores_a.get("total", 0),
            "total_b": scores_b.get("total", 0),
            "judge_order": "x=A,y=B" if x_is_a else "x=B,y=A",
            "judge_usage": judge_usage,
        }
    except json.JSONDecodeError:
        return {
            "raw_judge_output": raw,
            "total_a": 0,
            "total_b": 0,
            "judge_usage": judge_usage,
        }
