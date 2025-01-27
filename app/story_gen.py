import os
import subprocess
import logging
import json
from datetime import datetime
from textstat import textstat
import re
from config import METADATA_PATH, PROMPT_DIR, PROHIBITED_WORDS, STORIES_DIR

# --------------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# --------------------------------------------------------
# METADATA AND PROMPT LOADING FUNCTIONS
# --------------------------------------------------------

def load_metadata(file_path):
    """Loads metadata (settings, characters, themes) from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def load_prompt(file_path):
    """Loads a text prompt template from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Load prompt templates for different story sections
beginning_prompt_template = load_prompt(os.path.join(PROMPT_DIR, "story_beginning.txt"))
middle_prompt_template = load_prompt(os.path.join(PROMPT_DIR, "story_middle.txt"))
ending_prompt_template = load_prompt(os.path.join(PROMPT_DIR, "story_ending.txt"))

# --------------------------------------------------------
# STORY VALIDATION FUNCTION
# --------------------------------------------------------

def validate_story(text):
    """
    Validates a generated story based on readability, word count, and prohibited words.
    
    - Uses Flesch Reading Ease to ensure readability is child-friendly.
    - Uses Flesch-Kincaid Grade Level to keep the complexity suitable for young readers.
    - Ensures the word count falls within a reasonable range (800–1300 words).
    - Checks for the presence of prohibited words.

    Returns:
        bool: True if the story passes all validation checks, False otherwise.
    """

    # Readability metrics
    flesch_reading_ease = textstat.flesch_reading_ease(text)
    flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
    word_count = len(text.split())

    # Check for prohibited words
    flagged_terms = [word for word in PROHIBITED_WORDS if re.search(word, text, re.IGNORECASE)]

    # Validation criteria
    is_flesch_valid = 75 <= flesch_reading_ease <= 100
    is_grade_valid = 0 <= flesch_kincaid_grade <= 6
    is_word_count_valid = 800 <= word_count <= 1300
    has_no_prohibited_words = not flagged_terms

    # Print validation results for debugging
    print("\nStory Validation Results:")
    print(f"Flesch Reading Ease: {flesch_reading_ease:.2f} (Target: 75–100) - {'✅' if is_flesch_valid else '❌'}")
    print(f"Flesch-Kincaid Grade Level: {flesch_kincaid_grade:.2f} (Target: 0–6) - {'✅' if is_grade_valid else '❌'}")
    print(f"Word Count: {word_count} (Target: 800–1300) - {'✅' if is_word_count_valid else '❌'}")
    
    if flagged_terms:
        print(f"Prohibited Words Check: ❌ (Flagged: {', '.join(flagged_terms)})")
    else:
        print("Prohibited Words Check: ✅")

    # Return True if all conditions are met, False otherwise
    return is_flesch_valid and is_grade_valid and is_word_count_valid and has_no_prohibited_words

# --------------------------------------------------------
# STORY GENERATION FUNCTION (LLM INTERACTION)
# --------------------------------------------------------

def generate_story_section(prompt, model_name="llama3.1"):
    """
    Sends a text prompt to a language model and retrieves a generated response.

    Parameters:
        prompt (str): The input text prompt for the model.
        model_name (str): The name of the AI model used for generation.

    Returns:
        str: The generated text from the model.
    """
    try:
        logging.info(f"Sending prompt to model ({model_name})...")

        # Run the LLM model as a subprocess
        process = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            encoding="utf-8"
        )

        response = process.stdout.strip()

        if response:
            logging.info("Story section successfully generated.")
        else:
            logging.warning("Model returned an empty response. Retrying...")

        return response or ""

    except subprocess.CalledProcessError as e:
        logging.error(f"Model execution failed: {e.stderr}")
        return ""

# --------------------------------------------------------
# FULL STORY GENERATION FUNCTION
# --------------------------------------------------------

def generate_story(setting_key, selected_characters, theme_key):
    """
    Generates a children's story in three sections (beginning, middle, and end).
    
    - Utilizes metadata to structure the story.
    - Calls the LLM model to generate each section.
    - Runs validation to ensure quality.
    - Saves the story parts only if validation passes.

    Parameters:
        setting_key (str): The selected story setting.
        selected_characters (list): List of chosen characters.
        theme_key (str): The selected theme.

    Returns:
        tuple: The full story text and a dictionary of file paths for each section.
    """
    
    # Load metadata from file
    metadata = load_metadata(METADATA_PATH)

    # Extract setting and theme descriptions
    setting_description = metadata["settings"][setting_key]["description"]
    theme_description = metadata["themes"][theme_key]["description"]

    # Extract character descriptions
    character_descriptions = "\n".join(
        [f"{char}: {metadata['characters'][char]['description']}" for char in selected_characters]
    )

    MAX_ATTEMPTS = 5  # Maximum attempts for generating a valid story
    is_valid = False
    attempt = 1

    while not is_valid and attempt <= MAX_ATTEMPTS:
        logging.info(f"Generating story attempt {attempt}...")

        # ---- GENERATE BEGINNING ----
        beginning_prompt = beginning_prompt_template.format(
            setting=setting_key,
            setting_description=setting_description,
            characters=", ".join(selected_characters),
            theme_key=theme_key,
            theme_description=theme_description,
            character_descriptions=character_descriptions
        )
        beginning_response = generate_story_section(beginning_prompt)

        # ---- GENERATE MIDDLE ----
        middle_prompt = middle_prompt_template.format(
            beginning=beginning_response,
            theme=theme_key
        )
        middle_response = generate_story_section(middle_prompt)

        # ---- GENERATE ENDING ----
        ending_prompt = ending_prompt_template.format(
            beginning=beginning_response,
            middle=middle_response,
            theme=theme_key
        )
        end_response = generate_story_section(ending_prompt)

        # Combine the full story
        full_story = f"{beginning_response}\n\n{middle_response}\n\n{end_response}"

        # ---- VALIDATE STORY ----
        is_valid = validate_story(full_story)

        if not is_valid:
            logging.warning("Story validation failed. Regenerating...")
            attempt += 1
            continue  # Skip saving and retry story generation

        # ---- SAVE STORY FILES ----
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        story_folder = STORIES_DIR
        os.makedirs(story_folder, exist_ok=True)

        # Save story parts separately
        beginning_path = os.path.join(story_folder, f"story_{timestamp}_beginning.txt")
        middle_path = os.path.join(story_folder, f"story_{timestamp}_middle.txt")
        ending_path = os.path.join(story_folder, f"story_{timestamp}_end.txt")
        full_story_path = os.path.join(story_folder, f"story_{timestamp}_full.txt")

        # Write each section to its respective file
        for path, content in zip(
            [beginning_path, middle_path, ending_path, full_story_path], 
            [beginning_response, middle_response, end_response, full_story]
        ):
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)

        logging.debug(f"Story parts saved at:\n- {beginning_path}\n- {middle_path}\n- {ending_path}\n- {full_story_path}")

        return full_story, {
            "full_story": full_story_path,
            "beginning": beginning_path,
            "middle": middle_path,
            "ending": ending_path
        }

    return None, None  # Return None if no valid story is generated
