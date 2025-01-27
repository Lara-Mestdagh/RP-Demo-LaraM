import gradio as gr
import json
import logging
from config import METADATA_PATH, LICENSE_LLAMA, LICENSE_MELO, LICENSE_MUSIC
from story_gen import generate_story
from tts_gen import generate_narration
from music_gen import generate_music
from combine_audio import combine_audio

# --------------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s] - [%(levelname)s] - %(message)s",
)

# --------------------------------------------------------
# LOAD METADATA FROM JSON FILE
# --------------------------------------------------------

def load_metadata(file_path):
    """Loads metadata (settings, characters, themes) from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

metadata = load_metadata(METADATA_PATH)

# Extract settings, characters, and themes from metadata
settings = metadata["settings"]
characters = metadata["characters"]
themes = metadata["themes"]

# --------------------------------------------------------
# UTILITY FUNCTIONS FOR FORMATTING UI CHOICES
# --------------------------------------------------------

def format_choices(data):
    """
    Formats choices with corresponding emojis for better UI presentation.
    Returns a dictionary where:
    - Key: 'name + emoji'
    - Value: 'original name' (used for internal processing)
    """
    return {f"{name} {data[name]['icon']}": name for name in data}

formatted_settings = format_choices(settings)
formatted_themes = format_choices(themes)

def get_characters(setting_key):
    """
    Retrieves compatible characters for a selected setting, formatted with emojis.
    - Returns a dictionary mapping 'name + emoji' to the original name.
    """
    if setting_key:
        return {f"{char} {characters[char]['icon']}": char for char in settings[setting_key]["compatible_characters"]}
    return {}

# --------------------------------------------------------
# FULL PIPELINE: STORY, NARRATION, MUSIC, AUDIO COMBINATION
# --------------------------------------------------------

def full_pipeline(setting_key, selected_characters, theme_key):
    """
    Runs the full pipeline to generate a narrated children's story with background music.
    Steps:
    1. Converts UI selections back to internal metadata keys.
    2. Validates user input.
    3. Generates a story based on the selected setting, characters, and theme.
    4. Creates a narrated audio version of the story.
    5. Generates background music.
    6. Merges narration and music into a final audio output.
    7. Returns the story text and the audio file path.
    """
    
    # Convert UI-selected formatted keys back to original metadata keys
    setting_key = formatted_settings.get(setting_key, setting_key)
    theme_key = formatted_themes.get(theme_key, theme_key)

    # Convert selected characters back to original names
    character_mapping = {f"{name} {characters[name]['icon']}": name for name in characters}
    selected_characters = [character_mapping.get(char, char) for char in selected_characters]

    # Input validation
    if not setting_key:
        raise gr.Error("⚠️ Please select a setting.")
    if not selected_characters:
        raise gr.Error("⚠️ Please select at least one character.")
    if not theme_key:
        raise gr.Error("⚠️ Please select a theme.")

    logging.info(f"Generating story for Setting: {setting_key}, Characters: {selected_characters}, Theme: {theme_key}")

    # ---- STORY GENERATION ----
    story, story_paths = generate_story(setting_key, selected_characters, theme_key)
    if not story:
        raise gr.Error("❌ Story generation failed.")

    # ---- NARRATION GENERATION ----
    narration_paths = generate_narration([
        story_paths["beginning"], 
        story_paths["middle"], 
        story_paths["ending"]
    ])
    if not narration_paths:
        raise gr.Error("❌ Narration generation failed.")

    # ---- MUSIC GENERATION ----
    setting_description = settings[setting_key]["description"]
    music_paths = generate_music(setting_key, setting_description)
    if not music_paths:
        raise gr.Error("❌ Music generation failed.")

    # ---- COMBINE AUDIO (Narration + Music) ----
    full_audio_path = combine_audio(narration_paths, music_paths)
    if not full_audio_path:
        raise gr.Error("❌ Failed to merge final audio.")

    return story, full_audio_path

# --------------------------------------------------------
# GRADIO UI: USER INPUTS, OUTPUTS, AND INTERACTIVITY
# --------------------------------------------------------

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    # UI Header
    gr.Markdown("# 🎭 AI Storyteller Demo - Lara Mestdagh")
    gr.Markdown("## Choose a setting, up to 3 characters, and a theme to generate a children's story.")
    gr.Markdown("### Powered by Llama 3.1, MeloTTS, and MusicGen")

    # Input fields
    setting_dropdown = gr.Dropdown(choices=list(formatted_settings.keys()), label="Choose a Setting")
    character_dropdown = gr.Dropdown(choices=[], multiselect=True, max_choices=3, label="Select up to 3 Characters")
    theme_dropdown = gr.Radio(choices=list(formatted_themes.keys()), label="Choose a Theme")

    # Generate Button
    generate_button = gr.Button("Create your custom story!")

    # Output fields
    final_audio_output = gr.Audio(label="Complete Story Narration with Music", type="filepath")
    story_output = gr.Textbox(label="Generated Story", lines=10)

    # --------------------------------------------------------
    # UPDATE CHARACTER OPTIONS WHEN SETTING CHANGES
    # --------------------------------------------------------

    def update_characters(setting_key):
        """
        Updates the character dropdown based on the selected setting.
        Converts emoji-formatted setting back to its original key before lookup.
        """
        original_setting_key = formatted_settings.get(setting_key, setting_key)
        return gr.update(choices=list(get_characters(original_setting_key).keys()))

    # Update character dropdown dynamically
    setting_dropdown.change(update_characters, inputs=[setting_dropdown], outputs=[character_dropdown])

    # --------------------------------------------------------
    # EXECUTE FULL PIPELINE ON BUTTON CLICK
    # --------------------------------------------------------

    generate_button.click(
        fn=full_pipeline, 
        inputs=[setting_dropdown, character_dropdown, theme_dropdown],
        outputs=[story_output, final_audio_output]
    )

    # --------------------------------------------------------
    # CREDITS & LICENSE INFORMATION
    # --------------------------------------------------------

    gr.Markdown("## 📜 Credits & Licenses")
    gr.Markdown("This application uses the following models:")
    
    gr.Markdown("### **Llama 3.1** (Meta AI)")
    gr.File(value=LICENSE_LLAMA, label="Download Llama 3.1 License")

    gr.Markdown("### **MeloTTS** (TTS)")
    gr.File(value=LICENSE_MELO, label="Download MeloTTS License")

    gr.Markdown("### **Facebook MusicGen** (Meta AI)")
    gr.File(value=LICENSE_MUSIC, label="Download Facebook MusicGen License")

# Launch Gradio app
demo.launch(share=False, inbrowser=True)