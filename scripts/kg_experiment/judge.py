import json
import os
import random


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
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="Eres un evaluador experto en astrologia helenistica clasica. Responde siempre con JSON valido.",
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT_TEMPLATE.format(resp_x=resp_x, resp_y=resp_y),
            }
        ],
    )

    raw = _text_from_response(response) or "{}"

    try:
        scores = json.loads(raw)
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
        }
    except json.JSONDecodeError:
        return {"raw_judge_output": raw, "total_a": 0, "total_b": 0}
