# FIX-C03 — Dignidades: display puramente tradicional en tarjetas planetarias

## Diagnóstico

BUG-01 en CLAUDE.md ("rulerships modernos en lugar de tradicionales") está
**resuelto a nivel de cálculo** en `extended_calc.py`:
- Las tablas `RULERSHIPS_TRADITIONAL` / `DETRIMENTS_TRADITIONAL` usan correctamente
  Saturno→Acuario/Capricornio, Júpiter→Piscis/Sagitario, Marte→Escorpio/Aries.
- El campo `dignity` de cada planeta ya apunta al resultado tradicional.
- `context-builder.ts` ya usa solo la dignidad tradicional en todo el bloque de Lilly.

**Lo que falta**: el componente `PlanetCard` en `natal-chart-tab.tsx` tiene un
mecanismo `hasDual` que muestra dos badges ("Trad: X | Mod: Y") cuando la dignidad
tradicional difiere de la moderna. Esto ocurre en planetas en Escorpio/Acuario/Piscis
(ej: Saturno en Acuario → "Trad: Domicilio | Mod: Peregrino") y en Urano/Neptuno/Plutón
en cualquier signo.

Un astrólogo tradicional que ve "Mod:" en la carta inmediatamente identifica que el
sistema mezcla doctrinas — impacto directo en credibilidad.

## Archivo a modificar

```
next_app/components/natal-chart-tab.tsx    MODIFY — eliminar dual badge, simplificar
```

No se toca `extended_calc.py` (las tablas ya son correctas).
No se toca `context-builder.ts` (ya usa traditional).
El campo `dignity_modern` se conserva en los datos (backward compat, sin display).

## Spec

### Cambio en `PlanetCard` (función interna de `natal-chart-tab.tsx`)

**Eliminar** el bloque `hasDual`:
```tsx
// ELIMINAR este bloque completo:
const hasDual = !!(
  planet.dignity_traditional &&
  planet.dignity_modern &&
  planet.dignity_traditional !== planet.dignity_modern
);
const dTrad = hasDual ? getDignityInfoFromString(planet.dignity_traditional) : d;
const dMod  = hasDual ? getDignityInfoFromString(planet.dignity_modern)      : d;
```

**Eliminar** el renderizado condicional del doble badge:
```tsx
// ELIMINAR este bloque:
{hasDual ? (
  <div className="flex flex-col items-end gap-0.5">
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${dignityBadgeClass(dTrad)}`}>
      Trad: {dTrad.label} ({fmtScore(dTrad.score)})
    </span>
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${dignityBadgeClass(dMod)}`}>
      Mod: {dMod.label} ({fmtScore(dMod.score)})
    </span>
  </div>
) : (
  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${dignityBadgeClass(d)}`}>
    {d.label}{scoreStr ? ` ${scoreStr}` : ""}
  </span>
)}
```

**Reemplazar** por un único badge con label especial para planetas transpersonales:

```tsx
{/* Single traditional badge — Abu Oracle is a traditional doctrine system */}
<span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${dignityBadgeClass(d)}`}>
  {isTranspersonal(planet.name)
    ? "Transpersonal"
    : `${d.label}${scoreStr ? ` ${scoreStr}` : ""}`}
</span>
```

**Agregar** la helper `isTranspersonal` junto a las otras helpers del componente
(antes del `PlanetCard`):

```tsx
const TRANSPERSONAL_PLANETS = new Set(["Uranus", "Neptune", "Pluto"]);
function isTranspersonal(name: string): boolean {
  return TRANSPERSONAL_PLANETS.has(name);
}
```

### Resultado visual esperado

| Planeta | Signo | Antes | Después |
|---|---|---|---|
| Saturno | Acuario | Trad: Domicilio (+5) · Mod: Peregrino (0) | Domicilio +5 |
| Saturno | Leo | Trad: Detrimento (−4) · Mod: Peregrino (0) | Detrimento −4 |
| Marte | Escorpio | Trad: Domicilio (+5) · Mod: Peregrino (0) | Domicilio +5 |
| Júpiter | Piscis | Trad: Domicilio (+5) · Mod: Peregrino (0) | Domicilio +5 |
| Urano | Acuario | Trad: Peregrino (0) · Mod: Domicilio (+5) | Transpersonal |
| Plutón | Escorpio | Trad: Peregrino (0) · Mod: Domicilio (+5) | Transpersonal |
| Neptuno | Piscis | Trad: Peregrino (0) · Mod: Domicilio (+5) | Transpersonal |

### Actualizar CLAUDE.md

Marcar BUG-01 como resuelto:

```
| BUG-01 | ... | 🟢 Resuelto · FIX-C03 — display puramente tradicional; cálculo ya era correcto desde D3 |
```

## Criterios de aceptación

- [ ] Ninguna tarjeta planetaria muestra "Trad:" ni "Mod:" en el badge
- [ ] Saturno en Acuario muestra "Domicilio +5" (no "Peregrino")
- [ ] Urano/Neptuno/Plutón muestran "Transpersonal" (sin score)
- [ ] El campo `dignity_modern` sigue presente en los datos (no se modifica el backend)
- [ ] `npx tsc --noEmit` pasa sin errores
- [ ] BUG-01 marcado como resuelto en CLAUDE.md
