# Guardar en: abu_engine/services/quantum_solver.py

import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Sampler
from typing import List, Dict

def gaussian_influence(angle_planet: float, angle_house: float, sigma: float = 5.0) -> float:
    diff = abs(angle_planet - angle_house)
    diff = min(diff, 360 - diff)
    return np.exp(-(diff**2) / (2 * sigma**2))

def solve_quantum_location(
    candidates: List[Dict], 
    planetary_positions: Dict[str, float], 
    user_weights: Dict[str, float]
) -> Dict:
    """
    Recibe el TOP N candidatos pre-filtrados y decide el óptimo usando QAOA.
    """
    
    # 1. Definir Problema
    problem = QuadraticProgram()
    linear_costs = {}
    
    # Crear variables binarias y calcular costos lineales
    for city in candidates:
        city_id = city['city_id']  # Asegúrate de tener un ID único
        problem.binary_var(name=city_id)
        
        # Calcular Costo (Hamiltoniano Local)
        total_tension = 0
        angles = city['angles'] # Espera {'ASC': deg, 'MC': deg}
        
        for angle_deg in angles.values():
            for planet, planet_deg in planetary_positions.items():
                intensity = gaussian_influence(planet_deg, angle_deg)
                if intensity > 0.01:
                    w = user_weights.get(planet, 0)
                    # Invertimos signo: QUBO minimiza, Astrología busca maximizar beneficio
                    # Peso Positivo (Júpiter) -> Reduce costo (bueno)
                    # Peso Negativo (Saturno) -> Aumenta costo (malo)
                    total_tension -= (w * intensity)
        
        linear_costs[city_id] = total_tension

    # 2. Función Objetivo
    problem.minimize(linear=linear_costs)
    
    # 3. Restricción: Elegir EXACTAMENTE UNA ciudad
    # sum(x_i) == 1
    problem.linear_constraint(
        linear={city['city_id']: 1 for city in candidates}, 
        sense='==', 
        rhs=1, 
        name='select_one'
    )

    # 4. Ejecutar Solver (Simulador local para empezar)
    # COBYLA es bueno para pocas iteraciones y ruido bajo
    optimizer = COBYLA(maxiter=100)
    algorithm = MinimumEigenOptimizer(QAOA(sampler=Sampler(), optimizer=optimizer))
    
    result = algorithm.solve(problem)
    
    # 5. Decodificar Resultado
    selection = result.x
    best_idx = np.argmax(selection)
    
    return {
        "best_city": candidates[best_idx],
        "quantum_energy": result.fval, # Nivel de "tensión" final
        "status": result.status.name
    }