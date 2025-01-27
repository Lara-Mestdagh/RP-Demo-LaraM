import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data/")
PROMPT_DIR = os.path.join(DATA_DIR, "prompts")
METADATA_PATH = os.path.join(DATA_DIR, "frontend_metadata.json")
STORIES_DIR = os.path.join(BASE_DIR, "../generated/stories/")
NARRATIONS_DIR = os.path.join(BASE_DIR, "../generated/narrations/")
MUSIC_DIR = os.path.join(BASE_DIR, "../generated/music/")
FINAL_AUDIO_DIR = os.path.join(BASE_DIR, "../generated/final_audio/")
LICENSE_DIR = os.path.join(BASE_DIR, "../licenses/")
LICENSE_LLAMA = os.path.join(LICENSE_DIR, "llama3_1_license.txt")
LICENSE_MELO = os.path.join(LICENSE_DIR, "melotts_license.txt")
LICENSE_MUSIC = os.path.join(LICENSE_DIR, "musicgen_license.txt")



INSTRUMENTS_BY_SETTING = {
    "Magical Forest": ["flute", "harp", "chimes"], 
    "Small Kingdom": ["violin", "horns", "drums"], 
    "Desert Oasis": ["oud", "darbuka drums", "flute"], 
    "Underwater World": ["synth pads", "harp", "bubble sounds"], 
    "Flower Meadow": ["acoustic guitar", "soft piano", "wind chimes"], 
    "Snowy Land": ["celesta", "soft piano", "bells"], 
    "Sky Island": ["airy synth", "harp", "angelic choir"], 
    "Crystal Cave": ["glass harmonica", "chimes", "echoing pads"], 
}


# List of prohibited words/phrases
PROHIBITED_WORDS = [
    # Violence and Weapons
    r"\bviolence\b", r"\bwar\b",
    r"\bdeath\b", r"\battack\b", r"\bgun\b", r"\bknife\b",
    r"\bbomb\b", r"\btorture\b", r"\bmurder\b", r"\babuse\b",
    r"\binjure\b", r"\bexplode\b", r"\bpoison\b",

    # Hate and Prejudice
    r"\bhate\b", r"\bracism\b", r"\bbully\b", r"\bprejudice\b",
    r"\boppress\b", r"\bslur\b", r"\bdiscriminate\b", r"\binsult\b",

    # Horror and Fear
    r"\bghost\b", r"\bnightmare\b", r"\bterror\b", r"\bcreepy\b",
    r"\bevil\b", r"\bhaunt\b", r"\bskeleton\b", r"\bzombie\b",

    # Adult Themes
    r"\balcohol\b", r"\bdrugs\b", r"\bsex\b", r"\bnudity\b",
    r"\bporn\b", r"\bstrip\b", r"\bseduce\b",

    # Self-Harm and Mental Health
    r"\bsuicide\b", r"\bdepress\b",

    # Negative Attributes
    r"\bloser\b", r"\bugly\b", r"\bdumb\b", r"\bidiot\b",
    r"\bfool\b", r"\bfat\b", r"\bstupid\b",

    # Crime
    r"\bsteal\b", r"\bcrime\b", r"\bjail\b",
]