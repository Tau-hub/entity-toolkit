"""Local OCR with the OCR engine built into Windows (nothing to install, no network).

It uses the languages of your Windows profile: the game's text is read in English, so an English language pack
must be installed (Settings > Time & language > Language & region).
"""
import asyncio
import io

from PIL import Image
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream


async def _ocr(img, words=False):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    stream = InMemoryRandomAccessStream()
    w = DataWriter(stream)
    w.write_bytes(buf.getvalue())
    await w.store_async()
    stream.seek(0)
    bmp = await (await BitmapDecoder.create_async(stream)).get_software_bitmap_async()
    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise RuntimeError("Windows OCR is unavailable: install an English language pack (Settings > Time & language).")
    res = await engine.recognize_async(bmp)
    if words:
        return [[(w.text, w.bounding_rect.x, w.bounding_rect.y, w.bounding_rect.width, w.bounding_rect.height) for w in ln.words] for ln in res.lines]
    return [ln.text for ln in res.lines]


def read_lines(img):
    """Text lines recognised in a PIL image (enlarged 2x for small fonts)."""
    img = img.convert("RGB")
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    return asyncio.run(_ocr(img))


def read_words(img, zoom=3):
    """Words with their box (x, y, width, height) in the original image's pixels: lets callers tell font sizes apart."""
    img = img.convert("RGB").resize((img.width * zoom, img.height * zoom), Image.LANCZOS)
    return [[(t, x / zoom, y / zoom, w / zoom, h / zoom) for t, x, y, w, h in ln] for ln in asyncio.run(_ocr(img, True))]
