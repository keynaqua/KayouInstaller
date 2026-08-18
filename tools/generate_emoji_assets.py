from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT = Path(__file__).parents[1] / "assets" / "ui" / "emoji"
ICONS = {
    "pending": "⏳", "success": "✅", "error": "❌", "skipped": "🔆", "validate": "🍱",
    "java": "☕", "loader_neoforge": "🦊", "loader_fabric": "📃",
    "profile": "🏯", "mods": "⛲", "resourcepacks": "🎍",
    "shaders": "🌌", "datapacks": "🌸", "configs": "🫧", "activate": "✨",
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(r"C:\Windows\Fonts\seguiemj.ttf", 216)
    for name, character in ICONS.items():
        source = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
        draw = ImageDraw.Draw(source)
        bounds = draw.textbbox((0, 0), character, font=font, embedded_color=True)
        width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        draw.text(
            ((360 - width) / 2 - bounds[0], (360 - height) / 2 - bounds[1]),
            character, font=font, embedded_color=True,
        )
        content = source.getbbox()
        cropped = source.crop(content) if content else source
        cropped.thumbnail((68, 68), Image.Resampling.LANCZOS)
        image = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
        image.alpha_composite(cropped, ((80 - cropped.width) // 2, (80 - cropped.height) // 2))
        image.save(OUTPUT / f"{name}.png")
    for name, color, enabled in (("enabled", "#19d98b", True), ("disabled", "#ff5f72", False)):
        image = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((1, 1, 22, 22), radius=5, fill=color)
        if enabled:
            draw.line((6, 12, 10, 16, 18, 7), fill="white", width=3, joint="curve")
        else:
            draw.line((7, 7, 17, 17), fill="white", width=3)
            draw.line((17, 7, 7, 17), fill="white", width=3)
        image.save(OUTPUT / f"{name}.png")

    no_world = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(no_world)
    draw.ellipse((6, 6, 74, 74), fill="#f04f64")
    draw.line((27, 27, 53, 53), fill="white", width=7)
    draw.line((53, 27, 27, 53), fill="white", width=7)
    no_world.save(OUTPUT / "no_world.png")



if __name__ == "__main__":
    main()
