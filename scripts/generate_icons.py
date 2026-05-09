from PIL import Image
import os


SRC = "assets/social/logos/abu_oracle_logo_v1.png"
OUT_DIR = "next_app/public/icons"


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    img = Image.open(SRC).convert("RGBA")
    for size in (192, 512):
        img.resize((size, size), Image.LANCZOS).save(f"{OUT_DIR}/icon-{size}.png")

    padded_size = 512
    pad = int(padded_size * 0.1)
    inner = padded_size - 2 * pad
    bg = Image.new("RGBA", (padded_size, padded_size), (15, 23, 42, 255))
    inner_img = img.resize((inner, inner), Image.LANCZOS)
    bg.paste(inner_img, (pad, pad), inner_img)
    bg.save(f"{OUT_DIR}/icon-512-maskable.png")
    print("Icons generated.")


if __name__ == "__main__":
    main()
