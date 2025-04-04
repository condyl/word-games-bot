import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game.word_finder import WordBitesMove, optimize_word_order, are_words_related

# Create test moves with various words and scores
moves = [
    WordBitesMove('PLAY', [], 400),
    WordBitesMove('PLAYER', [], 800),
    WordBitesMove('PLAYERS', [], 1200),
    WordBitesMove('THINK', [], 400),
    WordBitesMove('THINKS', [], 800),
    WordBitesMove('THINKER', [], 800),
    WordBitesMove('THINKERS', [], 1200),
    WordBitesMove('RUN', [], 100),
    WordBitesMove('RUNS', [], 400),
    WordBitesMove('RUNNER', [], 800),
    WordBitesMove('RUNNING', [], 800),
]

# Shuffle the moves to ensure the algorithm works regardless of initial order
import random
random.shuffle(moves)

# Print original order
print("Original order:")
for i, move in enumerate(moves):
    print(f"{i+1}. {move.word} ({move.score} points)")

# Optimize the order
optimized_moves = optimize_word_order(moves)

# Print optimized order
print("\nOptimized order:")
for i, move in enumerate(optimized_moves):
    print(f"{i+1}. {move.word} ({move.score} points)")

# Print groups
print("\nGroups:")
current_group = []
current_base = ""

for move in optimized_moves:
    # Check if this is a new group
    if not current_group or not any(are_words_related(move.word, prev.word) for prev in current_group):
        if current_group:
            print(f"Group: {[m.word for m in current_group]}")
        current_group = [move]
    else:
        current_group.append(move)

# Print the last group
if current_group:
    print(f"Group: {[m.word for m in current_group]}") 