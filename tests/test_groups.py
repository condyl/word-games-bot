import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game.word_finder import WordBitesMove, group_related_words, are_words_related

# Create test moves with a more diverse set of words
moves = [
    WordBitesMove('THINK', [], 400),
    WordBitesMove('THINKS', [], 800),
    WordBitesMove('THINKER', [], 800),
    WordBitesMove('THINKERS', [], 1200),
    WordBitesMove('PLAY', [], 400),
    WordBitesMove('PLAYER', [], 800),
    WordBitesMove('PLAYERS', [], 1200),
    WordBitesMove('RUN', [], 100),
    WordBitesMove('RUNS', [], 400),
    WordBitesMove('RUNNER', [], 800),
    WordBitesMove('RUNNING', [], 800),
    WordBitesMove('WALK', [], 400),
    WordBitesMove('WALKING', [], 800),
    WordBitesMove('WALKER', [], 800),
    WordBitesMove('TALK', [], 400),
    WordBitesMove('TALKING', [], 800)
]

# Group related words
groups = group_related_words(moves)

# Print results
print(f'Number of groups: {len(groups)}')
for i, group in enumerate(groups):
    print(f'Group {i+1}: {[m.word for m in group]}')

# Test individual word relationships
print("\nTesting individual word relationships:")
word_pairs = [
    ('THINK', 'THINKS'),
    ('THINK', 'THINKER'),
    ('RUN', 'RUNNING'),
    ('RUN', 'RUNNER'),
    ('WALK', 'WALKING'),
    ('TALK', 'TALKING'),
    ('PLAY', 'PLAYER'),
    ('THINK', 'PLAY'),  # Should be unrelated
    ('RUN', 'WALK')     # Should be unrelated
]

for word1, word2 in word_pairs:
    related = are_words_related(word1, word2)
    print(f"'{word1}' and '{word2}' are {'related' if related else 'not related'}")
