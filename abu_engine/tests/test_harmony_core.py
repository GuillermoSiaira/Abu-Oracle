import math
import pytest

from abu_engine.harmony import (
    ASPECTS,
    angle_to_unit_vector,
    build_circle_vector,
    compute_harmonic_energy,
    compute_harmonics,
    angular_distance_deg,
    gaussian_resonance,
    aggregate_field,
)


def test_angle_to_unit_vector_basic():
    cos0, sin0 = angle_to_unit_vector(0)
    assert cos0 == pytest.approx(1.0)
    assert sin0 == pytest.approx(0.0)

    cos90, sin90 = angle_to_unit_vector(90)
    assert cos90 == pytest.approx(0.0, abs=1e-12)
    assert sin90 == pytest.approx(1.0)


def test_build_circle_vector_order_and_length():
    angles = {
        "Sun": 0,
        "Moon": 30,
        "Mercury": 60,
        "Venus": 90,
        "Mars": 120,
        "Jupiter": 150,
        "Saturn": 180,
        "Uranus": 210,
        "Neptune": 240,
        "Pluto": 270,
        "ASC": 300,
        "MC": 330,
    }
    vector = build_circle_vector(angles)
    assert len(vector) == 24
    # First pair corresponds to Sun
    assert vector[0] == pytest.approx(1.0)
    assert vector[1] == pytest.approx(0.0, abs=1e-12)
    # Mercury at 60° → cos = 0.5, sin = √3/2
    mercury_cos = vector[4]
    mercury_sin = vector[5]
    assert mercury_cos == pytest.approx(0.5)
    assert mercury_sin == pytest.approx(math.sqrt(3) / 2)


def test_harmonic_energy_all_zero_angles():
    angles = [0.0] * 12
    energy = compute_harmonic_energy(angles, k=3)
    assert energy == pytest.approx(12.0)
    harmonics = compute_harmonics(angles)
    for k, value in harmonics.items():
        assert value == pytest.approx(12.0)


def test_harmonic_energy_weights_mismatch():
    angles = [0.0, 10.0]
    with pytest.raises(ValueError):
        compute_harmonic_energy(angles, k=2, weights=[1.0])


def test_angular_distance_wrapping():
    assert angular_distance_deg(10, 350) == pytest.approx(20)
    assert angular_distance_deg(0, 180) == pytest.approx(180)


def test_gaussian_resonance_requires_positive_sigma():
    with pytest.raises(ValueError):
        gaussian_resonance(10, 0, 0)


def test_field_aggregation_groups():
    angles = {
        "Sun": 0,
        "Moon": 60,   # sextile with Sun
        "Mercury": 90,  # square with Sun
        "Venus": 10,
        "Mars": 130,
        "Jupiter": 210,
        "Saturn": 250,
        "Uranus": 307,
        "Neptune": 20,
        "Pluto": 170,
        "ASC": 245,
        "MC": 333,
    }
    sigmas_tight = {name: 0.5 for name in ASPECTS}
    weights = {
        "conjunction": 0.0,
        "sextile": 1.0,
        "square": 1.0,
        "trine": 0.0,
        "opposition": 0.0,
    }

    result = aggregate_field(angles, aspects=ASPECTS, sigmas=sigmas_tight, aspect_weights=weights)

    assert result["HF_harmony"] == pytest.approx(1.0, rel=0.01, abs=1e-3)
    assert result["HF_tension"] == pytest.approx(1.0, rel=0.01, abs=1e-3)
    assert result["HF_conjunction"] == pytest.approx(0.0)
    assert result["HF_total"] == pytest.approx(2.0, rel=0.01, abs=1e-3)
