import logging
import os
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class STTService:
    """
    Speech-to-Text service using Whisper.
    Provides word-level and sentence-level timestamps.
    """

    def __init__(self):
        self._available = None
        self._model = None
        self._model_size = "base"

    def is_available(self) -> bool:
        """Check if Whisper is available."""
        if self._available is not None:
            return self._available

        try:
            import whisper
            self._available = True
            logger.info("Whisper STT available")
            return True
        except ImportError:
            logger.warning("Whisper not installed. Install: pip install openai-whisper")
            self._available = False
            return False

    def _load_model(self):
        """Load appropriate Whisper model based on resources."""
        if self._model is not None:
            return self._model

        import whisper

        try:
            import torch
            if torch.cuda.is_available():
                vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                if vram >= 10:
                    self._model_size = "medium"
                elif vram >= 5:
                    self._model_size = "small"
                else:
                    self._model_size = "base"
        except Exception:
            self._model_size = "base"

        logger.info(f"Loading Whisper model: {self._model_size}")
        self._model = whisper.load_model(self._model_size)
        return self._model

    def transcribe(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        """Full transcription with timestamps."""
        if not self.is_available():
            raise RuntimeError("⚠️ Whisper not available. Install: pip install openai-whisper")

        model = self._load_model()
        result = model.transcribe(audio_path, language=language, word_timestamps=True)
        return result

    def get_word_timestamps(self, audio_path: str, language: str = "en") -> List[Dict[str, Any]]:
        """Get precise word-level timestamps."""
        result = self.transcribe(audio_path, language)
        words = []
        for segment in result.get("segments", []):
            for word in segment.get("words", []):
                words.append({
                    "word": word.get("word", "").strip(),
                    "start": round(word.get("start", 0), 3),
                    "end": round(word.get("end", 0), 3),
                    "confidence": round(word.get("probability", 0), 3)
                })
        return words

    def get_sentence_timestamps(self, audio_path: str, language: str = "en") -> List[Dict[str, Any]]:
        """Get sentence/segment-level timestamps."""
        result = self.transcribe(audio_path, language)
        return [
            {
                "text": s.get("text", "").strip(),
                "start": round(s.get("start", 0), 3),
                "end": round(s.get("end", 0), 3)
            }
            for s in result.get("segments", [])
        ]

    def generate_srt(self, audio_path: str, output_path: str, language: str = "en") -> str:
        """Generate SRT subtitle file."""
        words = self.get_word_timestamps(audio_path, language)
        if not words:
            raise RuntimeError("No words detected in audio")

        lines = []
        current = []
        line_start = 0

        for i, w in enumerate(words):
            if not current:
                line_start = w["start"]
            current.append(w)

            if len(current) >= 8 or w["word"].endswith((".", "!", "?")) or i == len(words) - 1:
                lines.append({
                    "text": " ".join(x["word"] for x in current),
                    "start": line_start,
                    "end": w["end"]
                })
                current = []

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for i, line in enumerate(lines, 1):
                def fmt(s):
                    h = int(s // 3600)
                    m = int((s % 3600) // 60)
                    sec = int(s % 60)
                    ms = int((s % 1) * 1000)
                    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

                f.write(f"{i}\n{fmt(line['start'])} --> {fmt(line['end'])}\n{line['text']}\n\n")

        logger.info(f"SRT generated: {output_path} ({len(lines)} lines)")
        return output_path

    def generate_vtt(self, audio_path: str, output_path: str, language: str = "en") -> str:
        """Generate VTT subtitle file."""
        srt_path = self.generate_srt(audio_path, output_path + ".tmp.srt", language)
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        vtt = "WEBVTT\n\n" + content.replace(",", ".")
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(vtt)
        os.remove(srt_path)
        return output_path
