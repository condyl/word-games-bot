import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from word_finder import WordBitesMove, optimize_word_order, are_words_related

# Create test moves with multiple groups of the same size but different max scores
moves = [
    # Group 1: THINK family (4 words, max score 2400)
    WordBitesMove('THINK', [], 400),
    WordBitesMove('THINKS', [], 800),
    WordBitesMove('THINKER', [], 1600),
    WordBitesMove('THINKERS', [], 2400),
    
    # Group 2: PLAY family (4 words, max score 2000)
    WordBitesMove('PLAY', [], 400),
    WordBitesMove('PLAYER', [], 800),
    WordBitesMove('PLAYING', [], 1600),
    WordBitesMove('PLAYERS', [], 2000),
    
    # Group 3: RUN family (4 words, max score 1600)
    WordBitesMove('RUN', [], 100),
    WordBitesMove('RUNS', [], 400),
    WordBitesMove('RUNNER', [], 1600),
    WordBitesMove('RUNNING', [], 1600),
    
    # Group 4: WALK family (3 words, max score 2800)
    WordBitesMove('WALK', [], 400),
    WordBitesMove('WALKER', [], 1600),
    WordBitesMove('WALKING', [], 2800),
    
    # Group 5: TALK family (2 words, max score 3200)
    WordBitesMove('TALK', [], 400),
    WordBitesMove('TALKATIVE', [], 3200),
    
    # High-scoring single words
    WordBitesMove('QUIZZICAL', [], 3600),
    WordBitesMove('XYLOPHONE', [], 3200),
    WordBitesMove('JACKPOT', [], 2800),
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

# Identify and print groups
print("\nGroups:")
current_group = []

for move in optimized_moves:
    # Check if this is a new group
    if not current_group or not any(are_words_related(move.word, prev.word) for prev in current_group):
        if current_group:
            max_score = max(m.score for m in current_group)
            print(f"Group size: {len(current_group)}, Max score: {max_score}, Words: {[m.word for m in current_group]}")
        current_group = [move]
    else:
        current_group.append(move)

# Print the last group
if current_group:
    max_score = max(m.score for m in current_group)
    print(f"Group size: {len(current_group)}, Max score: {max_score}, Words: {[m.word for m in current_group]}") 