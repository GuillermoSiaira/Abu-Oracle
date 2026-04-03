# -*- coding: utf-8 -*-
"""Wrapper para ejecutar Fase A-2 con encoding correcto en Windows."""
import os, sys

# Leer API key
with open('next_app/.env.local', encoding='utf-8') as f:
    for line in f:
        if line.startswith('ANTHROPIC_API_KEY='):
            os.environ['ANTHROPIC_API_KEY'] = line.strip().split('=',1)[1].strip().strip('"').strip("'")

os.environ['FINOPS_EXECUTE_A2'] = 'yes'
os.environ['N_SUBJECTS'] = '50'
os.environ['ABU_URL'] = 'http://localhost:8000'

# Reimportar stdout con utf-8
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Ejecutar el script principal
import importlib.util
spec = importlib.util.spec_from_file_location(
    "__main__",
    "scripts/finops/measure_token_distribution_output.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
