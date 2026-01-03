from manim import *
import math

class RoseOfVenus(Scene):
    def construct(self):
        # --- CONFIGURACIÓN ESTÉTICA "ABU DARK" ---
        self.camera.background_color = "#050505"
        
        # Colores
        COLOR_EARTH = "#4E94CE"  # Azul Tierra
        COLOR_VENUS = "#D4AF37"  # Oro Venus
        COLOR_SUN = "#F5F5DC"    # Blanco/Crema Sol
        COLOR_LINE = "#FFFFFF"   # Líneas del patrón

        # Títulos
        title = Text("The Rose of Venus", font_size=40, color=COLOR_LINE).to_edge(UP)
        subtitle = Text("8 Earth Years = 13 Venus Years", font_size=24, color=GRAY).next_to(title, DOWN)
        
        # --- PARÁMETROS ORBITALES ---
        # Radios proporcionales (aprox)
        R_EARTH = 3.0
        R_VENUS = R_EARTH * 0.72  # Venus está al 72% de la distancia de la Tierra
        
        # Velocidades angulares (Resonancia 13:8)
        # Tierra = 1 vuelta/año
        # Venus = 1.625 vueltas/año (13/8)
        W_EARTH = 1
        W_VENUS = 13/8

        # --- OBJETOS ---
        sun = Dot(radius=0.15, color=COLOR_SUN).set_glow_factor(0.8)
        
        # Órbitas (Guías visuales tenues)
        orbit_earth = Circle(radius=R_EARTH, color=COLOR_EARTH, stroke_width=1, stroke_opacity=0.3)
        orbit_venus = Circle(radius=R_VENUS, color=COLOR_VENUS, stroke_width=1, stroke_opacity=0.3)

        self.play(FadeIn(sun), Create(orbit_earth), Create(orbit_venus), Write(title), Write(subtitle))

        # --- DINÁMICA ---
        # Usamos un ValueTracker para el Tiempo (t)
        # Queremos simular 8 años terrestres.
        # 1 año = 2*PI radianes. 
        # 8 años = 16*PI.
        years_to_sim = 8
        total_time = years_to_sim * TAU 
        t = ValueTracker(0)

        # Planetas (Puntos móviles)
        def get_earth_pos():
            time = t.get_value()
            return np.array([
                R_EARTH * math.cos(time * W_EARTH),
                R_EARTH * math.sin(time * W_EARTH),
                0
            ])

        def get_venus_pos():
            time = t.get_value()
            return np.array([
                R_VENUS * math.cos(time * W_VENUS),
                R_VENUS * math.sin(time * W_VENUS),
                0
            ])

        earth = always_redraw(lambda: Dot(get_earth_pos(), color=COLOR_EARTH, radius=0.1))
        venus = always_redraw(lambda: Dot(get_venus_pos(), color=COLOR_VENUS, radius=0.1))
        
        self.add(earth, venus)

        # --- EL TRAZADO DEL PATRÓN ---
        # Aquí creamos el grupo que almacenará las miles de líneas
        rose_pattern = VGroup()
        self.add(rose_pattern)

        # Variable para controlar la frecuencia de dibujo (evita saturar la memoria)
        # Dibujamos una línea cada vez que pasa un poquito de tiempo
        self.last_t = 0 

        def update_pattern(mob, dt):
            current_t = t.get_value()
            # Dibujar una línea cada 0.05 radianes de movimiento aprox
            if current_t - self.last_t > 0.05:
                line = Line(
                    earth.get_center(),
                    venus.get_center(),
                    stroke_width=0.5, # Muy fino
                    stroke_opacity=0.2, # Transparente para que se sumen
                    color=COLOR_LINE
                )
                rose_pattern.add(line)
                self.last_t = current_t

        rose_pattern.add_updater(update_pattern)

        # --- ACCIÓN ---
        # Animamos el ValueTracker desde 0 hasta 8 años
        # run_time=14 segundos para que sea lento y satisfactorio
        self.play(
            t.animate.set_value(total_time),
            run_time=14, 
            rate_func=linear # Importante: velocidad constante astronómica
        )

        # Final: Limpiamos para dejar solo la flor
        rose_pattern.remove_updater(update_pattern) # Dejar de dibujar
        
        self.play(
            FadeOut(earth), FadeOut(venus), 
            FadeOut(orbit_earth), FadeOut(orbit_venus),
            FadeOut(sun),
            rose_pattern.animate.set_color(PINK).set_opacity(0.4) # Colorear la rosa final
        )
        
        # Texto final místico/científico CORREGIDO
        final_txt = Text("Geometry is the archetype of the Soul.", font_size=24, color=WHITE).to_edge(DOWN)
        self.play(Write(final_txt))
        
        self.wait(3)