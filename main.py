from get_game_board import get_game_board
from identify_game_version import identify_game_version
from word_finder import find_words, find_anagrams, print_found_words, print_anagram_words, find_word_bites_words, print_word_bites_moves, WordBitesMove, are_words_related, optimize_word_order
from word_drawer import draw_word, click_anagram_word, execute_word_bites_move
from press_start_button import focus_and_click_start
import time
import signal
from concurrent.futures import ThreadPoolExecutor
import heapq
from dataclasses import dataclass, field
from typing import Tuple, List
import os
from threading import Lock
from config import GAME_DURATION, WORD_SCORES
import traceback
import argparse
import random
import re
from collections import defaultdict

# Parse command line arguments
parser = argparse.ArgumentParser(description='Game Pigeon Word Game Solver')
parser.add_argument('--realistic', '-r', action='store_true', 
                    help='Enable realistic mode with human-like scores (15k-25k for Word Hunt, 20k-40k for Word Bites)')
parser.add_argument('--target', '-t', type=int,
                    help='Set target score for the game (overrides realistic mode ranges)')
parser.add_argument('--debug', '-d', action='store_true',
                    help='Save debug screenshots during gameplay')
args = parser.parse_args()

# Global variables
WORDS_FOUND = 0
GAME_VERSION = "unknown"
TIME_REMAINING = 90  # Track time remaining
START_TIME = 0  # Track start time globally
REALISTIC_MODE = False  # Default to perfect mode
TARGET_SCORE = None  # Track target score if specified
SAVE_DEBUG_SCREENSHOTS = False  # Track whether to save debug screenshots

# Word Hunt target scores for realistic mode
WORD_HUNT_MIN_SCORE = 17500
WORD_HUNT_MAX_SCORE = 25000
# Word Bites target scores for realistic mode
WORD_BITES_MIN_SCORE = 20000
WORD_BITES_MAX_SCORE = 40000

@dataclass(order=True)
class PrioritizedWord:
    priority: int
    word: str = None
    path: List[Tuple[int, int]] = None
    
    def __init__(self, word: str, path: List[Tuple[int, int]]):
        self.priority = -len(word)  # Negative length for max-heap behavior
        self.word = word
        self.path = path

@dataclass(order=True)
class PrioritizedWordBitesMove:
    priority: int
    move: WordBitesMove = field(compare=False)
    
    def __init__(self, move: WordBitesMove):
        # Negative score for max-heap behavior (highest score first)
        self.priority = -move.score
        
        # Prioritize vertical words of the same length/score
        # This ensures vertical words with the same score as horizontal words
        # will be processed first, without changing their actual score
        if move.is_vertical:
            # Use a small priority boost that doesn't affect the actual score
            self.priority -= 0.1  # Subtract a small value to increase precedence
            
        self.move = move

def timeout_handler(signum, frame):
    # Calculate time elapsed
    time_elapsed = time.time() - START_TIME
    
    print("\nTime's up! Game summary:")
    print("------------------------")
    if GAME_VERSION == "unknown":
        print("Game version: Unknown - Game identification failed or timed out")
    else:
        print(f"Game version: {GAME_VERSION}")
    print(f"Words found: {WORDS_FOUND}")
    print(f"Time played: {time_elapsed:.1f} seconds (of {GAME_DURATION} seconds)")
    print("Program terminated.")
    os._exit(0)

def update_time_remaining():
    global TIME_REMAINING
    TIME_REMAINING = max(0, GAME_DURATION - (time.time() - START_TIME))

