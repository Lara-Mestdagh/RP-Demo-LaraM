import os
import logging
import numpy as np
from datetime import datetime
import scipy.io.wavfile as wavfile
from config import FINAL_AUDIO_DIR
import librosa
import soundfile as sf

# --------------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# Ensure the output directory exists before attempting to save files
os.makedirs(FINAL_AUDIO_DIR, exist_ok=True)

# --------------------------------------------------------
# AUDIO LOADING FUNCTION
# --------------------------------------------------------

def load_wav_as_float32(file_path, target_sample_rate=None):
    """
    Loads a WAV file as a float32 NumPy array in the range [-1.0, 1.0].
    
    - If `target_sample_rate` is provided and different from the file's sample rate, 
      the function resamples the audio.
    - If the file is missing or fails to load, returns a float32 array of zeros 
      (acts as silence).

    Parameters:
        file_path (str): Path to the WAV file.
        target_sample_rate (int, optional): Target sample rate for resampling.

    Returns:
        tuple: (sample rate, NumPy array of audio samples)
    """

    # Duration of fallback silence (in seconds) if file is missing
    FALLBACK_DURATION = 3  

    if not os.path.exists(file_path):
        logging.error(f"Missing file: {file_path}. Using {FALLBACK_DURATION}s silence instead.")
        num_samples = int(FALLBACK_DURATION * target_sample_rate) if target_sample_rate else 0
        return target_sample_rate, np.zeros(num_samples, dtype=np.float32)

    try:
        # Load audio using librosa (ensures float32 format and mono-channel)
        y, sr = librosa.load(file_path, sr=None, mono=True)
        logging.info(f"Loaded {file_path} (Original SR: {sr}, Shape: {y.shape})")

        # Resample if needed
        if target_sample_rate and sr != target_sample_rate:
            logging.warning(f"Resampling {file_path} from {sr} Hz to {target_sample_rate} Hz.")
            y = librosa.resample(y, orig_sr=sr, target_sr=target_sample_rate)
            sr = target_sample_rate

        return sr, y.astype(np.float32)

    except Exception as e:
        logging.error(f"Error reading WAV file {file_path}: {e}")
        num_samples = int(FALLBACK_DURATION * target_sample_rate) if target_sample_rate else 0
        return target_sample_rate, np.zeros(num_samples, dtype=np.float32)

# --------------------------------------------------------
# AUDIO COMBINATION FUNCTION
# --------------------------------------------------------

def combine_audio(narration_paths, music_paths):
    """
    Combines narration and background music into a single audio track.
    
    - Ensures all audio files have a consistent sample rate.
    - Adds short silence between sections for better audio flow.
    - Normalizes the final mix to prevent audio clipping.
    - Saves the final combined audio as a WAV file.

    Parameters:
        narration_paths (list): List of file paths for the narration audio.
        music_paths (dict): Dictionary of file paths for background music.

    Returns:
        str: Path to the final combined audio file.
    """

    logging.info("Starting final audio merging process...")

    try:
        # 1) Determine the target sample rate using the first narration file
        sr, _ = load_wav_as_float32(narration_paths[0], None)
        logging.info(f"Using {sr} Hz as target sample rate for merging.")

        # 2) Load all narration and music files as float32, resampling if necessary
        _, narration_beginning = load_wav_as_float32(narration_paths[0], sr)
        _, narration_middle = load_wav_as_float32(narration_paths[1], sr)
        _, narration_end = load_wav_as_float32(narration_paths[2], sr)

        _, music_beginning = load_wav_as_float32(music_paths["beginning"], sr)
        _, music_transition1 = load_wav_as_float32(music_paths["transition1"], sr)
        _, music_transition2 = load_wav_as_float32(music_paths["transition2"], sr)
        _, music_ending = load_wav_as_float32(music_paths["ending"], sr)

        # 3) Generate half-second silence for spacing between sections
        silence_duration = int(sr * 0.5)  # 0.5 seconds of silence
        silence = np.zeros(silence_duration, dtype=np.float32)

        # 4) Concatenate narration and music sections with silence in between
        combined_audio_float = np.concatenate([
            silence, 
            music_beginning, silence,
            narration_beginning, silence,
            music_transition1, silence,
            narration_middle, silence,
            music_transition2, silence,
            narration_end, silence,
            music_ending, silence
        ], dtype=np.float32)

        # 5) Normalize the final mix to prevent clipping
        max_abs_value = np.max(np.abs(combined_audio_float))
        if max_abs_value > 1.0:
            logging.info(f"Normalizing audio to avoid clipping. Peak before: {max_abs_value:.2f}")
            combined_audio_float /= max_abs_value
        else:
            logging.info(f"No normalization needed. Peak amplitude: {max_abs_value:.2f}")

        # 6) Convert float32 to int16 for WAV saving (scaling from [-1,1] to [-32767, 32767])
        combined_audio_int16 = (combined_audio_float * 32767).astype(np.int16)

        # 7) Save the final combined audio file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_audio_path = os.path.join(FINAL_AUDIO_DIR, f"final_story_audio_{timestamp}.wav")
        wavfile.write(final_audio_path, sr, combined_audio_int16)

        duration_seconds = len(combined_audio_float) / sr
        logging.info(f"Final combined audio saved at: {final_audio_path} (Duration: {duration_seconds:.2f}s)")

        return final_audio_path

    except Exception as e:
        logging.error(f"Error while combining audio: {e}")
        return None
