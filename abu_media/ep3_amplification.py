"""
EP.3 — "The Amplification Mechanism"
Serie: The Mathematics of Place
Duración objetivo: ~45 segundos
Concepto: La función gaussiana de angularidad.
           Planetas cerca del ASC/MC/DSC/IC se amplifican.
           Eso crea variación geográfica en el HF.
"""

from manim import *
import math
import numpy as np


def gaussian_angularity(angle_deg, sigma=10.0):
    """
    Fuerza gaussiana de angularidad.
    Máxima en 0° (conjunción exacta con eje), cae a sigma grados.
    """
    return math.exp(-0.5 * (angle_deg / sigma) ** 2)


class TheAmplificationMechanism(Scene):
    def construct(self):
        self.camera.background_color = "#07080F"

        C_GOLD  = "#D4AF37"
        C_BLUE  = "#4E94CE"
        C_WHITE = "#E8E8E8"
        C_GRAY  = "#444455"
        C_GREEN = "#50C878"
        C_DIM   = "#2a2a3a"

        # ── TÍTULO ───────────────────────────────────────────────────────────
        title = Text("Angular planets are amplified.", font_size=28, color=C_WHITE)
        subtitle = Text("This is not metaphor. This is a Gaussian function.",
                        font_size=18, color=C_GOLD)
        hdr = VGroup(title, subtitle).arrange(DOWN, buff=0.18).to_edge(UP, buff=0.4)
        self.play(FadeIn(hdr, shift=UP * 0.2), run_time=0.7)
        self.wait(0.3)

        # ── PARTE 1: LA CURVA GAUSSIANA ──────────────────────────────────────
        axes = Axes(
            x_range=[-90, 90, 30],
            y_range=[0, 1.1, 0.5],
            x_length=7,
            y_length=2.8,
            axis_config={"color": C_GRAY, "stroke_width": 1.5},
            x_axis_config={"include_tip": False},
            y_axis_config={"include_tip": False},
        ).shift(DOWN * 0.4)

        x_lbl = Text("Distance from ASC / MC / DSC / IC (degrees)",
                     font_size=11, color=C_GRAY).next_to(axes, DOWN, buff=0.15)
        y_lbl = Text("Amplification", font_size=11, color=C_GRAY)
        y_lbl.rotate(90 * DEGREES).next_to(axes, LEFT, buff=0.1)

        sigma = 10.0
        curve = axes.plot(
            lambda x: gaussian_angularity(x, sigma),
            x_range=[-90, 90],
            color=C_GOLD,
            stroke_width=2.5
        )

        # Línea vertical en 0° (eje angular)
        zero_line = axes.get_vertical_line(axes.c2p(0, 1), color=C_BLUE, stroke_width=1.5)
        zero_lbl = Text("Exact\nangularity", font_size=11, color=C_BLUE,
                        line_spacing=1.2).next_to(zero_line, UP, buff=0.1)

        # Dot que se mueve sobre la curva
        angle_tracker = ValueTracker(-80)

        def get_curve_dot():
            x = angle_tracker.get_value()
            y = gaussian_angularity(x, sigma)
            return Dot(axes.c2p(x, y), color=C_WHITE, radius=0.07)

        def get_strength_label():
            x = angle_tracker.get_value()
            y = gaussian_angularity(x, sigma)
            pct = int(y * 100)
            col = interpolate_color(ManimColor("#444455"), ManimColor(C_GOLD), y)
            return Text(f"Strength: {pct}%", font_size=14, color=col).to_corner(DR).shift(UP * 0.5)

        curve_dot = always_redraw(get_curve_dot)
        strength_lbl = always_redraw(get_strength_label)

        self.play(
            Create(axes), Write(x_lbl), Write(y_lbl),
            run_time=0.6
        )
        self.play(Create(curve), Create(zero_line), Write(zero_lbl), run_time=0.8)
        self.play(FadeIn(curve_dot), FadeIn(strength_lbl), run_time=0.3)

        # El punto recorre la curva de -80° a 0° (planeta se acerca al eje)
        self.play(
            angle_tracker.animate.set_value(0),
            run_time=3.5,
            rate_func=smooth
        )
        self.wait(0.4)

        # ── PARTE 2: CONSECUENCIA GEOGRÁFICA ─────────────────────────────────
        self.play(FadeOut(VGroup(axes, curve, zero_line, zero_lbl,
                                 x_lbl, y_lbl, curve_dot, strength_lbl)),
                  run_time=0.5)

        consequence = VGroup(
            Text("Move 5° of latitude.", font_size=24, color=C_WHITE),
            Text("Jupiter moves from 45° to 8° from your MC.", font_size=20, color=C_GOLD),
            Text("Amplification: 10% → 97%", font_size=22, color=C_GREEN),
        ).arrange(DOWN, buff=0.35).shift(DOWN * 0.2)

        for line in consequence:
            self.play(FadeIn(line, shift=RIGHT * 0.15), run_time=0.45)
            self.wait(0.2)

        self.wait(0.5)

        # ── CIERRE ────────────────────────────────────────────────────────────
        self.play(FadeOut(consequence), run_time=0.4)
        close_text = VGroup(
            Text("This is why the map changes.", font_size=24, color=C_WHITE),
            Text("Geography is the operator.", font_size=20, color=C_GOLD),
        ).arrange(DOWN, buff=0.25).shift(DOWN * 0.1)
        self.play(FadeIn(close_text, shift=UP * 0.1), run_time=0.6)
        self.wait(2.0)
