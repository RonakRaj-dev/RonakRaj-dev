
import argparse
import cv2
import numpy as np

from PIL import Image
from rembg import remove, new_session
from pathlib import Path


def remove_background(image: Image.Image) -> Image.Image:
    """
    Remove the background and return an RGBA image.
    """
    session = new_session("u2net")

    output = remove(
        image,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10
    )

    return output.convert("RGBA")


def enhance_contrast(image: Image.Image) -> Image.Image:
    """
    Apply CLAHE to the L channel in LAB color space.
    Preserves color while enhancing local contrast.
    """
    rgb = np.array(image.convert("RGB"))

    # RGB to LAB
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)

    # Split LAB channels
    l_channel, a_channel, b_channel = cv2.split(lab)

    # Apply CLAHE to luminance
    clahe = cv2.createCLAHE(
        clipLimit=2.5,
        tileGridSize=(8, 8)
    )

    enhanced_l = clahe.apply(l_channel)

    # Merge channels
    enhanced_lab = cv2.merge(
        [enhanced_l, a_channel, b_channel]
    )

    # LAB to RGB
    enhanced_rgb = cv2.cvtColor(
        enhanced_lab,
        cv2.COLOR_LAB2RGB
    )

    return Image.fromarray(enhanced_rgb)


def composite_white(foreground: Image.Image) -> Image.Image:
    """
    Composite the transparent foreground onto pure white.
    """
    white_background = Image.new(
        "RGBA",
        foreground.size,
        (255, 255, 255, 255)
    )

    composited = Image.alpha_composite(
        white_background,
        foreground
    )

    return composited.convert("RGB")


def prep_photo(input_path: str, output_path: str):
    """
    Complete photo preparation pipeline.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input image not found: {input_path}"
        )

    print("[1/3] Loading image...")

    image = Image.open(input_path).convert("RGB")

    print("[2/3] Removing background...")

    foreground = remove_background(image)

    print("Enhancing facial contrast...")

    # Enhance RGB while retaining original alpha mask
    alpha = foreground.getchannel("A")

    enhanced = enhance_contrast(foreground)

    enhanced.putalpha(alpha)

    print("[3/3] Compositing onto white background...")

    final_image = composite_white(enhanced)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    final_image.save(output_path, quality=95)

    print(f"Photo preparation completed: {output_path}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Prepare a portrait for ASCII conversion."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Input portrait image path"
    )

    parser.add_argument(
        "--output",
        default="data/prepared_photo.png",
        help="Output image path"
    )

    args = parser.parse_args()

    prep_photo(args.input, args.output)
