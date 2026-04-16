# Assets — Social Media

Stock de imágenes, logos y banners para RRSS de Abu Oracle.

## Estructura

```
assets/social/
  logos/    — versiones del logo (variantes, tamaños, fondos)
  banners/  — headers/banners para perfiles (Twitter, Facebook, LinkedIn)
  posts/    — imágenes para posts específicos (mundana, cartas, mapas HF)
```

## Convención de nombres

```
{tipo}_{descripcion}_{variante}_{dimensiones}.{ext}

Ejemplos:
  logos/logo_round_dark_500x500.png
  logos/logo_round_light_500x500.png
  banners/banner_steampunk_twitter_1500x500.png
  banners/banner_steampunk_bluesky_3000x1000.png
  posts/stellium_aries_2026_1200x630.png
```

## Dimensiones recomendadas por plataforma

| Plataforma | Perfil | Banner/Header |
|---|---|---|
| Twitter/X | 400×400 | 1500×500 |
| Bluesky | 1000×1000 | 3000×1000 |
| Instagram | 320×320 | — |
| Facebook | 170×170 | 820×312 |
| Farcaster | 500×500 | — |
| Reddit | 256×256 | 1280×384 |
| TikTok | 200×200 | — |

## Archivos actuales

### Logos
- `logo_round_dark_1024x1024.png` — logo circular con triángulo/ojo/engranaje, fondo oscuro
- (agregar variantes: fondo blanco, fondo transparente, solo símbolo sin texto)

### Banners
- `banner_steampunk_dark.png` — reloj/engranajes con "Abu Oracle", formato horizontal

## Generación de imágenes para posts mundanos

El `content_generator.py` genera un `image_prompt` para cada post de Instagram/TikTok/Facebook.
Usar ese prompt con Midjourney, DALL-E o Stable Diffusion y guardar el resultado aquí en `posts/`.
