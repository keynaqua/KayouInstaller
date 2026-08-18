"""Small supersampled raster helpers for crisp Tkinter controls."""

from PIL import Image, ImageDraw, ImageTk


SCALE = 4


def render_photo(master, width: int, height: int, background: str, painter):
    """Render at 4x then downsample so curves do not expose Canvas stair-steps."""
    width, height = max(1, int(width)), max(1, int(height))
    image = Image.new("RGB", (width * SCALE, height * SCALE), background)
    painter(ImageDraw.Draw(image), SCALE)
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image, master=master)


def box(values, scale: int = SCALE):
    return tuple(round(value * scale) for value in values)
