import os
import webvtt

from app.extractors.base import BaseExtractor, ExtractedUnit


def _to_seconds(ts: str) -> float:
    # webvtt timestamps look like "00:01:23.456" or "01:23.456"
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


class VttExtractor(BaseExtractor):
    """One ExtractedUnit per cue -> exact 'jump to chunk' + highlight."""

    async def extract(self, source) -> list[ExtractedUnit]:
        if not source.file_path or not os.path.exists(source.file_path):
            raise FileNotFoundError(f"VTT file not found: {source.file_path}")
        units: list[ExtractedUnit] = []
        for caption in webvtt.read(source.file_path):
            text = caption.text.strip()
            if not text:
                continue
            units.append(
                ExtractedUnit(
                    text=text,
                    timestamp_start=_to_seconds(caption.start),
                    timestamp_end=_to_seconds(caption.end),
                )
            )
        return units