def apply_realistic_mode_word_hunt(all_words):
    """
    Apply realistic mode filtering to Word Hunt words with improved word selection.
    Focuses on common substrings and word families to create more natural word patterns.
    """
    from word_finder import calculate_score
    from collections import defaultdict
    
    # Calculate total possible score
    total_possible_score = calculate_score(all_words)
    print(f"Total possible score: {total_possible_score}")
    
    # Determine target score
    if TARGET_SCORE is not None:
        target_score = min(TARGET_SCORE, total_possible_score * 0.8)
        print(f"Using specified target score: {target_score}")
    else:
        target_score = random.randint(WORD_HUNT_MIN_SCORE, WORD_HUNT_MAX_SCORE)
        target_score = min(target_score, total_possible_score * 0.8)
        print(f"Target score for realistic mode: {target_score}")

    def find_common_substrings(words, min_length=3):
        """
        Find common substrings among the words and their frequencies.
        Returns a dictionary of substrings and their frequencies.
        """
        substring_freq = defaultdict(int)
        for word in words:
            word = word.lower()
            for length in range(min_length, len(word) + 1):
                for i in range(len(word) - length + 1):
                    substring = word[i:i + length]
                    substring_freq[substring] += 1
        return substring_freq
    
    def get_word_value(word, substring_freq):
        """
        Calculate a word's value based on its substrings.
        Returns a tuple of (substring_score, length_score) for sorting.
        """
        word = word.lower()
        max_freq = 0
        for length in range(3, len(word) + 1):
            for i in range(len(word) - length + 1):
                substring = word[i:i + length]
                freq = substring_freq[substring]
                max_freq = max(max_freq, freq)
        return max_freq
    
    # Find common substrings among all words
    substring_freq = find_common_substrings(all_words.keys())
    
    # Group words by their most valuable substrings
    word_groups = defaultdict(list)
    for word in all_words:
        best_substring = ""
        best_value = 0
        word_lower = word.lower()
        for length in range(3, len(word) + 1):
            for i in range(len(word) - length + 1):
                substring = word_lower[i:i + length]
                if substring_freq[substring] > best_value:
                    best_value = substring_freq[substring]
                    best_substring = substring
        word_groups[best_substring].append(word)
    
    # Sort groups by their frequency
    sorted_groups = sorted(word_groups.items(), 
                         key=lambda x: (substring_freq[x[0]], len(x[1])), 
                         reverse=True)
    
    # Select words to reach target score
    selected_words = {}
    current_score = 0
    
    # Calculate word scores
    word_scores = {}
    for word in all_words:
        length = len(word)
        word_scores[word] = WORD_SCORES.get(length, 400 * (length - 2))
    
    # Process each group of related words
    for substring, group in sorted_groups:
        if current_score >= target_score:
            break
            
        # Sort words within group by length (shorter first)
        sorted_words = sorted(group, key=len)
        
        # Take a percentage of words from each group
        num_to_take = max(1, int(len(sorted_words) * 0.7))
        
        # Always include the shortest word in the group
        if sorted_words:
            shortest = sorted_words[0]
            if shortest not in selected_words:
                selected_words[shortest] = all_words[shortest]
                current_score += word_scores[shortest]
        
        # Then add related words
        for word in sorted_words[1:num_to_take]:
            if current_score >= target_score:
                break
                
            if current_score + word_scores[word] > target_score:
                if current_score > target_score * 0.9:
                    break
                if len(word) > 6 and random.random() > 0.3:
                    continue
            
            selected_words[word] = all_words[word]
            current_score += word_scores[word]
    
    # If we haven't reached our target score, add some additional words
    if current_score < target_score * 0.9:
        remaining_words = [w for w in all_words if w not in selected_words]
        remaining_words.sort(key=lambda w: (len(w), get_word_value(w, substring_freq)))
        
        for word in remaining_words:
            if current_score >= target_score:
                break
                
            if current_score + word_scores[word] > target_score:
                if current_score > target_score * 0.9:
                    break
                if random.random() > 0.3:
                    continue
            
            selected_words[word] = all_words[word]
            current_score += word_scores[word]
    
    # Ensure we don't exceed the maximum score
    if current_score > WORD_HUNT_MAX_SCORE:
        print(f"Score {current_score} exceeds maximum target of {WORD_HUNT_MAX_SCORE}, removing some words...")
        words_to_remove = []
        
        # Sort words by their substring value (remove words with less common substrings first)
        for word in sorted(selected_words.keys(), 
                         key=lambda w: (-get_word_value(w, substring_freq), -len(w))):
            if current_score <= WORD_HUNT_MAX_SCORE:
                break
            words_to_remove.append(word)
            current_score -= word_scores[word]
        
        for word in words_to_remove:
            del selected_words[word]
    
    # Print statistics about the selected words
    print(f"\nSelected {len(selected_words)} words with a total score of {current_score}")
    print(f"Target was {target_score}, which is {current_score/target_score*100:.1f}% of target")
    
    # Print distribution of word lengths
    length_distribution = {}
    for word in selected_words:
        length = len(word)
        length_distribution[length] = length_distribution.get(length, 0) + 1
    
    print("\nWord length distribution:")
    for length in sorted(length_distribution.keys()):
        print(f"{length} letters: {length_distribution[length]} words")
    
    # Print example word families
    print("\nExample word families:")
    shown_families = 0
    for substring, group in sorted_groups:
        if shown_families >= 5:
            break
        selected_family = [w for w in group if w in selected_words]
        if len(selected_family) >= 2:
            print(f"Family with '{substring}': {', '.join(sorted(selected_family, key=len))}")
            shown_families += 1
    
    return selected_words

