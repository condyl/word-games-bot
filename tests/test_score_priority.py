import sys
import os
import random
from dataclasses import dataclass
from typing import List, Tuple, Any

# Add the parent directory to the path so we can import word_finder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.game.word_finder import are_words_related, optimize_word_order

# Create a mock WordBitesMove class that doesn't override our scores
@dataclass
class MockWordBitesMove:
    word: str
    block_moves: List[Any]
    score: int

def main():
    # Create test moves with various scores and relationships
    test_moves = [
        # High-scoring words (2000+ points)
        MockWordBitesMove(word="QUIZZICAL", block_moves=[], score=2800),
        MockWordBitesMove(word="XYLOPHONE", block_moves=[], score=2600),
        MockWordBitesMove(word="JACKPOT", block_moves=[], score=2200),
        
        # Medium-scoring related words (1200-1600 points)
        MockWordBitesMove(word="THINK", block_moves=[], score=1200),
        MockWordBitesMove(word="THINKS", block_moves=[], score=1400),
        MockWordBitesMove(word="THINKER", block_moves=[], score=1600),
        MockWordBitesMove(word="THINKERS", block_moves=[], score=1500),
        
        # Medium-scoring related words (1100-1500 points)
        MockWordBitesMove(word="PLAY", block_moves=[], score=1100),
        MockWordBitesMove(word="PLAYER", block_moves=[], score=1300),
        MockWordBitesMove(word="PLAYERS", block_moves=[], score=1500),
        
        # Lower-scoring related words (600-900 points)
        MockWordBitesMove(word="RUN", block_moves=[], score=600),
        MockWordBitesMove(word="RUNS", block_moves=[], score=700),
        MockWordBitesMove(word="RUNNER", block_moves=[], score=800),
        MockWordBitesMove(word="RUNNING", block_moves=[], score=900)
    ]
    
    # Shuffle the moves to ensure the sorting algorithm is tested
    random.shuffle(test_moves)
    
    # Print original order
    print("Original order:")
    for move in test_moves:
        print(f"{move.word}: {move.score} points")
    
    # Optimize the order
    optimized_moves = optimize_word_order(test_moves)
    
    # Print optimized order
    print("\nOptimized order:")
    for move in optimized_moves:
        print(f"{move.word}: {move.score} points")
    
    # Group the optimized moves to verify grouping logic
    print("\nGroups formed:")
    current_group = [optimized_moves[0]]
    for i in range(1, len(optimized_moves)):
        current_move = optimized_moves[i]
        prev_move = optimized_moves[i-1]
        
        # Check if current move is related to previous move and within score threshold
        if are_words_related(current_move.word, prev_move.word) and abs(current_move.score - prev_move.score) <= 400:
            current_group.append(current_move)
        else:
            # Print the completed group
            words = [move.word for move in current_group]
            scores = [move.score for move in current_group]
            print(f"Group (avg score: {sum(scores)/len(scores):.1f}): {words}")
            # Start a new group
            current_group = [current_move]
    
    # Print the last group
    if current_group:
        words = [move.word for move in current_group]
        scores = [move.score for move in current_group]
        print(f"Group (avg score: {sum(scores)/len(scores):.1f}): {words}")

if __name__ == "__main__":
    main() 