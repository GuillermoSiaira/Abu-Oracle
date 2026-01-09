import jax.numpy as jnp
import jax
from .planets import PLANET_DATA
from .aspects import obtener_estado_sistema, calcular_matriz_interaccion, detectar_aspectos

# Configurar CPU
jax.config.update("jax_platform_name", "cpu")

def main():
    print("--- INICIANDO MOTOR DE SINADSTRÍA TEMPORAL (JAX) ---")
    
    planetas = ['Mercurio', 'Venus', 'Marte', 'Jupiter', 'Saturno']
    
    # 1. DEFINIMOS AL NATIVO (Tu Nacimiento)
    # Supongamos Día Juliano relativo J2000. 
    # Ejemplo: Alguien nacido 20 años antes del 2000 (-7300 días)
    dia_natal = -7300.0 
    estado_natal = obtener_estado_sistema(dia_natal, planetas)
    
    print(f"\n1. Estado Natal (Día {dia_natal}):")
    for p, ang in zip(planetas, estado_natal):
        print(f"   {p}: {ang:.2f}°")

    # 2. DEFINIMOS EL AHORA (Tránsito)
    # Día J2000 actual (aprox 9000 días desde el 2000)
    dia_actual = 9125.0 
    estado_actual = obtener_estado_sistema(dia_actual, planetas)
    
    print(f"\n2. Estado Actual (Día {dia_actual}):")
    for p, ang in zip(planetas, estado_actual):
        print(f"   {p}: {ang:.2f}°")

    # 3. EL CRUCE (Tu requerimiento #2)
    # Calculamos la matriz: Filas = Natal, Columnas = Actual
    matriz_transitos = calcular_matriz_interaccion(estado_natal, estado_actual)
    
    print("\n3. Matriz de Tránsitos (Ángulos entre Natal vs Actual):")
    # Imprimimos la matriz formateada
    print("NATAL \\ ACTUAL | " + " | ".join([p[:4] for p in planetas]))
    print("-" * 60)
    for i, p_nat in enumerate(planetas):
        fila_str = " | ".join([f"{val:5.1f}°" for val in matriz_transitos[i]])
        print(f"{p_nat:14} | {fila_str}")

    # 4. BÚSQUEDA DE CUADRATURAS (Tensión)
    # ¿Hay algún planeta hoy haciendo 90° a un planeta natal?
    hay_tension = detectar_aspectos(matriz_transitos)
    
    if jnp.any(hay_tension):
        indices = jnp.argwhere(hay_tension)
        print("\n[ALERTA] ¡Aspectos Tensos (Cuadraturas) Detectados!")
        for idx in indices:
            p_natal = planetas[idx[0]]
            p_transito = planetas[idx[1]]
            distancia_real = matriz_transitos[idx[0], idx[1]]
            print(f" -> {p_transito} (Tránsito) está en CUADRATURA a {p_natal} (Natal). Ángulo exacto: {distancia_real:.2f}°")
    else:
        print("\nNo se detectaron cuadraturas importantes hoy.")

if __name__ == "__main__":
    main()