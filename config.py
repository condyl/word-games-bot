# Game timing constants
GAME_DURATION = 80  # seconds
MIN_WORD_LENGTH = 3
CLICK_DELAY = 0.02  # seconds between clicks/drags

# Window detection keywords
IPHONE_WINDOW_KEYWORDS = ['iPhone', 'iOS', 'QuickTime Player']

# Board dimensions
BOARD_SIZES = {
    '4x4': 4,
    '5x5': 5,
    'X': 5,
    'O': 5,
    'ANAGRAM6': 6,
    'ANAGRAM7': 7
}

# Empty cell patterns
EMPTY_CELLS = {
    'X': {(2,0), (0,2), (4,2), (2,4)},
    'O': {(0,0), (0,4), (2,2), (4,0), (4,4)}
}

# Word scoring
WORD_SCORES = {
    3: 100,
    4: 400,
    5: 800,
    6: 1400,
    7: 1800,
    8: 2200,
    9: 2600
}

# File paths
WORD_LIST_PATH = 'word_lists/collins-word-list-2019-filtered.txt'
DEBUG_DIR = 'debug' 