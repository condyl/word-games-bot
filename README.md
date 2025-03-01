# Word Finder Game Bot

This project is a bot designed to play a word finder game. It captures the game board, identifies the game version, finds all valid words, and draws them on the screen.

<img width="292" alt="image" src="https://github.com/user-attachments/assets/235b1f25-21ab-4823-91d9-7d27b928cddf" />
<img width="297" alt="image" src="https://github.com/user-attachments/assets/ee912181-bda6-47f2-9913-1037050f2d0a" />
<img width="299" alt="image" src="https://github.com/user-attachments/assets/2234036f-f0b7-454e-ad91-2dd79dd59783" />



## Features

- Capture game board from screenshots
- Identify game version
- Find all valid words on the game board
- Draw words on the screen
- Handle different game versions and board sizes
- Optimize word order to prioritize high-scoring words first
- Group related words with similar scores for efficient gameplay
- Intelligently build upon existing words rather than rebuilding from scratch
- Ultra-high-speed gameplay across all game modes (Word Hunt, Anagrams, and Word Bites)
- Support for both horizontal (left-to-right) and vertical (top-to-bottom) words in Word Bites

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

## Word Prioritization

The bot uses a sophisticated algorithm to prioritize words:

1. Words are first sorted by their point value (highest first)
2. Words with similar scores (within a 400-point threshold) that are related (e.g., "THINK", "THINKS", "THINKER") are grouped together
3. Words within each group are sorted by length (shortest to longest)

This ensures that high-value words are played first, while still maintaining the efficiency of playing related words back-to-back when their scores are similar.

## Efficient Word Building

For related words (e.g., "ICEWORM" and "ICEWORMS"), the bot intelligently builds upon the existing word rather than rebuilding it from scratch. This significantly improves efficiency by:

1. Identifying when a new word is an extension of a previously formed word
2. Only moving the additional blocks needed to form the new word
3. Preserving the existing word structure on the board

This optimization is especially effective for groups of related words, reducing the number of block movements required and increasing the speed of gameplay.

## Ultra-High-Speed Gameplay

The bot is optimized for ultra-fast gameplay:

- **Word Hunt and Anagrams**: Ultra-short mouse movement delays (0.001 seconds) for lightning-fast word drawing
- **Word Bites**: 
  - Priority queue system for immediate word formation (no 15-20 second delay)
  - Ultra-short mouse movement delays (0.005 seconds)
  - Optimized drag patterns with fewer intermediate points
  - Reduced delays between related words (0.03 seconds)
  - Reduced delays between groups (0.05 seconds)
  - Faster lookups in block restoration process
  - Reduced delay between block movements to 0.005 seconds
  - Word registration delay reduced to 0.05 seconds
  - Optimized block movement with minimal attempts
  - Support for both horizontal and vertical word formation for maximum scoring opportunities
  - Concurrent processing of word finding and word formation

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
- [tests](http://_vscodecontentref_/10): Directory containing test files

## Running Tests

To run all tests:

```sh
python3 tests/run_all_tests.py
```

To run a specific test:

```sh
python3 tests/test_score_priority.py
```

The test suite includes:
- `test_score_priority.py`: Tests prioritization by score first, then grouping related words
- `test_points_per_word.py`: Tests word grouping by average points per word
- `test_complex_priority.py`: Tests complex prioritization of word groups
- `test_word_priority.py`: Tests prioritization of groups over single words
- `test_word_order.py`: Tests basic word ordering functionality
- `test_groups.py`: Tests grouping of related words
- `test_word_extension.py`: Tests building upon existing words rather than rebuilding from scratch
- `test_vertical_words.py`: Tests finding both horizontal and vertical words in Word Bites

## License

This project is licensed under the MIT License.
