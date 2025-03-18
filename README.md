# AI Storyteller Proof of Concept / Demo

## Introduction

This project is an AI-powered storytelling application that allows users to generate and narrate customized children's stories. The application follows a structured workflow to ensure high-quality stories, engaging narration, and fitting background music.

## Features

- **Metadata Selection**: Users can choose settings, characters, and themes to customize their stories.
- **Story Generation**: Uses the Llama 3.1 model to generate stories in a three-act structure.
- **Story Validation**: Ensures readability, appropriate word count, and absence of prohibited words.
- **Narration (Text-to-Speech)**: Converts the story into narrated audio using MeloTTS.
- **Music Generation**: Creates background music clips using MusicGen-small from Facebook.
- **Audio Combination**: Merges narration and music into a final audio output.
- **User Interface**: A Gradio-based UI for easy interaction.

### Key Files and Directories

- **app/**: Contains the main application code.
  - `app.py`: Main application script with Gradio UI.
  - `combine_audio.py`: Functions to combine narration and music.
  - `config.py`: Configuration settings and paths.
  - `music_gen.py`: Functions to generate background music.
  - `story_gen.py`: Functions to generate stories.
  - `tts_gen.py`: Functions to generate text-to-speech narration.
- **data/**: Contains metadata and prompt templates.
  - `frontend_metadata.json`: Metadata for settings, characters, and themes.
  - `prompts/`: Directory with text prompt templates for story and music generation.
- **doc/**: Documentation files.
  - `steps.txt`: Steps and notes on the project development.
  - `summary.txt`: Summary of the project and its components.
- **generated/**: Directory for generated outputs (ignored by git).
  - `final_audio/`: Final combined audio files.
  - `music/`: Generated music clips.
  - `narrations/`: Generated narration audio files.
  - `stories/`: Generated story text files.
- **licenses/**: License files for the models used.
  - `llama3_1_license.txt`: License for Llama 3.1.
  - `melotts_license.txt`: License for MeloTTS.
  - `musicgen_license.txt`: License for MusicGen.
- **tests/**: Test scripts and generated test outputs (ignored by git).

## Installation

1. Clone the repository.
2. Install the required dependencies: `pip install -r requirements.txt`

## Usage

1. Run the application: `python app/app.py`
2. Open the Gradio interface in your browser.
3. Select the desired setting, characters, and theme.
4. Click "Create your custom story!" to generate and listen to the story.

## Credits & Licenses

This application uses the following models:

Llama 3.1 (Meta AI)
    License: llama3_1_license.txt
MeloTTS (TTS)
    License: melotts_license.txt
Facebook MusicGen (Meta AI)
    License: musicgen_license.txt

## License

This project is licensed under the MIT License. See the LICENSE file for details.
