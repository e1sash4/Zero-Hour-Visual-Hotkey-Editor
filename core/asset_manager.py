from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path

from models import MappedImage
from .archive_index import ArchiveIndex


class AssetManager:
    def __init__(self, index: ArchiveIndex, mapped_images: dict[str, MappedImage], cache_dir: str | Path):
        self.index = index
        self.mapped_images = mapped_images
        self._mapped_images_folded = {key.casefold(): value for key, value in mapped_images.items()}
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_icon(self, mapped_image_id: str) -> Path | None:
        mapped = self.mapped_images.get(mapped_image_id) or self._mapped_images_folded.get(mapped_image_id.casefold())
        if not mapped or not mapped.texture or mapped.right <= mapped.left or mapped.bottom <= mapped.top:
            return None
        digest = hashlib.sha1(f"{mapped.id}|{mapped.texture}|{mapped.box}".encode()).hexdigest()[:12]
        target = self.cache_dir / f"{mapped.id}_{digest}.png"
        if target.is_file():
            return target
        try:
            from PIL import Image
            payload = self.index.read(mapped.texture)
            with Image.open(io.BytesIO(payload)) as atlas:
                atlas.load()
                crop = atlas.crop(mapped.box).convert("RGBA")
                temp = target.with_suffix(".tmp")
                crop.save(temp, format="PNG")
                temp.replace(target)
            return target
        except Exception as exc:
            logging.getLogger(__name__).warning("Icon %s could not be extracted: %s", mapped_image_id, exc)
            return None
