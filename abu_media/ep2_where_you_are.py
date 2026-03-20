"""
EP.2 — "Where You Are Changes Everything"
Serie: The Mathematics of Place
Duración objetivo: ~45 segundos
Concepto: El horizonte local cambia con la latitud.
           Un planeta angular se amplifica. Eso es el mecanismo del HF.
"""

from manim import *
import math
import numpy as np


class WhereYouAreChangesEverything(Scene):
    def construct(self):
        self.camera.background_color = "#07080F"

        # ── PALETA ──────────────────────────────────────────────────────────
        C_GOLD   = "#D4AF37"
        C_BLUE   = "#4E94CE"
        C_WHITE  = "#E8E8E8"
        C_GRAY   = "#555566"
        C_RED    = "#E05050"
        C_GREEN  = "#50C878"
        C_DIM    = "#333344"

        # ── TÍTULO (entra y sale) ────────────────────────────────────────────
        title = Text("When you move, the sky doesn't change.",
                     font_size=28, color=C_WHITE)
        subtitle = Text("But your relationship to it does.",
                        font_size=22, color=C_GOLD)
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=0.2).to_edge(UP, buff=0.4)

        self.play(FadeIn(title_group, shift=UP * 0.2), run_time=0.8)
        self.wait(0.5)

        # ── ESCENA: TIERRA + CIELO ───────────────────────────────────────────
        earth_r = 1.4
        sky_r   = 3.2

        earth = Circle(radius=earth_r, color=C_BLUE, stroke_width=2)
        earth.set_fill(color="#1a2a4a", opacity=0.6)
        earth_lbl = Text("Earth", font_size=14, color=C_BLUE).move_to(ORIGIN)

        sky_ring = Circle(radius=sky_r, color=C_DIM, stroke_width=1)

        # Planeta A — Jupiter (benéfico, oro)
        jup_angle = 20 * DEGREES
        jup_pos = sky_r * np.array([math.cos(jup_angle), math.sin(jup_angle), 0])
        jupiter = Dot(jup_pos, color=C_GOLD, radius=0.1)
        jup_lbl = Text("Jupiter", font_size=13, color=C_GOLD).next_to(jupiter, UR, buff=0.1)

        # Planeta B — Saturn (tensión, rojo)
        sat_angle = 130 * DEGREES
        sat_pos = sky_r * np.array([math.cos(sat_angle), math.sin(sat_angle), 0])
        saturn = Dot(sat_pos, color=C_RED, radius=0.1)
        sat_lbl = Text("Saturn", font_size=13, color=C_RED).next_to(saturn, UL, buff=0.1)

        scene_group = VGroup(sky_ring, earth, earth_lbl, jupiter, jup_lbl, saturn, sat_lbl)
        scene_group.shift(DOWN * 0.3)

        self.play(DrawBorderThenFill(scene_group), run_time=1.0)

        # ── OBSERVADOR: POSICIÓN 1 (izquierda = latitud baja) ───────────────
        obs_tracker = ValueTracker(160 * DEGREES)

        def get_obs_pos():
            a = obs_tracker.get_value()
            return earth_r * np.array([math.cos(a), math.sin(a), 0]) + DOWN * 0.3

        obs_dot = always_redraw(
            lambda: Dot(get_obs_pos(), color=C_WHITE, radius=0.09)
        )

        # Horizonte local (perpendicular al radio en ese punto)
        horizon_len = 0.7

        def get_horizon():
            a = obs_tracker.get_value()
            pos = get_obs_pos()
            perp = np.array([-math.sin(a), math.cos(a), 0])
            return Line(
                pos - perp * horizon_len,
                pos + perp * horizon_len,
                color=C_WHITE, stroke_width=2.5, stroke_opacity=0.85
            )

        horizon = always_redraw(get_horizon)

        # MC local (perpendicular al horizonte = misma dirección que el radio)
        def get_mc_line():
            a = obs_tracker.get_value()
            pos = get_obs_pos()
            radial = np.array([math.cos(a), math.sin(a), 0])
            return Line(
                pos,
                pos + radial * 0.6,
                color=C_GOLD, stroke_width=2, stroke_opacity=0.7
            )

        mc_line = always_redraw(get_mc_line)
        mc_lbl_static = Text("MC", font_size=12, color=C_GOLD)

        # Línea de angularidad: obs → Jupiter
        def get_jup_line():
            obs = get_obs_pos()
            a = obs_tracker.get_value()
            mc_dir = np.array([math.cos(a), math.sin(a), 0])
            jup_dir = (jup_pos - obs) / np.linalg.norm(jup_pos - obs)
            angular_score = abs(np.dot(mc_dir, jup_dir))
            op = 0.2 + 0.8 * angular_score
            col = interpolate_color(ManimColor(C_DIM), ManimColor(C_GOLD), angular_score)
            return Line(obs, jup_pos, color=col, stroke_opacity=op, stroke_width=1.5)

        def get_sat_line():
            obs = get_obs_pos()
            a = obs_tracker.get_value()
            mc_dir = np.array([math.cos(a), math.sin(a), 0])
            sat_dir = (sat_pos - obs) / np.linalg.norm(sat_pos - obs)
            angular_score = abs(np.dot(mc_dir, sat_dir))
            op = 0.2 + 0.8 * angular_score
            col = interpolate_color(ManimColor(C_DIM), ManimColor(C_RED), angular_score)
            return Line(obs, sat_pos, color=col, stroke_opacity=op, stroke_width=1.5)

        jup_line = always_redraw(get_jup_line)
        sat_line = always_redraw(get_sat_line)

        self.play(
            FadeIn(obs_dot),
            Create(horizon),
            Create(mc_line),
            run_time=0.6
        )
        self.play(Create(jup_line), Create(sat_line), run_time=0.5)

        # ── SCORE HF en tiempo real ──────────────────────────────────────────
        score_label = Text("Harmony Field", font_size=14, color=C_GRAY).to_corner(DR).shift(UP * 0.6)

        def get_hf_score():
            obs = get_obs_pos()
            a = obs_tracker.get_value()
            mc_dir = np.array([math.cos(a), math.sin(a), 0])
            jup_dir = (jup_pos - obs) / np.linalg.norm(jup_pos - obs)
            sat_dir = (sat_pos - obs) / np.linalg.norm(sat_pos - obs)
            jup_ang = abs(np.dot(mc_dir, jup_dir))
            sat_ang = abs(np.dot(mc_dir, sat_dir))
            # HF simplificado pero honesto: benéfico angular suma, maléfico angular resta
            score = jup_ang * 8.0 - sat_ang * 6.0
            return score

        score_num = always_redraw(lambda: DecimalNumber(
            get_hf_score(),
            num_decimal_places=1,
            color=C_GREEN if get_hf_score() > 0 else C_RED,
            font_size=28
        ).next_to(score_label, DOWN, buff=0.1))

        self.play(FadeIn(score_label), Write(score_num), run_time=0.5)

        # ── TEXTO INTERMEDIO ─────────────────────────────────────────────────
        mid_text = Text("Angular planets are amplified.", font_size=20, color=C_WHITE)
        mid_text.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(mid_text), run_time=0.4)
        self.wait(0.3)

        # ── MOVIMIENTO: el observador viaja ──────────────────────────────────
        # de 160° (izq, Saturn angular) a 20° (der, Jupiter angular)
        self.play(
            obs_tracker.animate.set_value(25 * DEGREES),
            run_time=5.0,
            rate_func=smooth
        )
        self.wait(0.4)

        # ── TEXTO FINAL ──────────────────────────────────────────────────────
        self.play(FadeOut(mid_text), run_time=0.3)
        end_text = Text("That's the mechanism.\nThe math behind the map.",
                        font_size=20, color=C_GOLD,
                        line_spacing=1.3)
        end_text.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(end_text, shift=UP * 0.1), run_time=0.6)
        self.wait(2.0)
