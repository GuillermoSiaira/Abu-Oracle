from manim import *
import math

class PositionTriangle3D(ThreeDScene):
    def construct(self):
        self.camera.background_color = "#050505"
        
        # Títulos
        title = Text("The Position Triangle (P-Z-E)", font_size=32).to_corner(UL)
        ref = Text("Source: Mascheroni, Fig. 1 (Geodesia)", font_size=20, color=GRAY).next_to(title, DOWN, aligned_edge=LEFT)
        self.add_fixed_in_frame_mobjects(title, ref)

        # Configurar Cámara 3D
        self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)

        # --- 1. LA ESFERA CELESTE ---
        r = 2.5
        sphere = Surface(
            lambda u, v: np.array([
                r * np.cos(u) * np.cos(v),
                r * np.cos(u) * np.sin(v),
                r * np.sin(u)
            ]), v_range=[0, TAU], u_range=[-PI/2, PI/2],
            checkerboard_colors=[BLACK, BLACK], resolution=(16, 32), 
            fill_opacity=0, stroke_color=BLUE_E, stroke_width=0.5, stroke_opacity=0.3
        )
        
        # Ecuador y Meridianos básicos
        equator = Circle(radius=r, color=BLUE_E, stroke_width=1)
        axis_line = Line(OUT*r*1.2, IN*r*1.2, color=GRAY, stroke_opacity=0.5) # Eje del mundo

        self.play(Create(sphere), Create(equator), Create(axis_line))

        # --- 2. LOS PUNTOS DEL TRIÁNGULO ---
        
        # A. EL POLO (P) - Fijo
        # En Manim 3D, Z es "arriba" (OUT), pero visualmente el polo suele estar inclinado.
        # Simplifiquemos: Polo Norte en el eje Z positivo visual.
        point_P = Dot3D(point=OUT*r, color=WHITE, radius=0.08)
        label_P = Text("P", font_size=24).move_to(OUT*r*1.1 + RIGHT*0.2)
        
        # B. EL ASTRO (E) - Fijo por ahora (un momento congelado)
        # Digamos que está en una Declinación y Ascensión Recta fijas
        # Coordenadas esféricas arbitrarias
        theta_star = 45 * DEGREES # Latitud celeste (Declinación)
        phi_star = -30 * DEGREES  # Longitud celeste
        
        pos_E = np.array([
            r * np.cos(theta_star) * np.cos(phi_star),
            r * np.cos(theta_star) * np.sin(phi_star),
            r * np.sin(theta_star)
        ])
        point_E = Dot3D(point=pos_E, color=GOLD, radius=0.08)
        label_E = Text("E (Star)", font_size=24, color=GOLD).move_to(pos_E * 1.2)

        self.add_fixed_in_frame_mobjects(label_P, label_E) # Texto 2D flotante
        self.play(FadeIn(point_P), FadeIn(point_E))

        # C. EL CENIT (Z) - EL OPERADOR (Móvil)
        # Usamos un ValueTracker para mover la latitud del observador
        lat_tracker = ValueTracker(20) # Empezamos en latitud 20°
        lon_tracker = ValueTracker(60) # Longitud arbitraria

        def get_Z_pos():
            lat = lat_tracker.get_value() * DEGREES
            lon = lon_tracker.get_value() * DEGREES
            return np.array([
                r * np.cos(lat) * np.cos(lon),
                r * np.cos(lat) * np.sin(lon),
                r * np.sin(lat)
            ])

        point_Z = always_redraw(lambda: Dot3D(point=get_Z_pos(), color=RED, radius=0.08))
        label_Z = Text("Z (You)", font_size=24, color=RED)
        # Actualizador complejo para etiquetas 2D en escena 3D (truco manual)
        # Para simplificar, no etiquetamos Z dinámicamente con texto 2D o se romperá la ilusión
        # Usamos un punto rojo brillante.

        self.add(point_Z)

        # --- 3. LAS LÍNEAS DEL TRIÁNGULO (ARCOS GEODÉSICOS) ---
        
        # Función auxiliar para dibujar arcos de círculo máximo sobre la esfera
        def get_arc(p1, p2, color=WHITE):
            # En una esfera, la línea más corta es un arco de círculo máximo.
            # Manim no tiene "GreatCircleArc" nativo fácil entre dos vectores.
            # Usaremos una línea recta proyectada o un Arc3D simplificado.
            # Truco visual: Una curva Bezier 3D que pasa por la superficie.
            midpoint = (p1 + p2) / 2
            midpoint = midpoint / np.linalg.norm(midpoint) * r * 1.02 # Proyectar a superficie + un pelín
            return CubicBezier(p1, midpoint, midpoint, p2, color=color, stroke_width=3)

        # Arco P-Z (Co-latitud)
        arc_PZ = always_redraw(lambda: get_arc(point_P.get_center(), point_Z.get_center(), color=RED_B))
        
        # Arco P-E (Distancia Polar - Fija)
        arc_PE = get_arc(point_P.get_center(), point_E.get_center(), color=GOLD_B) # Este no cambia
        
        # Arco Z-E (Distancia Cenital - ESTO ES LO QUE CAMBIA CON IGP)
        arc_ZE = always_redraw(lambda: get_arc(point_Z.get_center(), point_E.get_center(), color=GREEN))

        self.play(Create(arc_PE))
        self.play(Create(arc_PZ), Create(arc_ZE))

        # --- 4. LA ANIMACIÓN (IGP EN ACCIÓN) ---
        
        # Texto explicativo
        info_text = Text("Moving Zenith (Z) changes Distance (Z-E)", font_size=24, color=WHITE).to_edge(DOWN)
        self.add_fixed_in_frame_mobjects(info_text)
        
        # Simular viaje: Cambiar Latitud y Longitud del observador
        self.play(
            lat_tracker.animate.set_value(60), # Viajar al norte
            lon_tracker.animate.set_value(10), # Cambiar longitud
            run_time=6,
            rate_func=smooth
        )
        
        # Rotar cámara para ver el resultado final
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(4)