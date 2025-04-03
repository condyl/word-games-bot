import os

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
    9: 2600,
    10: 3000,
    11: 3400,
    12: 3800,
    13: 4200,
    14: 4600,
    15: 5000,
    16: 5400
}

# Word list path
WORD_LIST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'word_lists/collins-word-list-2019-filtered.txt')

DEBUG_DIR = 'debug' 