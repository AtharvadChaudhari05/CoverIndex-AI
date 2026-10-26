from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from collections import OrderedDict
from threading import Lock

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
# Sarvam accepts at most 2500 characters per request; the client sends sentence-aligned chunks below this.
MAX_TTS_CHARS = 2500
TTS_LANGUAGES = {"en-IN", "hi-IN", "mr-IN", "ta-IN", "te-IN", "bn-IN"}

_CACHE_SIZE = 64
_cache: OrderedDict[str, bytes] = OrderedDict()
_cache_lock = Lock()


class TTSError(Exception):
    pass


def tts_available() -> bool:
    return bool(os.getenv("SARVAM_API_KEY"))


def synthesize_speech(text: str, language: str) -> bytes:
    """Returns MP3 audio for text, spoken in language (a BCP-47 code from TTS_LANGUAGES).
    Replays of the same text are served from an in-memory cache, so they cost nothing."""
    model = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
    speaker = os.getenv("SARVAM_TTS_SPEAKER", "priya")
    cache_key = hashlib.sha1(f"{model}|{speaker}|{language}|{text}".encode("utf-8")).hexdigest()

    with _cache_lock:
        if cache_key in _cache:
            _cache.move_to_end(cache_key)
            return _cache[cache_key]

    body = json.dumps(
        {
            "text": text,
            "target_language_code": language,
            "model": model,
            "speaker": speaker,
            "output_audio_codec": "mp3",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        SARVAM_TTS_URL,
        data=body,
        headers={"api-subscription-key": os.getenv("SARVAM_API_KEY", ""), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:300].decode("utf-8", errors="ignore")
        raise TTSError(f"Sarvam TTS returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise TTSError(f"Sarvam TTS request failed: {exc}") from exc

    audios = payload.get("audios") or []
    if not audios:
        raise TTSError("Sarvam TTS returned no audio")
    audio = base64.b64decode(audios[0])

    with _cache_lock:
        _cache[cache_key] = audio
        if len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
    return audio
