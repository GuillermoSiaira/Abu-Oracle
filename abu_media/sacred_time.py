from manim import *
import math

class SacredTimeStructure(Scene):
    def construct(self):
        # --- Configuración Estética ---
        self.camera.background_color = "#080808" # Negro casi absoluto
        GOLD_DARK = "#C5A059"
        
        # --- CAPA 1: SIDEREAL TIME (Geometría Sagrada / El Fondo) ---
        # Representa el orden cósmico inmutable
        def create_sacred_pattern():
            circles = VGroup()
            base_radius = 3.5
            # Círculo base
            circles.add(Circle(radius=base_radius, color=BLUE_E, stroke_width=1, stroke_opacity=0.3))
            # 6 Círculos de la Flor de la Vida
            for i in range(6):
                angle = i * PI / 3
                center = base_radius * np.array([math.cos(angle), math.sin(angle), 0])
                circles.add(Circle(radius=base_radius, color=BLUE_E, stroke_width=1, stroke_opacity=0.2).move_to(center))
            return circles

        sacred_bg = create_sacred_pattern()
        
        # Animación de entrada
        self.play(FadeIn(sacred_bg, run_time=2))
        # Rotación eterna y lenta (Precesión de los Equinoccios)
        sacred_bg.add_updater(lambda m, dt: m.rotate(0.02 * dt)) 

        # --- TÍTULOS ---
        title = Text("III. The Shape of Time", font_size=42, color=WHITE).to_edge(UP, buff=0.5)
        subtitle = Text("Mean vs. True Solar Time", font_size=24, color=GRAY_B).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle))

        # --- CAPA 2: MEAN SOLAR TIME (Tiempo Civil / La Máquina) ---
        # Círculo perfecto, movimiento constante
        orbit_mean = Circle(radius=2.2, color=GRAY, stroke_opacity=0.5)
        sun_mean = Dot(color=GRAY, radius=0.12)
        label_mean = Text("Mean", font_size=16, color=GRAY).next_to(sun_mean, UP)
        group_mean = VGroup(sun_mean, label_mean)
        
        self.play(Create(orbit_mean), FadeIn(group_mean))

        # --- CAPA 3: TRUE SOLAR TIME (Tiempo Real / El Fenómeno) ---
        # Elipse sutil, movimiento orgánico
        orbit_true = Ellipse(width=5.0, height=3.8, color=GOLD).rotate(15*DEGREES)
        sun_true = Dot(color=GOLD, radius=0.15)
        # Efecto de brillo (Glow)
        sun_glow = always_redraw(lambda: sun_true.copy().set_stroke(GOLD, 5, 0.4).set_fill(opacity=0).scale(1.3))
        label_true = Text("True", font_size=16, color=GOLD).next_to(sun_true, UP)
        group_true = VGroup(sun_true, label_true)

        self.play(Create(orbit_true), FadeIn(group_true), FadeIn(sun_glow))

        # --- CAPA 4: LOCAL ROTATIONAL (El Observador / La Cruz) ---
        # El centro estático donde estamos nosotros
        earth = Dot(ORIGIN, color=BLUE)
        horizon = Line(LEFT, RIGHT, color=BLUE_C, stroke_width=2).scale(0.5)
        axis = Line(UP, DOWN, color=BLUE_C, stroke_width=2).scale(0.5)
        observer = VGroup(earth, horizon, axis)
        self.play(GrowFromCenter(observer))

        self.wait(1)

        # --- ANIMACIÓN: LA DISCREPANCIA (Ecuación del Tiempo) ---
        cycle_time = 10
        
        # Línea roja que conecta la mentira (Mean) con la verdad (True)
        connector = always_redraw(lambda: Line(sun_mean.get_center(), sun_true.get_center(), color=RED, stroke_opacity=0.8))
        text_error = Text("Equation of Time (Divergence)", font_size=20, color=RED).to_corner(DL)
        
        self.play(FadeIn(connector), Write(text_error))

        # El ciclo de movimiento
        self.play(
            # El Sol Medio se mueve linealmente (aburrido, mecánico)
            MoveAlongPath(group_mean, orbit_mean, rate_func=linear, run_time=cycle_time),
            
            # El Sol Verdadero acelera y frena (Kepler / Orgánico)
            MoveAlongPath(
                group_true, 
                orbit_true, 
                # Función personalizada: t + amplitud * sin(t) para crear aceleración
                rate_func=lambda t: t + 0.12 * math.sin(2 * PI * t), 
                run_time=cycle_time
            ),
            run_time=cycle_time
        )
        
        self.wait(3)