Title: The Mathematical Formalization of Abu Oracle's Algorithms
Author: Atilio Guillermo Alberto Siaira — Abu Oracle Project
Date: 2026-06-04
License: CC BY 4.0   (atribución requerida; bien público)
Source: https://abu-oracle.com/corpus/formalization-en

---

# The Mathematical Formalization of Abu Oracle's Algorithms
Based on: J. G. Mascheroni — Course on Geodesy
Module: `abu_engine/core/houses.py` and `abu_engine/harmony/field.py`

This document makes explicit the spherical trigonometry underlying the calculation of the natal chart and house division (Placidus System), moving the model away from symbolic representation to ground it in celestial kinematics.

## 1. The Position Triangle (Base Coordinates)
To anchor the celestial vault to the observer's local horizon, the engine solves the Position Triangle ($ZP_nE$). The vertices are:
- Elevated Pole ($P_n$)
- Observer's Zenith ($Z$)
- Celestial body or ecliptic degree ($E$)

### Fundamental Sides and Angles
- Side $ZP_n$: $90^\circ - \varphi$ (where $\varphi$ is the observer's latitude)
- Side $ZE$: $\zeta$ (Zenith Distance)
- Side $EP_n$: $90^\circ - \delta$ (where $\delta$ is the body's declination)
- Angle $P_n$: $H$ (Hour Angle)
- Angle $Z$: $180^\circ - A$ (where $A$ is the Azimuth)

From Gauss's equations applied to this triangle, we obtain the Zenith Distance ($\zeta$), which is vital to know the body's altitude above the horizon:

$$\cos \zeta = \sin \varphi \sin \delta + \cos \varphi \cos \delta \cos H$$

And to locate the exact cardinal position (Azimuth $A$), fundamental for the Ascendant:

$$\tan A = \frac{\cos \delta \sin H}{-\cos \varphi \sin \delta + \sin \varphi \cos \delta \cos H}$$

## 2. Annual Kinematics: The Obliquity of the Ecliptic
The longitudinal advance of the Sun (and planets) on the ecliptic ($l$) is projected onto the celestial equator (Right Ascension, $\alpha$) undergoing a geometric deformation due to the inclination of the Earth's axis ($\epsilon \approx 23.5^\circ$).

The engine calculates this projection using the following geodetic equation:

$$\tan \alpha = \tan l \cdot \cos \epsilon$$

Note: This formula is responsible for the "short and long ascensions". It explains why signs near the equinoxes (Aries/Libra) ascend in radically different times than those near the solstices (Cancer/Capricorn), distorting the size of houses on a two-dimensional plane.

## 3. House Division Algorithm (Placidus System)
The Placidus system, used by `abu_engine`, does not divide physical space, but rather the time it takes for a zodiacal degree to travel from the horizon to the meridian.

### A. The Diurnal Semi-Arc Equation (The Horizon Limit)
To calculate the houses, we must first know when a zodiac degree "touches" the horizon. Mascheroni establishes that the altitude $h$ of a celestial body is $90^\circ - \zeta$. Therefore, on the horizon the altitude is zero ($h = 0$).

Substituting $0$ into the general altitude formula ($\sin h = \sin \varphi \sin \delta + \cos \varphi \cos \delta \cos H$), we deduce the fundamental equation of diurnal motion:

$$0 = \sin \varphi \sin \delta + \cos \varphi \cos \delta \cos H$$

By solving for the Hour Angle ($H$), we obtain the Diurnal Semi-Arc (SAD):

$$\cos H = -\tan \varphi \cdot \tan \delta$$

- Algorithmic Implication: the resulting value $H$ represents, in equatorial degrees (where $1^\circ = 4$ minutes of time), the exact arc from the body's rising (Ascendant) to its upper culmination (Midheaven).

### B. The Trisection (Calculation of Intermediate Cusps)
The core loop of the Placidus algorithm iterates using the Diurnal Semi-Arc to find the ecliptic degrees that divide the time of ascension into three equal parts (Temporal Hours).

1. 10th House Cusp (Midheaven): calculated directly through the Right Ascension of the meridian (local Hour Angle $H = 0^\circ$).
2. 1st House Cusp (Ascendant): the ecliptic degree whose Azimuth $A$ exactly intersects the eastern horizon.
3. Intermediate Cusps (11th and 12th Houses): the algorithm iterates over the ecliptic testing different degrees (with variable declination $\delta$). For each candidate degree:
   - Calculates its Diurnal Semi-Arc: $H_{candidate} = \arccos(-\tan \varphi \cdot \tan \delta_{candidate})$
   - Divides $H_{candidate}$ by $3$. This defines a Temporal Hour ($HT$).
   - The 12th House is that specific degree of the zodiac whose Right Ascension distance to the upper local meridian is exactly $\tfrac{1}{3} H_{candidate}$ (or $1\ HT$).
   - The 11th House is that degree whose distance to the meridian is exactly $\tfrac{2}{3} H_{candidate}$ (or $2\ HT$).

## 4. Computational Implication (Big-O Notation)
Because $\delta$ is a non-linear function of ecliptic longitude $l$, intermediate cusps cannot be isolated with a simple closed-form equation, requiring in the backend root-finding algorithms (iterative numerical methods like Newton-Raphson). This turns the Placidus house division calculation into the operation with the highest algorithmic cost within the core engine $O(K)$, compared to the constant $O(1)$ of simple spatial division house systems.
