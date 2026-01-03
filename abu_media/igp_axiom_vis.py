from manim import *
import math

class IGP_Axiom_Vis(Scene):
    def construct(self):
        # Configuración estética "Abu Dark"
        self.camera.background_color = "#050505"
        
        # --- TEXTOS AXIOMÁTICOS ---
        title = Text("Axiom 5.2: Geography as Operator", font_size=32, color=WHITE).to_edge(UP)
        subtitle = Text("Navigating the Harmony Field (IGP)", font_size=24, color=GRAY).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle))

        # --- EL SISTEMA (Tierra + Cielo) ---
        
        # 1. La Tierra (Centro)
        earth_radius = 1.5
        earth = Circle(radius=earth_radius, color=BLUE, stroke_width=2).set_fill(BLUE_E, opacity=0.3)
        earth_label = Text("Terra", font_size=16, color=BLUE).move_to(ORIGIN)
        
        # 2. El Cielo (Órbita Planetaria - Simbólica)
        sky_radius = 3.5
        sky_orbit = Circle(radius=sky_radius, color=GRAY, stroke_opacity=0.2)
        
        # 3. Los Planetas (Fijos en t=0)
        # Saturno (Maléfico/Tensión)
        saturn_angle = 120 * DEGREES
        saturn_pos = sky_radius * np.array([math.cos(saturn_angle), math.sin(saturn_angle), 0])
        saturn = Dot(saturn_pos, color=RED)
        saturn_lbl = Text("Saturn", font_size=16, color=RED).next_to(saturn, UP)
        
        # Júpiter (Benéfico/Armonía)
        jupiter_angle = 30 * DEGREES
        jupiter_pos = sky_radius * np.array([math.cos(jupiter_angle), math.sin(jupiter_angle), 0])
        jupiter = Dot(jupiter_pos, color=GOLD)
        jupiter_lbl = Text("Jupiter", font_size=16, color=GOLD).next_to(jupiter, UR)

        universe = VGroup(earth, earth_label, sky_orbit, saturn, saturn_lbl, jupiter, jupiter_lbl)
        self.play(DrawBorderThenFill(universe))

        # --- EL OPERADOR (Usuario IGP) ---
        
        # Usamos un ValueTracker para simular la posición del usuario
        user_angle_tracker = ValueTracker(120 * DEGREES) 
        
        # El punto del usuario sobre la Tierra
        def get_user_point():
            ang = user_angle_tracker.get_value()
            return earth_radius * np.array([math.cos(ang), math.sin(ang), 0])

        user_dot = always_redraw(lambda: Dot(get_user_point(), color=WHITE, radius=0.08))
        
        # Horizonte Local (Axioma 3.2)
        local_horizon = always_redraw(lambda: Line(LEFT, RIGHT, color=WHITE, stroke_opacity=0.5, stroke_width=2)
                                      .scale(1)
                                      .rotate(user_angle_tracker.get_value() + 90*DEGREES)
                                      .move_to(get_user_point()))

        self.play(FadeIn(user_dot), Create(local_horizon))
        
        # --- LÍNEAS DE FUERZA ---
        
        def get_saturn_line():
            u_pos = get_user_point()
            dist = np.linalg.norm(u_pos - saturn_pos)
            color = interpolate_color(RED, GRAY, min(1, dist/4))
            opacity = 1.0 if dist < 2.5 else 0.3
            return Line(u_pos, saturn_pos, color=color, stroke_opacity=opacity)

        def get_jupiter_line():
            u_pos = get_user_point()
            dist = np.linalg.norm(u_pos - jupiter_pos)
            color = interpolate_color(GOLD, GRAY, min(1, dist/4))
            opacity = 1.0 if dist < 2.5 else 0.3
            return Line(u_pos, jupiter_pos, color=color, stroke_opacity=opacity)

        line_sat = always_redraw(get_saturn_line)
        line_jup = always_redraw(get_jupiter_line)
        self.add(line_sat, line_jup)

        # --- DASHBOARD (H Score) ---
        score_box = Rectangle(width=4, height=1, color=WHITE).to_corner(DR)
        score_title = Text("Harmony Field (H)", font_size=20).move_to(score_box.get_top() + DOWN*0.2)
        
        # ESTA ES LA PARTE QUE REQUIERE LATEX
        score_val = always_redraw(lambda: 
            DecimalNumber(
                (5 - np.linalg.norm(get_user_point() - jupiter_pos)) * 20 - 
                (5 - np.linalg.norm(get_user_point() - saturn_pos)) * 20 + 50,
                num_decimal_places=1,
                color=WHITE if np.linalg.norm(get_user_point() - jupiter_pos) > 2.5 else GOLD
            ).move_to(score_box.get_center() + DOWN*0.1)
        )
        self.play(Create(score_box), Write(score_title), Write(score_val))

        # --- ACCIÓN ---
        action_text = Text("User moves. Time is fixed. Destiny changes.", font_size=20, color=BLUE_C).to_edge(DOWN)
        self.play(Write(action_text))
        
        self.play(
            user_angle_tracker.animate.set_value(30 * DEGREES),
            run_time=6,
            rate_func=smooth
        )
        
        final_text = Text("Optimization Complete", font_size=20, color=GOLD).next_to(action_text, UP)
        self.play(Write(final_text))
        self.wait(2)