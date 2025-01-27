import os
import requests
import logging
import librosa
import time
import numpy as np
from datetime import datetime
from config import NARRATIONS_DIR

# --------------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# --------------------------------------------------------
# AUDIO VALIDATION FUNCTION
# --------------------------------------------------------

def validate_audio(file_path):
    """
    Validates the generated TTS narration using librosa.
    
    Checks the following criteria:
    - **RMS Loudness**: Ensures the audio isn't too quiet.
    - **Sample Rate**: Confirms correct audio sampling rate (44100 Hz).
    - **Duration**: Ensures the narration is at least 10 seconds long.

    Parameters:
        file_path (str): Path to the generated narration audio file.

    Returns:
        bool: True if the audio passes all validation checks, False otherwise.
    """
    try:
        # Load audio file
        y, sr = librosa.load(file_path, sr=None)
        rms = np.sqrt(np.mean(y**2))  # Root Mean Square (RMS) loudness
        duration = librosa.get_duration(y=y, sr=sr)

        # Validation thresholds
        EXPECTED_SR = 44100  # Expected sample rate (CD quality)
        MIN_RMS = 0.02  # Minimum acceptable loudness
        MIN_DURATION = 10.0  # Minimum acceptable duration (10 seconds)

        is_rms_valid = rms >= MIN_RMS
        is_sample_rate_valid = sr == EXPECTED_SR
        is_duration_valid = duration >= MIN_DURATION

        # Logging validation results
        logging.info(f"Validating audio: {file_path}")
        logging.info(f"RMS: {rms:.4f} (Target: >{MIN_RMS}) - {'✅' if is_rms_valid else '❌'}")
        logging.info(f"Duration: {duration:.2f} sec (Target: >={MIN_DURATION}) - {'✅' if is_duration_valid else '❌'}")
        logging.info(f"Sample Rate: {sr} Hz (Expected: {EXPECTED_SR}) - {'✅' if is_sample_rate_valid else '❌'}")

        return is_rms_valid and is_duration_valid and is_sample_rate_valid

    except Exception as e:
        logging.error(f"Error validating audio {file_path}: {e}")
        return False

# --------------------------------------------------------
# TEXT-TO-SPEECH (TTS) GENERATION FUNCTION
# --------------------------------------------------------

def generate_narration(text_files, output_folder=NARRATIONS_DIR):
    """
    Converts a list of text files into TTS-generated narration audio files.
    
    - Sends text content to a local TTS service (MeloTTS) via an API request.
    - Saves the generated audio files in the specified output folder.
    - Validates each audio file before finalizing the output list.

    Parameters:
        text_files (list): List of file paths containing the story text.
        output_folder (str): Directory to save the generated narration files.

    Returns:
        list: A list of valid narration file paths.
    """
    
    logging.info("Starting TTS narration generation...")
    narration_paths = []

    try:
        # Ensure output directory exists
        os.makedirs(output_folder, exist_ok=True)

        for i, text_file in enumerate(text_files):
            # Generate a unique timestamped filename for each narration part
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_folder, f"narration_part_{i+1}_{timestamp}.wav")

            # Read text from file
            with open(text_file, "r", encoding="utf-8") as file:
                text = file.read()
            logging.debug(f"Processing TTS for: {text_file} (Length: {len(text)} chars)")

            # Define TTS API request parameters
            url = "http://localhost:8888/convert/tts"  # Local TTS API endpoint
            headers = {"Content-Type": "application/json"}
            data = {"text": text}

            # Attempt to request TTS conversion
            MAX_TTS_ATTEMPTS = 3
            for attempt in range(MAX_TTS_ATTEMPTS):
                try:
                    logging.info(f"TTS request attempt {attempt+1} / {MAX_TTS_ATTEMPTS}")
                    response = requests.post(url, headers=headers, json=data)

                    if response.status_code == 200:
                        # Successful response, exit retry loop
                        break
                except requests.exceptions.RequestException:
                    # Log failure and retry after a short delay
                    if attempt < MAX_TTS_ATTEMPTS - 1:
                        logging.warning("TTS request failed. Retrying...")
                        time.sleep(2)
            else:
                # If all attempts fail, skip this text file
                logging.error("TTS request failed after max attempts.")
                continue

            # Save the TTS-generated audio file
            with open(output_file, "wb") as file:
                file.write(response.content)
            logging.debug(f"Narration saved: {output_file}")

            # Validate the generated audio file before adding it to the final list
            if validate_audio(output_file):
                narration_paths.append(output_file)
            else:
                logging.warning(f"Invalid audio file detected: {output_file}, skipping.")

        return narration_paths

    except Exception as e:
        logging.error(f"Unexpected error in TTS generation: {e}")
        return []
