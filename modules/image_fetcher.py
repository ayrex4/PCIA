import io
import re
import urllib.request
from pathlib import Path
from PIL import Image
from duckduckgo_search import DDGS
from utils.logger import get_logger

logger = get_logger("ImageFetcher")

class ImageFetcher:
    def __init__(self, download_dir="data/downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _safe_stem(self, text):
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", text.strip().lower())
        cleaned = cleaned.strip("_")
        return cleaned[:50] if cleaned else "image"

    def _download_bytes(self, url):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            data = resp.read()
        return content_type, data

    def download_best_image(self, query, min_width=800, min_height=600):
        """Downloads the best high-resolution image using DuckDuckGo."""
        logger.info(f"Searching DDG for high-quality image: {query}")
        
        try:
            # 🔥 FIX: Using DDG Image Search instead of messy Bing HTML
            results = DDGS().images(query, max_results=15)
        except Exception as e:
            logger.error(f"DDGS Image search failed: {e}")
            return None

        if not results:
            logger.warning("No image candidates found.")
            return None

        stem = self._safe_stem(query)
        best_fallback = None
        largest_area = 0

        for idx, res in enumerate(results):
            candidate_url = res.get('image')
            if not candidate_url: continue
            
            try:
                logger.debug(f"Attempting download: {candidate_url}")
                content_type, raw_data = self._download_bytes(candidate_url)
                if "image" not in content_type and not raw_data:
                    continue

                image = Image.open(io.BytesIO(raw_data))
                width, height = image.size
                area = width * height

                fmt = (image.format or "JPEG").upper()
                ext = "jpg" if fmt == "JPEG" else fmt.lower()
                out_path = self.download_dir / f"{stem}_{idx}.{ext}"

                result_data = {
                    "path": str(out_path.resolve()),
                    "width": width,
                    "height": height,
                    "source_url": candidate_url,
                }

                # 1. Strict Check
                if width >= min_width and height >= min_height:
                    image.convert("RGB").save(out_path, format="JPEG" if ext == "jpg" else fmt)
                    logger.info(f"Downloaded perfect image: {result_data['path']} ({width}x{height})")
                    return result_data
                
                # 2. Fallback Check (Keep largest just in case)
                if area > largest_area:
                    largest_area = area
                    best_fallback = (image, result_data, out_path, ext, fmt)

            except Exception as e:
                logger.debug(f"Failed to process {candidate_url}: {e}")
                continue

        # 3. Fallback to largest found if strict resolution not met
        if best_fallback:
            image, result_data, out_path, ext, fmt = best_fallback
            image.convert("RGB").save(out_path, format="JPEG" if ext == "jpg" else fmt)
            logger.warning(f"Fell back to largest found: {result_data['path']} ({result_data['width']}x{result_data['height']})")
            return result_data

        logger.warning("All candidates failed to download.")
        return None