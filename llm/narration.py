"""
Chronicle narration via TTS.

Local: tries the installed voxcpm package (openbmb/VoxCPM2 from HF Hub) first;
       falls back to gTTS when the model or GPU is unavailable.
HF Space: same code path — `VoxCPM.from_pretrained("openbmb/VoxCPM2")` loads
          directly from https://huggingface.co/openbmb/VoxCPM2 at runtime.
"""

import logging
import os
from pathlib import Path

# True when running inside a Hugging Face Space
_IS_HF_SPACE = bool(os.environ.get("SPACE_ID"))

logger = logging.getLogger(__name__)

# Use absolute path so Gradio's /file= endpoint can serve these files reliably
AUDIO_CACHE_DIR = Path(__file__).parent.parent / "audio_cache"
AUDIO_CACHE_DIR.mkdir(exist_ok=True)

NARRATOR_VOICE_DESCRIPTION = (
    "(A calm, even-toned automated archive system, slightly formal, "
    "unhurried pace, no emotional inflection)"
)

_voxcpm_model = None
_first_narration_path: Path | None = None


def _get_voxcpm_model():
    """Lazy-load VoxCPM2. Loaded once, reused across calls.

    Both locally and on HF Space, the model is fetched from
    https://huggingface.co/openbmb/VoxCPM2 via `from_pretrained`.
    """
    global _voxcpm_model
    if _voxcpm_model is None:
        from voxcpm import VoxCPM

        env_label = "HF Space" if _IS_HF_SPACE else "local"
        logger.info("Loading VoxCPM2 (openbmb/VoxCPM2) in %s environment...", env_label)
        _voxcpm_model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
        logger.info("VoxCPM2 loaded.")
    return _voxcpm_model


def _narrate_with_voxcpm(text: str, cache_path: Path) -> bool:
    """Try VoxCPM2 TTS. Returns True on success."""
    global _first_narration_path
    try:
        import soundfile as sf

        model = _get_voxcpm_model()

        if _first_narration_path and _first_narration_path.exists():
            wav = model.generate(
                text=text,
                reference_wav_path=str(_first_narration_path),
                cfg_value=2.0,
                inference_timesteps=10,
            )
        else:
            prompt_text = f"{NARRATOR_VOICE_DESCRIPTION}{text}"
            wav = model.generate(
                text=prompt_text,
                cfg_value=2.0,
                inference_timesteps=10,
            )

        if wav is None or len(wav) == 0:
            return False

        sf.write(str(cache_path), wav, model.tts_model.sample_rate)

        if _first_narration_path is None:
            _first_narration_path = cache_path
        return True

    except Exception as e:
        logger.debug(f"VoxCPM2 unavailable: {e}")
        return False


def _narrate_with_gtts(text: str, cache_path: Path) -> bool:
    """Fallback TTS using gTTS (Google Text-to-Speech). Returns True on success."""
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(cache_path))
        return True

    except Exception as e:
        logger.debug(f"gTTS fallback failed: {e}")
        return False


def narrate_chronicle(text: str, cache_key: str) -> str | None:
    """
    Generate spoken narration for a Chronicle entry.
    Tries VoxCPM2 first, then gTTS as fallback.

    Args:
        text: The Chronicle text to narrate.
        cache_key: Unique key for caching, e.g. "year_3" or "milestone_death_001".

    Returns:
        Path to the generated audio file, or None if all TTS methods failed.
    """
    # Check cache (wav = VoxCPM2, mp3 = gTTS)
    for ext in (".wav", ".mp3"):
        cached = AUDIO_CACHE_DIR / f"{cache_key}{ext}"
        if cached.exists():
            return str(cached)

    # Try VoxCPM2 first (WAV)
    wav_path = AUDIO_CACHE_DIR / f"{cache_key}.wav"
    if _narrate_with_voxcpm(text, wav_path):
        return str(wav_path)

    # Fallback to gTTS (MP3)
    mp3_path = AUDIO_CACHE_DIR / f"{cache_key}.mp3"
    if _narrate_with_gtts(text, mp3_path):
        logger.info(f"gTTS narration saved: {mp3_path}")
        return str(mp3_path)

    logger.warning(
        f"Chronicle narration failed for {cache_key}: all TTS methods unavailable"
    )
    return None
