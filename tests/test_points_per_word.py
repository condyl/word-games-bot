import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from word_finder import WordBitesMove, optimize_word_order, are_words_related

# Create test moves with groups having different average points per word
moves = [
    # Group 1: THINK family (4 words, avg score = 1200)
    WordBitesMove('THINK', [], 400),
    WordBitesMove('THINKS', [], 800),
    WordBitesMove('THINKER', [], 1600),
    WordBitesMove('THINKERS', [], 2000),
    
    # Group 2: PLAY family (3 words, avg score = 1600)
    WordBitesMove('PLAY', [], 800),
    WordBitesMove('PLAYER', [], 1600),
    WordBitesMove('PLAYERS', [], 2400),
    
    # Group 3: RUN family (4 words, avg score = 800)
    WordBitesMove('RUN', [], 400),
    WordBitesMove('RUNS', [], 600),
    WordBitesMove('RUNNER', [], 1000),
    WordBitesMove('RUNNING', [], 1200),
    
    # Group 4: WALK family (2 words, avg score = 2000)
    WordBitesMove('WALK', [], 1600),
    WordBitesMove('WALKING', [], 2400),
    
    # Group 5: TALK family (2 words, avg score = 1600)
    WordBitesMove('TALK', [], 800),
    WordBitesMove('TALKING', [], 2400),
    
    # Test for leading unrelated letters
    WordBitesMove('THINK', [], 400),
    WordBitesMove('UNTHINK', [], 1600),  # Should not be grouped with THINK
    
    # High-scoring single words
    WordBitesMove('QUIZZICAL', [], 3600),  # Highest points per word (3600)
    WordBitesMove('XYLOPHONE', [], 3200),  # Second highest points per word (3200)
    WordBitesMove('JACKPOT', [], 2800),    # Third highest points per word (2800)
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

# Identify and print groups with their average points
print("\nGroups by average points per word:")
current_group = []

for move in optimized_moves:
    # Check if this is a new group
    if not current_group or not any(are_words_related(move.word, prev.word) for prev in current_group):
        if current_group:
            total_score = sum(m.score for m in current_group)
            avg_score = total_score / len(current_group)
            print(f"Group size: {len(current_group)}, Avg points: {avg_score:.1f}, Total: {total_score}, Words: {[m.word for m in current_group]}")
        current_group = [move]
    else:
        current_group.append(move)

# Print the last group
if current_group:
    total_score = sum(m.score for m in current_group)
    avg_score = total_score / len(current_group)
    print(f"Group size: {len(current_group)}, Avg points: {avg_score:.1f}, Total: {total_score}, Words: {[m.word for m in current_group]}")

# Test if "THINK" and "UNTHINK" are considered related
print("\nTesting leading unrelated letters:")
print(f"Are 'THINK' and 'UNTHINK' related? {are_words_related('THINK', 'UNTHINK')}") 