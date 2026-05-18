"""
Diseños experimentales para KG-C03.

Cada módulo en este paquete representa un diseño completo del experimento:
sujetos, prompt de evaluación, y funciones de construcción de contextos A y B.

El runner.py los carga dinámicamente con `--design <module_name>`.

Contrato mínimo que cada diseño debe exportar:
    DESIGN_ID: str             — identificador, igual al nombre del módulo
    DESIGN_DESCRIPTION: str    — explicación corta de la pregunta científica
    EVAL_PROMPT: str           — prompt que recibe Lilly (igual en A y B)
    SUBJECTS: list[dict]       — sujetos a evaluar
    build_context_a(natal, bio) -> str   — construye condición A
    build_context_b(natal, bio) -> str   — construye condición B
"""
