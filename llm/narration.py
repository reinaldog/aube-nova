"""
Chronicle narration via VoxCPM2 (OpenBMB).
Converts Chronicle text entries to spoken audio using a consistent
"archive computer" narrator voice via Voice Design.

Falls back gracefully if VoxCPM2 is unavailable (CPU-only environments).
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

AUDIO_CACHE_DIR = Path("audio_cache")
AUDIO_CACHE_DIR.mkdir(exist_ok=True)

NARRATOR_VOICE_DESCRIPTION = (
    "(A calm, even-toned automated archive system, slightly formal, "
    "unhurried pace, no emotional inflection)"
)

_model = None
_first_narration_path: Path | None = None


def _get_model():
    """Lazy-load VoxCPM2. Loaded once, reused across calls."""
    global _model
    if _model is None:
        from voxcpm import VoxCPM

        logger.info("Loading VoxCPM2...")
        _model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
        logger.info("VoxCPM2 loaded.")
    return _model


def narrate_chronicle(text: str, cache_key: str) -> str | None:
    """
    Generate spoken narration for a Chronicle entry.

    Args:
        text: The Chronicle text to narrate.
        cache_key: Unique identifier for caching, e.g. "year_3" or "milestone_death_001".

    Returns:
        Path to the generated .wav file, or None if generation failed.
    """
    global _first_narration_path

    cache_path = AUDIO_CACHE_DIR / f"{cache_key}.wav"
    if cache_path.exists():
        return str(cache_path)

    try:
        import soundfile as sf

        model = _get_model()

        # Use voice cloning from first narration for consistency; fall back to Voice Design
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
            logger.warning(f"VoxCPM2 returned empty audio for {cache_key}")
            return None

        sf.write(str(cache_path), wav, model.tts_model.sample_rate)

        # Lock in the voice after first successful generation
        if _first_narration_path is None:
            _first_narration_path = cache_path

        return str(cache_path)

    except Exception as e:
        logger.warning(f"Chronicle narration failed for {cache_key}: {e}")
        return None
