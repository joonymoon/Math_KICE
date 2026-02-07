"""
Image Processor
Crop whitespace, optimize images for KakaoTalk display
"""

import os
from pathlib import Path
from typing import Tuple, Optional

try:
    from PIL import Image, ImageOps
except ImportError:
    print("PIL not installed. Run: pip install Pillow")
    raise


class ImageProcessor:
    """Process and optimize images for messaging"""

    @staticmethod
    def trim_whitespace(
        image_path: str,
        output_path: str = None,
        padding: int = 20,
        background_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> str:
        """
        Remove whitespace borders from image

        Args:
            image_path: Input image path
            output_path: Output path (default: overwrite input)
            padding: Padding to add after trim (pixels)
            background_color: Background color to trim (default: white)

        Returns:
            Output file path
        """
        output_path = output_path or image_path

        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Get bounding box of non-white area
            bg = Image.new(img.mode, img.size, background_color)
            diff = ImageOps.invert(ImageOps.grayscale(Image.eval(
                Image.blend(img, bg, 0),
                lambda x: 0 if x > 250 else 255
            )))

            bbox = diff.getbbox()

            if bbox:
                # Add padding
                left = max(0, bbox[0] - padding)
                top = max(0, bbox[1] - padding)
                right = min(img.width, bbox[2] + padding)
                bottom = min(img.height, bbox[3] + padding)

                # Crop
                cropped = img.crop((left, top, right, bottom))
                cropped.save(output_path, "PNG", optimize=True)
            else:
                # No content found, save as is
                img.save(output_path, "PNG", optimize=True)

        return output_path

    @staticmethod
    def auto_crop(
        image_path: str,
        output_path: str = None,
        threshold: int = 245,
        remove_footer: bool = True
    ) -> str:
        """
        Auto-crop image - remove header, footer, and bottom whitespace

        Args:
            image_path: Input image path
            output_path: Output path
            threshold: Brightness threshold (0-255)
            remove_footer: Remove bottom area (page numbers, copyright)

        Returns:
            Output file path
        """
        output_path = output_path or image_path

        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")

            orig_width, orig_height = img.size

            # For 250 DPI PDF: actual size is 2924x4136
            # Header (홀수형, 수학 영역, page#): ~480 pixels
            # Footer (page#, copyright): ~350 pixels
            header_px = 480
            footer_px = 350

            # Scale based on actual image height
            scale = orig_height / 4136
            top = int(header_px * scale)
            bottom = orig_height - int(footer_px * scale)

            # Crop header and footer
            img = img.crop((0, top, orig_width, bottom))

            # Smart bottom trim: find content boundary
            gray = img.convert("L")
            pixels = gray.load()

            # Scan from bottom up to find actual content
            content_bottom = img.height
            for y in range(img.height - 1, int(img.height * 0.4), -1):
                dark_count = 0
                for x in range(50, img.width - 50, 20):  # Skip margins
                    if pixels[x, y] < threshold:
                        dark_count += 1
                if dark_count >= 5:  # Found content row
                    content_bottom = min(y + 40, img.height)
                    break

            # Trim bottom whitespace
            if content_bottom < img.height - 80:
                img = img.crop((0, 0, img.width, content_bottom))

            # Resize: 1600px wide for better text readability on mobile
            new_width = 1600
            ratio = new_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            img.save(output_path, "PNG", optimize=True)

        return output_path

    @staticmethod
    def resize_for_kakao(
        image_path: str,
        output_path: str = None,
        max_width: int = 1600,
        max_height: int = 2200
    ) -> str:
        """
        Resize image for optimal KakaoTalk display

        Args:
            image_path: Input image path
            output_path: Output path
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            Output file path
        """
        output_path = output_path or image_path

        with Image.open(image_path) as img:
            # Calculate new size maintaining aspect ratio
            ratio = min(max_width / img.width, max_height / img.height)

            if ratio < 1:
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            img.save(output_path, "PNG", optimize=True)

        return output_path

    @staticmethod
    def process_for_kakao(
        image_path: str,
        output_path: str = None
    ) -> str:
        """
        Full processing pipeline for KakaoTalk images

        Args:
            image_path: Input image path
            output_path: Output path

        Returns:
            Output file path
        """
        output_path = output_path or image_path

        # Step 1: Auto-crop whitespace
        ImageProcessor.auto_crop(image_path, output_path)

        # Step 2: Resize for optimal display
        ImageProcessor.resize_for_kakao(output_path, output_path)

        return output_path


def process_all_images(input_dir: str, output_dir: str = None):
    """Process all images in a directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path

    if output_dir:
        output_path.mkdir(parents=True, exist_ok=True)

    images = list(input_path.glob("*.png"))
    print(f"Processing {len(images)} images...")

    for img_file in images:
        out_file = output_path / img_file.name
        print(f"  Processing: {img_file.name}")
        ImageProcessor.process_for_kakao(str(img_file), str(out_file))

    print("Done!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) >= 3 else None
        process_all_images(input_dir, output_dir)
    else:
        print("Usage: python image_processor.py <input_dir> [output_dir]")