def apply_realistic_mode_word_bites(all_moves):
    """
    Apply realistic mode filtering to Word Bites moves with improved word selection.
    Focuses on common substrings and word families to create more natural word patterns.
    """
    from word_finder import calculate_score
    from collections import defaultdict
    
    # Calculate total possible score
    total_possible_score = sum(move.score for move in all_moves)
    print(f"Total possible score: {total_possible_score}")
    
    # Determine target score
    if TARGET_SCORE is not None:
        target_score = min(TARGET_SCORE, total_possible_score * 0.8)
        print(f"Using specified target score: {target_score}")
    else:
        target_score = random.randint(WORD_BITES_MIN_SCORE, WORD_BITES_MAX_SCORE)
        target_score = min(target_score, total_possible_score * 0.8)
        print(f"Target score for realistic mode: {target_score}")
    
    # Group moves by word length
    moves_by_length = {}
    for move in all_moves:
        length = len(move.word)
        if length not in moves_by_length:
            moves_by_length[length] = []
        moves_by_length[length].append(move)
    
    # Randomize moves within each length group
    for length in moves_by_length:
        random.shuffle(moves_by_length[length])
    
    # Create a dictionary of words to moves for easier lookup
    word_to_move = {move.word: move for move in all_moves}
    
    # Find related words (words that are substrings of other words)
    related_words = {}
    for move in all_moves:
        word = move.word
        related_words[word] = []
        for other_move in all_moves:
            other_word = other_move.word
            if word != other_word:
                # Check if one word is contained in the other
                if word in other_word or other_word in word:
                    related_words[word].append(other_word)
                # Check for common prefix (at least 3 letters)
                elif len(word) >= 3 and len(other_word) >= 3:
                    prefix_len = min(len(word), len(other_word))
                    if word[:prefix_len] == other_word[:prefix_len]:
                        related_words[word].append(other_word)
    
    # Select moves to reach target score
    selected_moves = []
    selected_words = set()  # Keep track of selected words
    current_score = 0
    
    # First, include a percentage of shorter words (3-5 letters)
    for length in range(3, 6):
        if length in moves_by_length:
            # Take a moderate percentage of shorter words, but limit by target score
            percentage = 0.6 if length == 3 else (0.65 if length == 4 else 0.7)
            num_to_take = max(1, int(len(moves_by_length[length]) * percentage))
            
            for move in moves_by_length[length][:num_to_take]:
                # Check if adding this word would exceed our target score
                if current_score + move.score > target_score:
                    # If we're already close to target, stop adding words
                    if current_score > target_score * 0.9:
                        break
                    # Otherwise, randomly decide whether to include this word
                    if random.random() > 0.3:  # 30% chance to include
                        continue
                
                selected_moves.append(move)
                selected_words.add(move.word)
                current_score += move.score
                
                # Also include some related longer words
                for related_word in related_words[move.word]:
                    if related_word not in selected_words and len(related_word) > len(move.word):
                        # Higher chance to include related words
                        if random.random() < 0.7:  # 70% chance to include related words
                            related_move = word_to_move[related_word]
                            selected_moves.append(related_move)
                            selected_words.add(related_word)
                            current_score += related_move.score
                            
                            # If we've reached our target, stop adding words
                            if current_score >= target_score:
                                break
                
                # If we've reached our target, stop adding words
                if current_score >= target_score:
                    break
    
    # Then add medium-length words (6-7 letters) if we haven't reached target
    if current_score < target_score * 0.9:  # Only if we're below 90% of target
        for length in range(6, 8):
            if length in moves_by_length and current_score < target_score:
                # Take a moderate percentage of medium words
                percentage = 0.6 if length == 6 else 0.55
                num_to_take = max(1, int(len(moves_by_length[length]) * percentage))
                
                for move in moves_by_length[length][:num_to_take]:
                    # Skip if already added as a related word
                    if move.word in selected_words:
                        continue
                        
                    # Check if adding this word would exceed our target score
                    if current_score + move.score > target_score:
                        # If we're already close to target, stop adding words
                        if current_score > target_score * 0.9:
                            break
                        # Otherwise, randomly decide whether to include this word
                        if random.random() > 0.4:  # 40% chance to include
                            continue
                    
                    selected_moves.append(move)
                    selected_words.add(move.word)
                    current_score += move.score
                    
                    # Also include some related longer words
                    for related_word in related_words[move.word]:
                        if related_word not in selected_words and len(related_word) > len(move.word):
                            # Higher chance to include related words
                            if random.random() < 0.7:  # 70% chance to include related words
                                related_move = word_to_move[related_word]
                                selected_moves.append(related_move)
                                selected_words.add(related_word)
                                current_score += related_move.score
                                
                                # If we've reached our target, stop adding words
                                if current_score >= target_score:
                                    break
                    
                    # If we've reached our target, stop adding words
                    if current_score >= target_score:
                        break
                
                # If we've reached our target, stop adding words
                if current_score >= target_score:
                    break
    
    # Finally, add longer words (8+ letters) only if we're well below target
    if current_score < target_score * 0.85:  # Only if we're below 85% of target
        for length in sorted(moves_by_length.keys()):
            if length >= 8 and current_score < target_score:
                # Take a higher percentage of longer words than before
                percentage = 0.5 if length == 8 else (0.4 if length == 9 else 0.3)
                num_to_take = max(1, int(len(moves_by_length[length]) * percentage))
                
                for move in moves_by_length[length][:num_to_take]:
                    # Skip if already added as a related word
                    if move.word in selected_words:
                        continue
                        
                    # Check if adding this word would exceed our target score
                    if current_score + move.score > target_score:
                        # If we're already close to target, stop adding words
                        if current_score > target_score * 0.9:
                            break
                        # Otherwise, randomly decide whether to include this word
                        if random.random() > 0.3:  # 30% chance to include
                            continue
                    
                    selected_moves.append(move)
                    selected_words.add(move.word)
                    current_score += move.score
                    
                    # If we've reached our target, stop adding words
                    if current_score >= target_score:
                        break
                
                # If we've reached our target, stop adding words
                if current_score >= target_score:
                    break
    
    # Ensure we don't exceed the maximum score
    if current_score > WORD_BITES_MAX_SCORE:
        print(f"Score {current_score} exceeds maximum target of {WORD_BITES_MAX_SCORE}, removing some words...")
        # Remove some words to get below the maximum, but try to preserve related word groups
        moves_to_remove = []
        
        # First, identify words that don't have many related words in our selection
        word_relation_count = {}
        for move in selected_moves:
            word = move.word
            word_relation_count[word] = 0
            for other_move in selected_moves:
                other_word = other_move.word
                if word != other_word and (word in other_word or other_word in word):
                    word_relation_count[word] += 1
        
        # Sort moves by relation count (ascending) and then by length (descending)
        # This way we remove words with fewer relations first, and longer words before shorter ones
        for move in sorted(selected_moves, key=lambda m: (word_relation_count[m.word], -len(m.word), -m.score)):
            if current_score <= WORD_BITES_MAX_SCORE:
                break
            moves_to_remove.append(move)
            current_score -= move.score
        
        for move in moves_to_remove:
            selected_moves.remove(move)
            selected_words.remove(move.word)
    
    print(f"Selected {len(selected_moves)} words with a total score of {current_score}")
    print(f"Target was {target_score}, which is {current_score/target_score*100:.1f}% of target")
    
    # Print distribution of word lengths
    length_distribution = {}
    for move in selected_moves:
        length = len(move.word)
        length_distribution[length] = length_distribution.get(length, 0) + 1
    
    print("Word length distribution:")
    for length in sorted(length_distribution.keys()):
        print(f"{length} letters: {length_distribution[length]} words")
    
    # Re-optimize the selected moves to ensure efficient gameplay
    return optimize_word_order(selected_moves)

