from manim import *
import math

class ZodiacDrift(Scene):
    def construct(self):
        # Configuración estética
        self.camera.background_color = "#020204" # Negro espacial

        # --- FUNCIÓN AUXILIAR PARA CREAR RUEDAS ZODIACALES ---
        def create_zodiac_wheel(radius, color, label_color, is_sidereal=False):
            wheel_group = VGroup()
            # Círculo principal
            main_circle = Circle(radius=radius, color=color, stroke_width=3)
            wheel_group.add(main_circle)

            # Signos (abreviados para simplificar)
            signs = ["ARI", "TAU", "GEM", "CAN", "LEO", "VIR", 
                     "LIB", "SCO", "SAG", "CAP", "AQU", "PIS"]
            
            for i in range(12):
                angle = i * (2 * PI / 12)
                # Líneas divisorias
                start_point = main_circle.get_center()
                end_point = main_circle.point_at_angle(angle)
                # Hacemos las líneas internas más cortas para que se vea limpio
                divider = Line(start_point * (radius*0.2 if is_sidereal else 0), end_point, color=color, stroke_width=1, stroke_opacity=0.5)
                
                # Etiquetas de texto
                label_angle = angle + (PI / 12) # Centrar el texto en el segmento
                label_pos = radius * 0.85 * np.array([math.cos(label_angle), math.sin(label_angle), 0])
                
                label_text = signs[i]
                # Si es sideral, añadimos un sufijo para diferenciar
                if is_sidereal: label_text += "*"

                label = Text(label_text, font_size=14, color=label_color).move_to(label_pos)
                # Rotar el texto para que siga la curva
                label.rotate(label_angle - PI/2)
                
                wheel_group.add(divider, label)
                
            return wheel_group

        # --- CREACIÓN DE LOS OBJETOS ---

        # 1. Rueda Sideral (Exterior, Azul, Fija a las estrellas)
        sidereal_radius = 3.5
        sidereal_wheel = create_zodiac_wheel(sidereal_radius, BLUE_D, BLUE_B, is_sidereal=True)
        sidereal_title = Text("Sidereal Zodiac (Fixed Stars)", font_size=20, color=BLUE_B).to_corner(UL)
        
        # 2. Rueda Tropical (Interior, Naranja, Basada en estaciones)
        tropical_radius = 2.5
        tropical_wheel = create_zodiac_wheel(tropical_radius, ORANGE, YELLOW)
        tropical_title = Text("Tropical Zodiac (Seasons/Equinox)", font_size=20, color=YELLOW).next_to(sidereal_title, DOWN, aligned_edge=LEFT)

        # 3. Marcador del Punto Vernal (0° Aries Tropical)
        # Una línea roja prominente en el inicio de la rueda naranja
        equinox_marker = Arrow(start=ORIGIN, end=RIGHT*tropical_radius, color=RED, buff=0, stroke_width=4)
        equinox_label = Text("Vernal Equinox (0° Ari)", font_size=16, color=RED).next_to(equinox_marker, RIGHT)
        
        # Agrupamos la rueda tropical con su marcador para que se muevan juntos
        tropical_group = VGroup(tropical_wheel, equinox_marker, equinox_label)

        # --- ANIMACIÓN: EL DESFASE ---

        # Presentación inicial
        self.play(Write(sidereal_title), Write(tropical_title))
        self.play(
            SpinInFromNothing(sidereal_wheel, run_time=1.5),
            SpinInFromNothing(tropical_group, run_time=1.5)
        )
        self.wait(1)

        # Texto explicativo del fenómeno
        explanation = Text("Precession: The slow drift over millennia...", font_size=24).to_edge(DOWN)
        self.play(Write(explanation))

        # LA ACCIÓN PRINCIPAL: Precesión
        # Giramos la rueda tropical lentamente en sentido horario (negativo)
        # mientras la sideral se queda quieta.
        # 30 grados es un signo completo (aprox 2160 años de historia real)
       # --- CORRECCIÓN: Usar ValueTracker para sincronizar arco y rotación ---
        
        # 1. Creamos un "rastreador" de valor que empiece en 0
        drift_tracker = ValueTracker(0)
        
        # El ángulo objetivo (-30 grados)
        target_angle = -30 * DEGREES

        # 2. El arco ahora "escucha" al tracker, no a la rueda
        drift_arc = always_redraw(lambda: Arc(
            radius=tropical_radius*1.1,
            start_angle=0,
            angle=drift_tracker.get_value(), # <--- Aquí está el cambio clave
            color=RED,
            stroke_opacity=0.6,
            stroke_width=6
        ))
        self.add(drift_arc)

        # 3. Animamos las dos cosas JUNTAS en el mismo self.play
        self.play(
            # A. Rotamos la rueda visualmente
            Rotate(tropical_group, angle=target_angle, about_point=ORIGIN),
            # B. Animamos el valor invisible del tracker para que el arco crezca igual
            drift_tracker.animate.set_value(target_angle),
            
            run_time=8,
            rate_func=linear
        )

        # Resultado final
        final_text = Text("Current Drift: ~24° (Ayanamsa)", font_size=20, color=RED).next_to(equinox_label, UP)
        self.play(Write(final_text))
        self.wait(3)