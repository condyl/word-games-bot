# Game Pigeon Word Game Solver

A Python bot that automatically solves word games in Game Pigeon. Supports Word Hunt, Anagrams, and Word Bites.

<img width="292" alt="image" src="https://github.com/user-attachments/assets/235b1f25-21ab-4823-91d9-7d27b928cddf" />
<img width="297" alt="image" src="https://github.com/user-attachments/assets/ee912181-bda6-47f2-9913-1037050f2d0a" />
<img width="299" alt="image" src="https://github.com/user-attachments/assets/8f121c47-7fc1-40f9-a89c-5ab5f330b100" />


## Requirements

- macOS with iPhone mirroring capabilities
- Python 3.8+
- Dependencies in `requirements.txt`

## Installation

1. Clone and install dependencies:
```sh
git clone https://github.com/condyl/game-pigeon-winner.git
cd game-pigeon-winner
pip install -r requirements.txt
```

## Usage

1. Mirror your iPhone to your Mac
2. Open Game Pigeon and start a word game
3. Run the bot with optional arguments:
```sh
# Normal mode - finds all possible words
python main.py

# Realistic mode - limits scores to human-like levels
python main.py --realistic

# Target score mode - aims for a specific score
python main.py --target 10000

# Debug mode - saves screenshots and processing images
python main.py --debug
```

## Project Structure

```
game-pigeon-winner/
├── src/                    # Source code
│   ├── game/              # Game-specific modules
│   ├── config/            # Configuration files
│   └── utils/             # Utility functions
├── scripts/               # Utility scripts
├── tests/                 # Test files
├── word_lists/           # Word list files
└── requirements.txt      # Python dependencies
```

## Features

- Automatic game board detection
- Word finding and drawing
- Support for all game modes
- Realistic mode for human-like scores
- Target score mode for custom score limits
- Debug mode for troubleshooting
- Optimized word selection and drawing

## License

MIT License
