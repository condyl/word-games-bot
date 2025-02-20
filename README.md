# Word Finder Game Bot

This project is a bot designed to play a word finder game. It captures the game board, identifies the game version, finds all valid words, and draws them on the screen.

## Features

- Capture game board from screenshots
- Identify game version
- Find all valid words on the game board
- Draw words on the screen
- Handle different game versions and board sizes

## Requirements

- Python 3.8+
- Quartz (for macOS)
- Additional dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/condyl/auto-word-hunt.git
    cd auto-word-hunt
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Ensure you have the necessary word list file:
    - [collins-word-list-2019-filtered.txt](http://_vscodecontentref_/0)

## Usage

1. Start the bot:
    ```sh
    python main.py
    ```

2. The bot will automatically capture the game board, identify the game version, find all valid words, and draw them on the screen.

## File Structure

- [main.py](http://_vscodecontentref_/1): Main entry point for the bot
- [get_game_board.py](http://_vscodecontentref_/2): Captures the game board from screenshots
- [identify_game_version.py](http://_vscodecontentref_/3): Identifies the game version
- [word_finder.py](http://_vscodecontentref_/4): Finds all valid words on the game board
- [word_drawer.py](http://_vscodecontentref_/5): Draws words on the screen
- [press_start_button.py](http://_vscodecontentref_/6): Focuses the game window and clicks the start button
- [filter_collins.py](http://_vscodecontentref_/7): Filters the Collins word list
- [word_lists](http://_vscodecontentref_/8): Directory containing word list files
- [debug](http://_vscodecontentref_/9): Directory containing debug screenshots

## License

This project is licensed under the MIT License.