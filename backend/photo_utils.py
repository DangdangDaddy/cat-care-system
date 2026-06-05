"""照片处理工具。

这里保持为纯函数，方便上传接口、相似照片检测和后续批量导入复用。
"""

import hashlib
import io
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps

EXIF_DATETIME_KEYS = (36867, 36868, 306)
THUMBNAIL_SIZE = (480, 480)
THUMBNAIL_QUALITY = 92
PHOTO_HASH_SIZE = 8


def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_average_hash_from_image(image: Image.Image, size: int = PHOTO_HASH_SIZE) -> int:
    """计算轻量感知哈希，用于提示相似照片而不是做严格去重。"""
    grayscale = image.convert("L").resize((size, size), Image.Resampling.LANCZOS)
    pixels = list(grayscale.getdata())
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if pixel >= avg else "0" for pixel in pixels)
    return int(bits, 2)


def extract_captured_at_from_image(image: Image.Image) -> Optional[datetime]:
    try:
        exif = image.getexif()
    except Exception:
        return None

    for key in EXIF_DATETIME_KEYS:
        raw_value = exif.get(key)
        if not raw_value:
            continue
        text = str(raw_value).strip()
        for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    return None


def extract_captured_at(content: bytes) -> Optional[datetime]:
    try:
        with Image.open(io.BytesIO(content)) as image:
            return extract_captured_at_from_image(image)
    except Exception:
        return None


def normalize_image_for_thumbnail(content: bytes) -> tuple[Optional[Image.Image], Optional[datetime]]:
    try:
        image = Image.open(io.BytesIO(content))
        captured_at = extract_captured_at_from_image(image)
        # 手机照片常依赖 EXIF orientation 展示方向，生成缩略图前先转正。
        image = ImageOps.exif_transpose(image)
        if image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")
        elif image.mode != "RGB":
            image = image.convert("RGB")
        return image, captured_at
    except Exception:
        return None, None


def compute_average_hash_from_content(content: bytes) -> Optional[int]:
    image, _ = normalize_image_for_thumbnail(content)
    if image is None:
        return None
    return compute_average_hash_from_image(image)


def load_average_hash_from_path(photo_path: Path) -> Optional[int]:
    if not photo_path.exists():
        return None

    try:
        with Image.open(photo_path) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode in ("RGBA", "P", "LA"):
                image = image.convert("RGB")
            elif image.mode != "RGB":
                image = image.convert("RGB")
            return compute_average_hash_from_image(image)
    except Exception:
        return None


def hamming_distance(left: int, right: int) -> int:
    return bin(left ^ right).count("1")


def save_thumbnail(content: bytes, thumbnail_path: Path) -> Optional[datetime]:
    image, captured_at = normalize_image_for_thumbnail(content)
    if image is None:
        return captured_at

    # 等比缩小即可满足相册预览，原图仍由上传目录保留。
    image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(thumbnail_path, "JPEG", quality=THUMBNAIL_QUALITY, optimize=True)
    return captured_at
