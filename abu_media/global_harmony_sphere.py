from manim import *
import math

class GlobalHarmonySphere(ThreeDScene):
    def construct(self):
        # Configuración estética "Abu Dark" consistente con tus otros scripts
        self.camera.background_color = "#050505"
        
        # --- 1. TÍTULOS Y CONTEXTO ---
        title = Text("The Topology of Fate", font_size=40, color=WHITE).to_corner(UL)
        subtitle = Text("Visualizing the Astro-Geodetic Harmony Field (Scalar H)", font_size=24, color=GRAY).next_to(title, DOWN, aligned_edge=LEFT)
        self.add_fixed_in_frame_mobjects(title, subtitle)

        # Configurar Cámara 3D
        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)

        # --- 2. LA FUNCIÓN DE ARMONÍA (SIMULADA) ---
        # Esta función simula la interferencia de ondas planetarias sobre la esfera.
        # En producción, esto llamaría a tu 'Abu Engine'.
        # Input: u (latitud), v (longitud) -> Output: Scalar (Tensión/Energía)
        def harmony_potential(u, v):
            # Simulación de interferencia compleja:
            # - Onda base ecuatorial (clima/latitud)
            # - 3 "Focos de Tensión" (e.g. Marte/Saturno angulares)
            # - 2 "Pozos de Armonía" (e.g. Júpiter/Venus angulares)
            
            val = 0
            # Onda estacional base
            val += 0.3 * np.sin(3 * u) 
            # Foco de tensión (Pico)
            val += 0.5 * np.exp(-10 * ((u - 0.5)**2 + (v - 1.0)**2)) 
            # Foco de armonía (Valle)
            val -= 0.6 * np.exp(-10 * ((u + 0.3)**2 + (v + 2.0)**2))
            # Ruido armónico (Aspectos menores)
            val += 0.1 * np.sin(10 * v) * np.cos(10 * u)
            return val

        # --- 3. LA ESFERA TOPOLÓGICA (RELIEVE = TENSIÓN) ---
        # R = Radio Base + harmony_potential
        # Si la tensión es alta, el terreno se eleva (mayor energía potencial).
        # Si hay armonía, se hunde (pozo de potencial = estabilidad).
        
        resolution_uv = (64, 128) # Alta resolución para que se vea el "heatmap"
        radius_base = 2.5

        def param_surface(u, v):
            # u range: -PI/2 to PI/2 (Lat)
            # v range: 0 to TAU (Lon)
            
            # Calculamos el desplazamiento radial basado en la "Fricción"
            h = harmony_potential(u, v)
            r = radius_base + (h * 0.4) # Exageramos el relieve para visualizar
            
            x = r * np.cos(u) * np.cos(v)
            y = r * np.cos(u) * np.sin(v)
            z = r * np.sin(u)
            return np.array([x, y, z])

        # Creamos la superficie
        planet = Surface(
            param_surface,
            u_range=[-PI/2, PI/2],
            v_range=[0, TAU],
            resolution=resolution_uv,
            should_make_jagged=False
        )

        # NUEVO ESTILO: Mapa de calor metálico (Científico)
        # En lugar de ajedrez, usamos un color base dorado/metálico y jugamos con el brillo
        # para que los relieves resalten con la luz al girar.
        planet.set_style(
            fill_opacity=1, 
            stroke_width=0.1, 
            stroke_color=BLACK,
            fill_color=GOLD_E # Un dorado oscuro base
        )
        planet.set_sheen_factor(0.6) # Esto le da el aspecto "metálico/satélite"
        planet.set_sheen_direction(np.array([1, 1, 1])) # Dirección del brillo
        # Malla de latitud/longitud (Wireframe) para referencia geodésica
        grid = Surface(
            lambda u, v: radius_base * 1.01 * np.array([ # Ligeramente más grande
                np.cos(u) * np.cos(v),
                np.cos(u) * np.sin(v),
                np.sin(u)
            ]),
            u_range=[-PI/2, PI/2],
            v_range=[0, TAU],
            resolution=(24, 48),
            fill_opacity=0,
            stroke_color=WHITE,
            stroke_width=0.5,
            stroke_opacity=0.3
        )

        # --- 5. ANIMACIÓN: ESCANEO DEL "GROUND STATE" ---
        
        self.play(Create(grid), FadeIn(planet))
        self.wait(1)

        # Texto Explicativo Dinámico
        label_t = Text("Searching for Ground State (Min H)...", font_size=24, color=GOLD).to_corner(DR)
        self.add_fixed_in_frame_mobjects(label_t)

        # Rotación para mostrar la topología completa
        self.begin_ambient_camera_rotation(rate=0.2)
        
        # Simular un "Scanner" que encuentra el punto óptimo
        # (Supongamos que sabemos dónde está el valle en nuestra función simulada)
        optimal_coords = np.array([ # Coordenadas aproximadas del valle simulado
            (radius_base - 0.2) * np.cos(-0.3) * np.cos(-2.0 + PI*2), # Ajuste manual
            (radius_base - 0.2) * np.cos(-0.3) * np.sin(-2.0 + PI*2),
            (radius_base - 0.2) * np.sin(-0.3)
        ])
        
        marker = Dot3D(point=optimal_coords, color=TEAL, radius=0.1)
        marker_ring = Circle(radius=0.3, color=TEAL).rotate(PI/2, axis=RIGHT).move_to(optimal_coords)
        
        self.play(FadeIn(marker), Create(marker_ring))
        
        found_text = Text("Global Optimization Found", font_size=24, color=TEAL).to_corner(DR)
        self.play(ReplacementTransform(label_t, found_text))

        self.wait(4)