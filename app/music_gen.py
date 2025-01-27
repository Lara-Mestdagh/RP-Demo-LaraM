import os
import torch
import logging
import librosa
import numpy as np
import time
import scipy.io.wavfile as wavfile
from transformers import AutoProcessor, MusicgenForConditionalGeneration
from datetime import datetime
from config import MUSIC_DIR, PROMPT_DIR, INSTRUMENTS_BY_SETTING

# --------------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# --------------------------------------------------------
# LOAD MUSICGEN MODEL
# --------------------------------------------------------

# Load the MusicGen processor and model for conditional music generation
processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small", attn_implementation="eager")

# --------------------------------------------------------
# LOAD MUSIC PROMPT TEMPLATES
# --------------------------------------------------------

def load_prompt(file_path):
    """Loads a text prompt template from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Load predefined music prompt templates for different parts of the story
PROMPTS = {
    "beginning": load_prompt(os.path.join(PROMPT_DIR, "music_beginning.txt")),
    "transition1": load_prompt(os.path.join(PROMPT_DIR, "music_transition1.txt")),
    "transition2": load_prompt(os.path.join(PROMPT_DIR, "music_transition2.txt")),
    "ending": load_prompt(os.path.join(PROMPT_DIR, "music_ending.txt")),
}

# --------------------------------------------------------
# MUSIC VALIDATION SETTINGS
# --------------------------------------------------------

EXPECTED_SR = 32000  # Expected sample rate (32kHz)
MIN_AMPLITUDE = 0.2  # Minimum amplitude to ensure the generated music isn't silent

# --------------------------------------------------------
# MUSIC VALIDATION FUNCTION
# --------------------------------------------------------

def validate_music_clip(file_path):
    """
    Validates the generated music clip using librosa.
    
    Checks the following criteria:
    - **Peak Amplitude**: Ensures the music is not too quiet.
    - **Sample Rate**: Confirms the generated audio is at the expected 32 kHz.

    Parameters:
        file_path (str): Path to the generated music file.

    Returns:
        bool: True if the music clip meets all validation criteria, False otherwise.
    """
    try:
        # Load the audio file
        y, sr = librosa.load(file_path, sr=None)
        amplitude = np.max(np.abs(y))  # Peak amplitude (absolute max)

        is_amplitude_valid = amplitude > MIN_AMPLITUDE
        is_sample_rate_valid = sr == EXPECTED_SR

        # Logging validation results
        logging.info(f"Validating music clip: {file_path}")
        logging.info(f"Peak Amplitude: {amplitude:.4f} (Target: >{MIN_AMPLITUDE}) - "
                     f"{'✅' if is_amplitude_valid else '❌'}")
        logging.info(f"Sample Rate: {sr} Hz (Expected: {EXPECTED_SR}) - "
                     f"{'✅' if is_sample_rate_valid else '❌'}")

        return is_amplitude_valid and is_sample_rate_valid

    except Exception as e:
        logging.error(f"Error validating music clip {file_path}: {e}")
        return False

# --------------------------------------------------------
# MUSIC GENERATION FUNCTION
# --------------------------------------------------------

def generate_music(setting_key, setting_description):
    """
    Generates instrumental music clips at 32 kHz based on the story setting.
    
    - Selects appropriate instruments for the setting.
    - Uses the MusicGen model to generate different sections of the background music.
    - Saves and validates the generated music clips.

    Parameters:
        setting_key (str): The selected story setting.
        setting_description (str): A description of the setting for better music generation.

    Returns:
        dict: A dictionary containing file paths to the generated music clips.
    """
    
    logging.info(f"Starting music generation for {setting_key} ({setting_description})")

    # Select instruments based on the story setting; default to soft piano and strings if unspecified
    instruments = INSTRUMENTS_BY_SETTING.get(setting_key, ["soft piano", "harp", "strings"])
    logging.info(f"Instrumentation: {instruments}")

    # Ensure the output directory exists
    os.makedirs(MUSIC_DIR, exist_ok=True)
    
    # Generate a timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Join instrument names into a single string for the prompt
    instruments_str = ", ".join(instruments)

    # Dictionary to store file paths of successfully generated music clips
    music_clips = {}

    # Maximum attempts for music generation
    MAX_MUSIC_ATTEMPTS = 3

    # Generate music clips for each section (beginning, transitions, ending)
    for key, prompt_template in PROMPTS.items():
        for attempt in range(MAX_MUSIC_ATTEMPTS):
            try:
                # Format the prompt using story metadata
                prompt_text = prompt_template.format(
                    setting=setting_key,
                    setting_description=setting_description,
                    instruments=instruments_str
                )
                logging.info(f"Attempt {attempt+1} / {MAX_MUSIC_ATTEMPTS} for {key} music.")

                # Prepare inputs for the MusicGen model
                inputs = processor(text=[prompt_text], padding=True, return_tensors="pt")

                # Generate audio using the MusicGen model
                with torch.no_grad():
                    audio_values = model.generate(
                        **inputs,
                        do_sample=True,  # Enable sampling for variability
                        guidance_scale=3,  # Controls how closely output follows the prompt
                        max_new_tokens=100  # Limits the length of generated audio
                    )

                # Convert audio tensor to NumPy array
                audio_array = audio_values.cpu().numpy().astype(np.float32)

                # Define the file path for the generated music
                music_path = os.path.join(MUSIC_DIR, f"music_{key}_{timestamp}.wav")

                # Save the generated music as a WAV file with a 32 kHz sample rate
                wavfile.write(music_path, EXPECTED_SR, audio_array)

                # Validate the generated music clip before adding it to the output list
                if validate_music_clip(music_path):
                    music_clips[key] = music_path
                    logging.info(f"✅ Music validation passed for {key}.")
                    break  # Exit retry loop on success
                else:
                    logging.warning(f"❌ Music validation failed for {key}, retrying...")

            except Exception as e:
                logging.error(f"Error generating {key} music: {e}")
                if attempt < MAX_MUSIC_ATTEMPTS - 1:
                    logging.info("Retrying music generation after a short delay...")
                    time.sleep(2)  # Short delay before retrying

        else:
            # If all attempts fail, log the failure and store None
            logging.error(f"Music generation failed after max attempts for {key}.")
            music_clips[key] = None

    return music_clips