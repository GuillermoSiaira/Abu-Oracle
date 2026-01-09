import jax.numpy as jnp
from jax import jit, vmap
from .planets import PLANET_DATA, obtener_posicion_heliocentrica

# ==============================================================================
# 1. DEFINICIÓN DE ASPECTOS (La "Opinión" del Sistema)
# ==============================================================================
# Definimos los armónicos principales que Abu debe buscar.
# Ángulo (grados), Orbe (tolerancia), Nombre
ASPECTOS_DEFINICION = {
    'Conjuncion': {'angulo': 0.0,   'orbe': 8.0, 'peso': 1.0},
    'Oposicion':  {'angulo': 180.0, 'orbe': 8.0, 'peso': -1.0},
    'Trigono':    {'angulo': 120.0, 'orbe': 6.0, 'peso': 0.8},
    'Cuadratura': {'angulo': 90.0,  'orbe': 6.0, 'peso': -0.8},
    'Sextil':     {'angulo': 60.0,  'orbe': 4.0, 'peso': 0.5},
}

# ==============================================================================
# 2. MOTOR DE ESTADO (Captura una "Foto" del cielo)
# ==============================================================================

def obtener_estado_sistema(t_dias, planetas_keys):
    """
    Devuelve un vector con las longitudes eclípticas (0-360) de todos los planetas.
    t_dias: Puede ser un escalar (un momento) o un vector (muchos días).
    """
    # Función interna auxiliar para obtener el ángulo de un solo planeta
    def get_angulo_planeta(nombre):
        data = PLANET_DATA[nombre]
        # Usamos la función que ya creaste en planets.py
        # Nota: Asumimos origen Sol (Heliocéntrico) para aspectos planetarios puros por ahora.
        # Para Geocéntrico, habría que restar la Tierra primero.
        pos = obtener_posicion_heliocentrica(t_dias, data['a'], data['e'], data['p'], data['L0'])
        return jnp.degrees(jnp.arctan2(pos[1], pos[0])) % 360.0

    # Creamos una lista de arrays (uno por planeta) y los apilamos
    # Resultado: Una matriz de [num_planetas]
    angulos = [get_angulo_planeta(p) for p in planetas_keys]
    return jnp.stack(angulos)

# ==============================================================================
# 3. MOTOR DE RELACIONES (JAX Matrix Operations)
# ==============================================================================

@jit
def diferencia_angular_minima(a1, a2):
    """Calcula la distancia más corta en un círculo (ej: 350 vs 10 es 20 grados, no 340)"""
    diff = jnp.abs(a1 - a2)
    return jnp.minimum(diff, 360.0 - diff)

@jit
def calcular_matriz_interaccion(angulos_A, angulos_B):
    """
    CRUCIAL: Compara dos sets de ángulos.
    - Si angulos_A == angulos_B -> Carta Natal (Aspectos internos)
    - Si angulos_A != angulos_B -> Tránsitos (A vs B)
    
    Output: Matriz [N_planetas_A x N_planetas_B] con las diferencias angulares.
    """
    # Broadcasting de JAX:
    # A[:, None] lo vuelve columna, B[None, :] lo vuelve fila.
    # La resta genera la matriz de todas las combinaciones.
    matriz_diff = diferencia_angular_minima(angulos_A[:, None], angulos_B[None, :])
    return matriz_diff

# ==============================================================================
# 4. DETECTOR DE EVENTOS
# ==============================================================================

def detectar_aspectos(matriz_distancias):
    """
    Analiza la matriz de distancias y busca coincidencias con ASPECTOS_DEFINICION.
    Devuelve una máscara 'caliente' donde hay aspectos.
    """
    # Por simplicidad en esta fase, buscamos solo Cuadraturas exactas (+- orbe)
    # En el futuro, esto iterará sobre todos los aspectos.
    
    target = 90.0 # Buscamos Cuadraturas
    orbe = 6.0
    
    # Lógica booleana tensorial
    es_cuadratura = jnp.abs(matriz_distancias - target) < orbe
    return es_cuadratura