def main():
    try:
        global START_TIME, WORDS_FOUND, GAME_VERSION, REALISTIC_MODE, TARGET_SCORE, SAVE_DEBUG_SCREENSHOTS
        words_found = 0
        
        # Set target score if specified
        if args.target is not None:
            TARGET_SCORE = args.target
            print(f"Target score set to: {TARGET_SCORE}")
            # Enable realistic mode if target score is specified
            REALISTIC_MODE = True
            print("Target score specified - enabling realistic mode")
        
        # Set realistic mode if specified
        if args.realistic:
            REALISTIC_MODE = True
            print("Realistic mode enabled")
            
        # Set debug screenshots if specified
        SAVE_DEBUG_SCREENSHOTS = args.debug
        if SAVE_DEBUG_SCREENSHOTS:
            print("Debug screenshots enabled")
        else:
            print("Debug screenshots disabled")
        
        if REALISTIC_MODE:
            print("Running in REALISTIC mode - scores will be limited to human-like levels")
            if TARGET_SCORE is not None:
                print(f"Target score: {TARGET_SCORE} points")
            else:
                print(f"Word Hunt target: {WORD_HUNT_MIN_SCORE}-{WORD_HUNT_MAX_SCORE} points")
                print(f"Word Bites target: {WORD_BITES_MIN_SCORE}-{WORD_BITES_MAX_SCORE} points")
        else:
            print("Running in PERFECT mode - will find all possible words")
        
        print("Starting game...")
        if not focus_and_click_start():
            print("Failed to start game - Could not find or click the start button")
            return
            
        print("Waiting for game to load...")
        time.sleep(2)
        
        signal.signal(signal.SIGALRM, timeout_handler)
        
        try:
            print("Identifying game version...")
            game_version = identify_game_version(save_debug=SAVE_DEBUG_SCREENSHOTS)
            
            if game_version is None:
                print("Failed to identify game version - No iPhone window found")
                GAME_VERSION = "unknown - No iPhone window"
                return
            
            GAME_VERSION = game_version
            print(f"Detected game version: {game_version}")
            if game_version.startswith('unknown'):
                print("Failed to identify game version - Unknown game type")
                return
        except Exception as e:
            print(f"Failed to identify game version: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            GAME_VERSION = f"unknown - Error: {str(e)}"
            return
        
        try:
            print(f"Capturing game board for {game_version}...")
            board = get_game_board(game_version, save_debug=SAVE_DEBUG_SCREENSHOTS)
        except Exception as e:
            print(f"Failed to capture game board: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            return

        if board:
            print("Game Board captured successfully!")
            
            START_TIME = time.time()
            signal.alarm(GAME_DURATION)
            print(f"Starting gameplay timer ({GAME_DURATION} seconds)...")
            
            if game_version == "WORD_BITES":
                print(board)
                print("Finding all Word Bites words first...")
                all_moves = list(find_word_bites_words(board))
                words_found = len(all_moves)
                WORDS_FOUND = words_found
                print(f"Found a total of {words_found} possible Word Bites words")
                
                print("Optimizing word order...")
                optimized_moves = optimize_word_order(all_moves)
                
                if REALISTIC_MODE:
                    optimized_moves = apply_realistic_mode_word_bites(optimized_moves)
                    moves_by_length = {}
                    for move in optimized_moves:
                        length = len(move.word)
                        if length not in moves_by_length:
                            moves_by_length[length] = []
                        moves_by_length[length].append(move)
                    
                    final_moves = []
                    
                    short_moves = []
                    for length in range(3, 5):
                        if length in moves_by_length and moves_by_length[length]:
                            num_to_take = max(1, int(len(moves_by_length[length]) * 0.4))
                            short_moves.extend(moves_by_length[length][:num_to_take])
                            moves_by_length[length] = moves_by_length[length][num_to_take:]
                    
                    random.shuffle(short_moves)
                    final_moves.extend(short_moves)
                    
                    medium_moves = []
                    for length in range(5, 7):
                        if length in moves_by_length and moves_by_length[length]:
                            num_to_take = max(1, int(len(moves_by_length[length]) * 0.3))
                            medium_moves.extend(moves_by_length[length][:num_to_take])
                            moves_by_length[length] = moves_by_length[length][num_to_take:]
                    
                    random.shuffle(medium_moves)
                    final_moves.extend(medium_moves)
                    
                    long_moves = []
                    for length in range(7, 15):
                        if length in moves_by_length and moves_by_length[length]:
                            num_to_take = max(1, int(len(moves_by_length[length]) * 0.5))
                            long_moves.extend(moves_by_length[length][:num_to_take])
                            moves_by_length[length] = moves_by_length[length][num_to_take:]
                    
                    random.shuffle(long_moves)
                    final_moves.extend(long_moves)
                    
                    remaining_moves = []
                    for length in sorted(moves_by_length.keys()):
                        remaining_moves.extend(moves_by_length[length])
                    
                    random.shuffle(remaining_moves)
                    final_moves.extend(remaining_moves)
                    
                    optimized_moves = final_moves
                    print(f"Reordered moves for more human-like play pattern")
                
                move_queue = []
                heap_lock = Lock()
                
                for move in optimized_moves:
                    with heap_lock:
                        heapq.heappush(move_queue, PrioritizedWordBitesMove(move))
                
                print("Starting to form words...")
                with heap_lock:
                    heapq.heappush(move_queue, PrioritizedWordBitesMove(WordBitesMove("", [], 0)))
                
                print("Executing all moves...")
                execute_word_bites_moves_from_heap(move_queue, heap_lock, board)
                
            elif game_version.startswith('ANAGRAM'):
                print(' '.join(board[0]))
                print("Finding anagrams...")
                found_words = find_anagrams(board, min_length=3)
                words_found = len(found_words)
                WORDS_FOUND = words_found
                
                print(f"Found {words_found} anagrams. Starting to click words...")
                if REALISTIC_MODE:
                    from word_finder import calculate_score
                    total_possible_score = calculate_score(found_words)
                    print(f"Total possible anagram score: {total_possible_score}")
                    
                    target_percentage = random.uniform(0.6, 0.8)
                    target_score = int(total_possible_score * target_percentage)
                    print(f"Target anagram score: {target_score} ({target_percentage*100:.1f}% of possible)")
                    
                    words_by_length = {}
                    for word in found_words:
                        length = len(word)
                        if length not in words_by_length:
                            words_by_length[length] = []
                        words_by_length[length].append(word)
                    
                    for length in words_by_length:
                        random.shuffle(words_by_length[length])
                    
                    selected_words = []
                    current_score = 0
                    
                    word_scores = {}
                    for word in found_words:
                        length = len(word)
                        word_scores[word] = WORD_SCORES.get(length, 400 * (length - 2))
                    
                    related_words = {}
                    for word in found_words:
                        related_words[word] = []
                        for other_word in found_words:
                            if word != other_word:
                                if word in other_word or other_word in word:
                                    related_words[word].append(other_word)
                                elif len(word) >= 3 and len(other_word) >= 3:
                                    prefix_len = min(len(word), len(other_word))
                                    if word[:prefix_len] == other_word[:prefix_len]:
                                        related_words[word].append(other_word)
                    
                    for length in sorted(words_by_length.keys()):
                        percentage = 0.7 if length <= 4 else (0.6 if length <= 6 else 0.5)
                        num_to_take = max(1, int(len(words_by_length[length]) * percentage))
                        
                        for word in words_by_length[length][:num_to_take]:
                            if current_score + word_scores[word] > target_score:
                                if current_score > target_score * 0.9:
                                    break
                                if random.random() > 0.3:
                                    continue
                            
                            selected_words.append(word)
                            current_score += word_scores[word]
                            
                            for related_word in related_words[word]:
                                if related_word not in selected_words and len(related_word) > len(word):
                                    if random.random() < 0.7:
                                        selected_words.append(related_word)
                                        current_score += word_scores[related_word]
                                        
                                        if current_score >= target_score:
                                            break
                            
                            if current_score >= target_score:
                                break
                    
                    print(f"Selected {len(selected_words)} anagram words with a total score of {current_score}")
                    print(f"Target was {target_score}, which is {current_score/target_score*100:.1f}% of target")
                    
                    length_distribution = {}
                    for word in selected_words:
                        length = len(word)
                        length_distribution[length] = length_distribution.get(length, 0) + 1
                    
                    print("Anagram word length distribution:")
                    for length in sorted(length_distribution.keys()):
                        print(f"{length} letters: {length_distribution[length]} words")
                    
                    play_order = []
                    
                    words_by_length = {}
                    for word in selected_words:
                        length = len(word)
                        if length not in words_by_length:
                            words_by_length[length] = []
                        words_by_length[length].append(word)
                    
                    short_words = []
                    for length in range(3, 5):
                        if length in words_by_length:
                            num_to_take = max(1, int(len(words_by_length[length]) * 0.4))
                            short_words.extend(words_by_length[length][:num_to_take])
                            words_by_length[length] = words_by_length[length][num_to_take:]
                    
                    random.shuffle(short_words)
                    play_order.extend(short_words)
                    
                    medium_words = []
                    for length in range(5, 7):
                        if length in words_by_length:
                            num_to_take = max(1, int(len(words_by_length[length]) * 0.3))
                            medium_words.extend(words_by_length[length][:num_to_take])
                            words_by_length[length] = words_by_length[length][num_to_take:]
                    
                    random.shuffle(medium_words)
                    play_order.extend(medium_words)
                    
                    long_words = []
                    for length in range(7, 15):
                        if length in words_by_length:
                            num_to_take = max(1, int(len(words_by_length[length]) * 0.5))
                            long_words.extend(words_by_length[length][:num_to_take])
                            words_by_length[length] = words_by_length[length][num_to_take:]
                    
                    random.shuffle(long_words)
                    play_order.extend(long_words)
                    
                    remaining_words = []
                    for length in sorted(words_by_length.keys()):
                        remaining_words.extend(words_by_length[length])
                    
                    random.shuffle(remaining_words)
                    play_order.extend(remaining_words)
                    
                    print(f"Reordered anagram words for more human-like play pattern")
                    sorted_words = play_order
                else:
                    sorted_words = sorted(found_words.keys(), key=lambda x: (-len(x), x))
                
                for i, word in enumerate(sorted_words):
                    if i % 10 == 0:
                        print(f"Processed {i}/{len(sorted_words)} words...")
                    click_anagram_word(word, board, game_version)
                    time.sleep(0.01)
                
                print_anagram_words({word: found_words[word] for word in sorted_words})
            else:
                for row in board:
                    print(' '.join(row))
                word_queue = []
                word_paths = {}
                heap_lock = Lock()
                
                all_words = {}
                
                print(f"Starting word hunt for {game_version}...")
                
                for word, path in find_words(board, game_version):
                    if word not in all_words:
                        all_words[word] = path
                
                if REALISTIC_MODE:
                    selected_words = apply_realistic_mode_word_hunt(all_words)
                else:
                    selected_words = all_words
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    draw_future = executor.submit(draw_words_from_heap, word_queue, heap_lock, game_version)
                    
                    if REALISTIC_MODE:
                        words_by_length = {}
                        for word in selected_words:
                            length = len(word)
                            if length not in words_by_length:
                                words_by_length[length] = []
                            words_by_length[length].append(word)
                        
                        short_words = []
                        for length in range(3, 5):
                            if length in words_by_length:
                                num_to_take = max(1, int(len(words_by_length[length]) * 0.4))
                                short_words.extend(words_by_length[length][:num_to_take])
                                words_by_length[length] = words_by_length[length][num_to_take:]
                        
                        random.shuffle(short_words)
                        
                        medium_words = []
                        for length in range(5, 7):
                            if length in words_by_length:
                                num_to_take = max(1, int(len(words_by_length[length]) * 0.3))
                                medium_words.extend(words_by_length[length][:num_to_take])
                                words_by_length[length] = words_by_length[length][num_to_take:]
                        
                        random.shuffle(medium_words)
                        
                        long_words = []
                        for length in range(7, 15):
                            if length in words_by_length:
                                num_to_take = max(1, int(len(words_by_length[length]) * 0.5))
                                long_words.extend(words_by_length[length][:num_to_take])
                                words_by_length[length] = words_by_length[length][num_to_take:]
                        
                        random.shuffle(long_words)
                        
                        remaining_words = []
                        for length in sorted(words_by_length.keys()):
                            remaining_words.extend(words_by_length[length])
                        
                        random.shuffle(remaining_words)
                        
                        play_order = short_words + medium_words + long_words + remaining_words
                        
                        for word in play_order:
                            path = selected_words[word]
                            word_paths[word] = path
                            words_found += 1
                            WORDS_FOUND = words_found
                            with heap_lock:
                                heapq.heappush(word_queue, PrioritizedWord(word, path))
                            
                            if words_found % 20 == 0:
                                print(f"Found {words_found} words so far...")
                    else:
                        for word, path in selected_words.items():
                            word_paths[word] = path
                            words_found += 1
                            WORDS_FOUND = words_found
                            with heap_lock:
                                heapq.heappush(word_queue, PrioritizedWord(word, path))
                            
                            if words_found % 20 == 0:
                                print(f"Found {words_found} words so far...")
                
                print(f"Found a total of {words_found} words. Starting to draw words...")
                with heap_lock:
                    heapq.heappush(word_queue, PrioritizedWord("", []))
                
                draw_future.result()
                
                print_found_words(word_paths)
            
            # Add a small delay before exiting to ensure all words are processed
            time.sleep(1)
            print("\nGame completed successfully!")
            os._exit(0)
            
        else:
            print("Failed to get game board - Board detection returned None")
            os._exit(1)
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        os._exit(0)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")
        os._exit(1)
    finally:
        signal.alarm(0)
        os._exit(0)  # Ensure we exit even if there's an error

def draw_words_from_heap(word_heap: List[PrioritizedWord], heap_lock: Lock, game_version: str) -> None:
    """Draw words as they become available in the heap, longest first"""
    while True:
        with heap_lock:
            if not word_heap:
                time.sleep(0.1)
                continue
            
            prioritized_word = heapq.heappop(word_heap)
        
        # Check for sentinel value
        if not prioritized_word.path:
            break
            
        # Draw the word directly
        draw_word(prioritized_word.path, game_version)

def execute_word_bites_moves_from_heap(move_heap: List[PrioritizedWordBitesMove], heap_lock: Lock, board) -> None:
    """Execute Word Bites moves as they become available in the heap, highest score first"""
    # Keep track of the last successfully formed word and its block positions
    last_word = None
    last_word_blocks = {}  # Maps position -> block
    
    # Stats tracking
    vertical_words_count = 0
    horizontal_words_count = 0
    total_score = 0
    
    # Process counter for progress reporting
    processed_count = 0
    total_moves = len(move_heap) - 1  # Subtract 1 for sentinel
    
    while True:
        with heap_lock:
            if not move_heap:
                time.sleep(0.05)  # Reduced sleep time
                continue
            
            prioritized_move = heapq.heappop(move_heap)
        
        # Check for sentinel value
        if not prioritized_move.move.word:
            # Print final stats before exiting
            print(f"\nWord Bites stats:")
            print(f"Vertical words: {vertical_words_count}")
            print(f"Horizontal words: {horizontal_words_count}")
            print(f"Total score: {total_score}")
            break
        
        move = prioritized_move.move
        processed_count += 1
        
        # Only log every 5th word to reduce console output overhead
        if processed_count % 10 == 0 or processed_count == 1:
            orientation = "VERTICAL" if move.is_vertical else "HORIZONTAL"
            print(f"Playing word {processed_count}/{total_moves}: {move.word} ({move.score} pts) [{orientation}]")
        
        # Check if we can build upon the previous word
        if last_word and are_words_related(last_word, move.word):
            # Try to identify which blocks need to be added to form the new word
            if move.word.startswith(last_word):
                # The new word is an extension of the last word (e.g., "PLAY" -> "PLAYER")
                suffix = move.word[len(last_word):]
                
                # Create a modified move that only includes the new blocks needed
                modified_block_moves = []
                for block, target_pos in move.block_moves:
                    # Skip blocks that are already in position from the previous word
                    if target_pos not in last_word_blocks:
                        modified_block_moves.append((block, target_pos))
                
                if modified_block_moves:
                    # Create a new move with just the blocks we need to add
                    from word_finder import WordBitesMove
                    modified_move = WordBitesMove(move.word, modified_block_moves, move.score, move.is_vertical, move.block_moves)
                    success = execute_word_bites_move(modified_move, board, True)
                else:
                    # If no new blocks needed (shouldn't happen), use the original move
                    success = execute_word_bites_move(move, board, True)
            
            elif last_word.startswith(move.word):
                # The new word is a prefix of the last word (e.g., "PLAYER" -> "PLAY")
                # This is less common but possible
                success = True  # No need to do anything, the word is already formed
            
            else:
                # The words are related but one is not a prefix of the other
                # (e.g., "PLAY" -> "PLAYING" where we need to remove 'Y' and add 'YING')
                success = execute_word_bites_move(move, board, True)
        else:
            # No previous word or words are not related, execute normally
            success = execute_word_bites_move(move, board, True)
        
        if success:
            # Update the last word and its block positions
            last_word = move.word
            last_word_blocks = {}
            for block, pos in move.block_moves:
                # Find the actual block at this position
                actual_block = board.get_block_at(pos[0], pos[1])
                if actual_block:
                    last_word_blocks[pos] = actual_block
            
            # Use a shorter delay between words
            time.sleep(0.01)  # Further reduced delay between words
            
            # Update stats
            if move.is_vertical:
                vertical_words_count += 1
            else:
                horizontal_words_count += 1
            total_score += move.score
        else:
            # If we fail to form a word, wait a bit before trying the next one
            time.sleep(0.01)  # Further reduced delay after failure
            # Reset last word tracking since we failed
            last_word = None
            last_word_blocks = {}

if __name__ == "__main__":
    main() 