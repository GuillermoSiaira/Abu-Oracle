"""
EP.5 — "The Signal Is Real"
Serie: The Mathematics of Place
Duración objetivo: ~50 segundos
Concepto: 527 eventos biográficos reales.
           Distribución de delta_hf_weighted para eventos positivos vs negativos.
           Cohen's d = 0.44. La señal es medible.

Datos reales del dataset Abu Oracle:
  n_total = 527
  n_positive = 377, mean_delta_hf_positive = -0.619
  n_negative = 69,  mean_delta_hf_negative = -1.554
  Cohen's d ≈ 0.44 (separación entre distribuciones)
"""

from manim import *
import numpy as np
import random


# ── Datos reales del correlator ──────────────────────────────────────────────
MEAN_POS   = -0.619
MEAN_NEG   = -1.554
STD_SHARED = 2.1   # estimado del dataset para visualización honesta
N_POS      = 377
N_NEG      = 69
COHENS_D   = 0.44


def normal_pdf(x, mu, sigma):
    return (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


class TheSignalIsReal(Scene):
    def construct(self):
        self.camera.background_color = "#07080F"

        C_GOLD   = "#D4AF37"
        C_GREEN  = "#50C878"
        C_RED    = "#E05050"
        C_WHITE  = "#E8E8E8"
        C_GRAY   = "#444455"
        C_BLUE   = "#4E94CE"

        # ── TÍTULO ────────────────────────────────────────────────────────────
        title = Text("527 biographical events.", font_size=28, color=C_WHITE)
        subtitle = Text("Historical figures. Verified dates. Real lives.",
                        font_size=18, color=C_GOLD)
        hdr = VGroup(title, subtitle).arrange(DOWN, buff=0.18).to_edge(UP, buff=0.35)
        self.play(FadeIn(hdr, shift=UP * 0.2), run_time=0.7)
        self.wait(0.4)

        # ── EJES ──────────────────────────────────────────────────────────────
        axes = Axes(
            x_range=[-7, 5, 2],
            y_range=[0, 0.22, 0.1],
            x_length=8.5,
            y_length=3.2,
            axis_config={"color": C_GRAY, "stroke_width": 1.2},
            x_axis_config={"include_tip": False},
            y_axis_config={"include_tip": False},
        ).shift(DOWN * 0.55)

        x_lbl = Text("Δ Harmony Field  (event location vs natal location)",
                     font_size=11, color=C_GRAY).next_to(axes, DOWN, buff=0.15)
        y_lbl = Text("Density", font_size=11, color=C_GRAY)
        y_lbl.rotate(90 * DEGREES).next_to(axes, LEFT, buff=0.12)

        self.play(Create(axes), Write(x_lbl), Write(y_lbl), run_time=0.6)

        # ── CURVA EVENTOS NEGATIVOS (primero, en rojo) ────────────────────────
        curve_neg = axes.plot(
            lambda x: normal_pdf(x, MEAN_NEG, STD_SHARED),
            x_range=[-7, 5],
            color=C_RED,
            stroke_width=2.5
        )
        area_neg = axes.get_area(
            curve_neg,
            x_range=[-7, 5],
            color=C_RED,
            opacity=0.18
        )
        neg_lbl = Text(f"Negative events  (n={N_NEG})", font_size=13, color=C_RED)
        neg_lbl.next_to(axes.c2p(MEAN_NEG, 0.19), UP, buff=0.05)

        self.play(Create(curve_neg), FadeIn(area_neg), Write(neg_lbl), run_time=0.9)
        self.wait(0.3)

        # ── CURVA EVENTOS POSITIVOS (segundo, en verde) ───────────────────────
        curve_pos = axes.plot(
            lambda x: normal_pdf(x, MEAN_POS, STD_SHARED),
            x_range=[-7, 5],
            color=C_GREEN,
            stroke_width=2.5
        )
        area_pos = axes.get_area(
            curve_pos,
            x_range=[-7, 5],
            color=C_GREEN,
            opacity=0.18
        )
        pos_lbl = Text(f"Positive events  (n={N_POS})", font_size=13, color=C_GREEN)
        pos_lbl.next_to(axes.c2p(MEAN_POS, 0.19), UP, buff=0.05)

        self.play(Create(curve_pos), FadeIn(area_pos), Write(pos_lbl), run_time=0.9)
        self.wait(0.3)

        # ── FLECHA DE SEPARACIÓN ──────────────────────────────────────────────
        sep_arrow = DoubleArrow(
            axes.c2p(MEAN_NEG, 0.10),
            axes.c2p(MEAN_POS, 0.10),
            color=C_GOLD,
            stroke_width=2,
            buff=0,
            tip_length=0.15
        )
        sep_lbl = Text(f"Cohen's d = {COHENS_D}", font_size=16, color=C_GOLD)
        sep_lbl.next_to(sep_arrow, UP, buff=0.08)

        self.play(Create(sep_arrow), Write(sep_lbl), run_time=0.7)
        self.wait(0.5)

        # ── MENSAJE CENTRAL ───────────────────────────────────────────────────
        self.play(FadeOut(VGroup(axes, curve_neg, area_neg, neg_lbl,
                                  curve_pos, area_pos, pos_lbl,
                                  sep_arrow, sep_lbl, x_lbl, y_lbl)),
                  run_time=0.5)

        msg = VGroup(
            Text("When people are in high-HF locations,", font_size=21, color=C_WHITE),
            Text("positive biographical events cluster.", font_size=21, color=C_WHITE),
            Text(" ", font_size=10),
            Text("This is not astrology.", font_size=24, color=C_GOLD),
            Text("This is a measurable signal.", font_size=24, color=C_GOLD),
        ).arrange(DOWN, buff=0.22).shift(DOWN * 0.1)

        for line in msg:
            self.play(FadeIn(line, shift=RIGHT * 0.1), run_time=0.38)

        self.wait(2.0)
