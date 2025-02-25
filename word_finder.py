from typing import List, Set, Tuple, Dict, Optional
from config import WORD_SCORES, WORD_LIST_PATH  # Add imports from config
from word_bites_board import WordBitesBoard, Block, BlockType
from dataclasses import dataclass
from copy import deepcopy

# Cache for prefix sets
_prefix_cache = {}

def get_prefix_set(valid_words):
    """Get or create prefix set for the given words."""
    cache_key = frozenset(valid_words)
    if cache_key not in _prefix_cache:
        prefixes = set()
        for word in valid_words:
            for i in range(1, len(word)):
                prefixes.add(word[:i])
        _prefix_cache[cache_key] = prefixes
    return _prefix_cache[cache_key]

def load_word_lists() -> Set[str]:
    """Load the filtered Collins word list into a set of valid words."""
    all_words = set()
    
    try:
        with open(WORD_LIST_PATH, 'r', encoding='utf-8') as f:  # Use path from config
            words = f.read().splitlines()
            all_words.update(w.upper() for w in words)  # Convert to uppercase
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find word list file. Please ensure '{WORD_LIST_PATH}' exists.")
    
    return all_words

def get_empty_cells(game_version: str) -> Set[Tuple[int, int]]:
    """Return set of coordinates for empty cells based on game version."""
    if game_version == "X":
        return {(2,0), (0,2), (4,2), (2,4)}
    elif game_version == "O":
        return {(0,0), (0,4), (2,2), (4,0), (4,4)}
    return set()

def get_neighbors(x: int, y: int, board_size: int, empty_cells: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Get all valid neighboring positions (including diagonals), excluding empty cells."""
    neighbors = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < board_size and 
                0 <= new_y < board_size and 
                (new_x, new_y) not in empty_cells):
                neighbors.append((new_x, new_y))
    return neighbors

def find_words(board: List[List[str]], game_version: str = "4x4", min_length: int = 3):
    """
    Find all valid words in the game board.
    Returns a generator of tuples (word, path) as words are found.
    """
    valid_words = load_word_lists()
    board_size = len(board)
    empty_cells = get_empty_cells(game_version)
    
    # Create prefix set for faster lookups
    prefixes = get_prefix_set(valid_words)
    
    def is_valid_prefix(word: str) -> bool:
        return word in prefixes or word in valid_words
    
    def dfs(x: int, y: int, current_word: str, path: List[Tuple[int, int]], visited: Set[Tuple[int, int]]):
        current_word += board[x][y].upper()
        
        # Early termination if this prefix isn't valid
        if not is_valid_prefix(current_word):
            return
        
        if len(current_word) >= min_length and current_word in valid_words:
            yield (current_word, path.copy())
        
        # Stop exploring if word is too long (longest possible word)
        if len(current_word) >= 15:  # Adjust this value based on your word list
            return
            
        # Get valid neighbors first to avoid unnecessary iterations
        neighbors = []
        for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < board_size and 
                0 <= new_y < board_size and 
                (new_x, new_y) not in empty_cells and 
                (new_x, new_y) not in visited):
                neighbors.append((new_x, new_y))
        
        # Explore valid neighbors
        for next_x, next_y in neighbors:
            visited.add((next_x, next_y))
            path.append((next_x, next_y))
            yield from dfs(next_x, next_y, current_word, path, visited)
            path.pop()
            visited.remove((next_x, next_y))
    
    # Start DFS from each non-empty position on the board
    for x in range(board_size):
        for y in range(board_size):
            if (x, y) not in empty_cells and board[x][y].strip():
                visited = {(x, y)}
                yield from dfs(x, y, "", [(x, y)], visited)

def calculate_score(words: dict[str, List[Tuple[int, int]]]) -> int:
    """Calculate total score based on word lengths."""
    score = 0
    for word in words:
        length = len(word)
        if length in WORD_SCORES:
            score += WORD_SCORES[length]
        else:
            score += 400 * (length - 2)  # Standard scoring formula for longer words
    return score

def print_found_words(words: dict[str, List[Tuple[int, int]]]):
    """Print found words sorted by length and alphabetically."""
    sorted_words = sorted(words.keys(), key=lambda x: (len(x), x))
    
    print("\nFound Words:")
    current_length = 0
    for word in sorted_words:
        if len(word) != current_length:
            current_length = len(word)
            print(f"\n{current_length} letters:")
        print(f"{word} {words[word]}")
    
    print(f"\nTotal words found: {len(words)}")
    print(f"Total score: {calculate_score(words)}")

def find_anagrams(board: List[List[str]], min_length: int = 3) -> dict[str, str]:
    """
    Find all valid words that can be made from the given letters.
    Args:
        board: Single-row grid of letters from get_game_board
        min_length: Minimum word length to consider
    Returns:
        Dictionary mapping found words to the letters used
    """
    valid_words = load_word_lists()
    
    # For anagrams, we expect a single row of letters
    if len(board) != 1:
        raise ValueError("Anagram board should be a single row of letters")
        
    # Convert board row to string of letters
    letters = ''.join(board[0]).replace(' ', '').upper()
    
    letter_counts = {}
    for letter in letters:
        letter_counts[letter] = letter_counts.get(letter, 0) + 1
    
    found_words = {}
    
    def can_make_word(word: str) -> bool:
        word_counts = {}
        for letter in word:
            word_counts[letter] = word_counts.get(letter, 0) + 1
            if word_counts[letter] > letter_counts.get(letter, 0):
                return False
        return True
    
    for word in valid_words:
        if len(word) >= min_length and len(word) <= len(letters):
            if can_make_word(word):
                found_words[word] = letters
    
    return found_words

def print_anagram_words(words: dict[str, str]):
    """Print found anagram words sorted by length and alphabetically."""
    sorted_words = sorted(words.keys(), key=lambda x: (len(x), x))
    
    print("\nFound Anagram Words:")
    current_length = 0
    for word in sorted_words:
        if len(word) != current_length:
            current_length = len(word)
            print(f"\n{current_length} letters:")
        print(word)
    
    print(f"\nTotal words found: {len(words)}")
    print(f"Total score: {calculate_score(words)}")

@dataclass
class WordBitesMove:
    """Represents a move in Word Bites - which blocks to move where to form a word"""
    word: str
    block_moves: List[Tuple[Block, Tuple[int, int]]]  # List of (block, target_position) pairs
    score: int = 0

    def __post_init__(self):
        # Calculate score based on word length
        length = len(self.word)
        if length in WORD_SCORES:
            self.score = WORD_SCORES[length]
        else:
            self.score = 400 * (length - 2)  # Standard scoring formula for longer words

def are_words_related(word1: str, word2: str) -> bool:
    """
    Check if two words are related (one is a derivative of the other).
    Words are considered related if:
    1. They are identical
    2. One word is a prefix of the other (e.g., "PLAY" and "PLAYER")
    3. They share a common stem (first 3-4 characters) without leading unrelated letters
    
    Examples of related words:
    - "think" and "thinks"
    - "think" and "thinker"
    - "run" and "running"
    - "play" and "player"
    
    The function ensures words don't have leading or trailing unrelated letters.
    For example, "UNTHINK" and "THINK" would not be considered related despite
    sharing a common stem, because "UNTHINK" has a leading "UN" that changes the meaning.
    """
    # Convert to uppercase for consistency
    word1 = word1.upper()
    word2 = word2.upper()
    
    # If words are identical, they're related
    if word1 == word2:
        return True
    
    # Check if one word is a prefix of the other
    if word1.startswith(word2) or word2.startswith(word1):
        return True
    
    # Check for common word stems
    # Get the first 3-4 characters as a potential stem
    min_length = min(len(word1), len(word2))
    if min_length >= 3:
        stem_length = min(4, min_length)
        # Only consider words related if they both start with the same stem
        # This prevents words with leading unrelated letters from being considered related
        if word1[:stem_length] == word2[:stem_length]:
            return True
    
    return False

def group_related_words(words_list: List[WordBitesMove]) -> List[List[WordBitesMove]]:
    """
    Group related words together so they can be played back-to-back.
    
    This function:
    1. Groups words that are related (share common stems or prefixes)
    2. Sorts words within each group by length (shortest to longest)
    3. Sorts groups by average points per word in the group (highest first)
    
    The resulting groups will be used by optimize_word_order to prioritize
    groups with higher average point value, maximizing gameplay efficiency.
    
    Returns:
        A list of lists, where each inner list contains related words.
    """
    if not words_list:
        return []
    
    # Create a copy of the list to avoid modifying the original
    remaining_words = words_list.copy()
    word_groups = []
    
    while remaining_words:
        # Start a new group with the first remaining word
        current_word = remaining_words[0]
        current_group = [current_word]
        remaining_words.remove(current_word)
        
        # Find all words related to the current group
        i = 0
        while i < len(remaining_words):
            # Check if this word is related to any word in the current group
            is_related = False
            for group_word in current_group:
                if are_words_related(group_word.word, remaining_words[i].word):
                    is_related = True
                    break
            
            if is_related:
                current_group.append(remaining_words[i])
                remaining_words.pop(i)
            else:
                i += 1
        
        # Sort words within the group by length (shortest to longest)
        current_group.sort(key=lambda m: (len(m.word), m.word))
        word_groups.append(current_group)
    
    # Sort groups by average points per word (highest first)
    word_groups.sort(key=lambda group: -sum(move.score for move in group) / len(group))
    
    return word_groups

def optimize_word_order(moves_list: List[WordBitesMove]) -> List[WordBitesMove]:
    """
    Optimize the order of words to prioritize high-scoring words first, then related words.
    
    This function will:
    1. Sort all words by their score (highest first)
    2. For words with similar scores (within a threshold), group related words together
    3. Sort words within each group by length (shortest to longest)
    4. Return a list with this optimized order, where:
       a. Highest scoring words come first
       b. Related words with similar scores are kept together
    
    This ensures that high-value words (e.g., a 2200-point word) are prioritized over
    groups of lower-scoring words, while still maintaining the efficiency of playing
    related words back-to-back when their scores are similar.
    """
    if not moves_list:
        return []
    
    # Define a threshold for considering scores "similar"
    # Words with scores within this threshold will be grouped if related
    SCORE_THRESHOLD = 400
    
    # First, sort all words by score (highest first)
    sorted_by_score = sorted(moves_list, key=lambda m: -m.score)
    
    # Group words with similar scores that are related
    result = []
    i = 0
    
    while i < len(sorted_by_score):
        current_word = sorted_by_score[i]
        current_score = current_word.score
        
        # Find all words with similar scores that are related to the current word
        related_group = [current_word]
        j = i + 1
        
        while j < len(sorted_by_score):
            next_word = sorted_by_score[j]
            
            # If the score difference is within the threshold and words are related
            if (current_score - next_word.score <= SCORE_THRESHOLD and 
                any(are_words_related(word.word, next_word.word) for word in related_group)):
                related_group.append(next_word)
                sorted_by_score.pop(j)
            else:
                j += 1
        
        # Sort words within the group by length (shortest to longest)
        # For words of the same length, sort alphabetically
        related_group.sort(key=lambda m: (len(m.word), m.word))
        
        # Add the group to the result
        result.extend(related_group)
        i += 1
    
    return result

def find_word_bites_words(board: WordBitesBoard, min_length: int = 3) -> List[WordBitesMove]:
    """
    Find all possible words that can be made in Word Bites by moving blocks around.
    Only keeps one combination per word (first one found) since points can only be earned once.
    Args:
        board: The Word Bites board
        min_length: Minimum word length to consider
    Returns:
        List of WordBitesMove objects describing how to form each word,
        optimized to group related words together
    """
    valid_words = load_word_lists()
    found_moves = {}  # Use dict to track unique words
    
    # Get all blocks and their letters
    blocks = board.blocks
    
    # Create a map of letters to blocks that contain them
    letter_to_blocks: Dict[str, List[Block]] = {}
    for block in blocks:
        for letter in block.letters:
            if letter not in letter_to_blocks:
                letter_to_blocks[letter] = []
            letter_to_blocks[letter].append(block)
    
    def can_place_blocks_horizontally(blocks_to_place: List[Block], row: int, start_col: int, board_copy: WordBitesBoard) -> bool:
        """Check if we can place the given blocks horizontally starting at the given position"""
        col = start_col
        for block in blocks_to_place:
            # Check if we can move the block to this position
            if not board_copy.is_valid_position(block, row, col):
                return False
            col += 1
        return True
    
    def try_form_word(word: str, row: int, start_col: int, board_copy: WordBitesBoard) -> Optional[List[Tuple[Block, Tuple[int, int]]]]:
        """Try to form a word at the given position by moving blocks"""
        moves = []
        col = start_col
        
        # First check if we have enough space for the word
        if start_col + len(word) > board_copy.COLS:
            return None
        
        # For each letter in the word
        i = 0
        while i < len(word):
            letter = word[i]
            # Find a block containing this letter that we haven't used yet
            available_blocks = [b for b in letter_to_blocks.get(letter, []) 
                              if not any(b == m[0] for m in moves)]
            
            if not available_blocks:
                return None  # Can't form word - missing required letter
                
            # Try each available block
            placed = False
            for block in available_blocks:
                target_pos = None
                
                # If it's a horizontal block
                if block.type == BlockType.HORIZONTAL:
                    # If this is the first letter of the block
                    if block.letters[0] == letter:
                        # Check if we have room for the second letter and it matches
                        if i + 1 < len(word) and block.letters[1] == word[i + 1]:
                            target_pos = (row, col)
                            # Check if both positions are valid
                            if (col + 1 < board_copy.COLS and 
                                board_copy.is_valid_position(block, row, col)):
                                moves.append((block, target_pos))
                                placed = True
                                i += 2  # Skip next letter since we used both letters
                                col += 2  # Skip next position
                                break
                    # If this is the second letter of the block
                    elif block.letters[1] == letter and i > 0 and block.letters[0] == word[i - 1]:
                        # We can only use this if the previous letter matches and wasn't placed yet
                        if not moves or moves[-1][0] != block:
                            target_pos = (row, col - 1)  # Position block one space left
                            if (col > 0 and 
                                board_copy.is_valid_position(block, row, col - 1)):
                                moves.append((block, target_pos))
                                placed = True
                                col += 1
                                break
                
                # If it's a vertical block
                elif block.type == BlockType.VERTICAL:
                    if block.letters[0] == letter:
                        target_pos = (row, col)
                        # Check if we have room below
                        if (row + 1 < board_copy.ROWS and 
                            board_copy.is_valid_position(block, row, col)):
                            moves.append((block, target_pos))
                            placed = True
                            col += 1
                            i += 1
                            break
                    elif block.letters[1] == letter:
                        target_pos = (row - 1, col)  # Place it one row up
                        # Check if we have room above
                        if (row > 0 and 
                            board_copy.is_valid_position(block, row - 1, col)):
                            moves.append((block, target_pos))
                            placed = True
                            col += 1
                            i += 1
                            break
                
                # Single block
                else:
                    target_pos = (row, col)
                    if board_copy.is_valid_position(block, row, col):
                        moves.append((block, target_pos))
                        placed = True
                        col += 1
                        i += 1
                        break
            
            if not placed:
                return None  # Couldn't place a block for this letter
            
            if i >= len(word):
                break
        
        return moves if len(moves) > 0 else None
    
    # Try forming words in each row
    for row in range(board.ROWS):
        # Try each starting position in the row
        for start_col in range(board.COLS):
            # Create a copy of the board for testing moves
            board_copy = deepcopy(board)
            
            # Try each valid word
            for word in valid_words:
                # Skip words that are too short, too long to fit, or already found
                if (len(word) < min_length or 
                    start_col + len(word) > board.COLS or
                    word in found_moves):  # Skip if we already found this word
                    continue
                
                # Try to form this word
                moves = try_form_word(word, row, start_col, board_copy)
                if moves:
                    # Only keep the first valid combination found for this word
                    found_moves[word] = WordBitesMove(word=word, block_moves=moves)
    
    # Convert dict to list
    moves_list = list(found_moves.values())
    
    # Optimize the order of words to prioritize related words
    return optimize_word_order(moves_list)

def print_word_bites_moves(moves: List[WordBitesMove]):
    """Print found Word Bites words sorted by length and alphabetically."""
    if not moves:
        print("\nNo valid words found")
        return
        
    print("\nFound Word Bites Words:")
    current_length = 0
    total_score = 0
    
    for move in moves:
        if len(move.word) != current_length:
            current_length = len(move.word)
            print(f"\n{current_length} letters:")
        
        # Print just the word and score
        print(f"{move.word} ({move.score} points)")
        total_score += move.score
    
    print(f"\nTotal words found: {len(moves)}")
    print(f"Total possible score: {total_score}")

def move_block(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
    """
    Move a block from one position to another.
    Returns True if successful, False if move is invalid.
    """
    block = self.get_block_at(from_row, from_col)
    if not block:
        return False
        
    if block.position != (from_row, from_col):
        return False
        
    # Remove from old positions first
    old_positions = block.get_all_positions()
    for old_row, old_col in old_positions:
        self.grid[old_row][old_col] = None
    self.blocks.remove(block)
        
    # Check if new position is valid
    new_block = block.move_to(to_row, to_col)
    new_positions = new_block.get_all_positions()
    
    # Verify all new positions are within bounds and empty
    for new_row, new_col in new_positions:
        if not (0 <= new_row < self.ROWS and 0 <= new_col < self.COLS):
            # Restore block to original position
            for pos_row, pos_col in old_positions:
                self.grid[pos_row][pos_col] = block
            self.blocks.append(block)
            return False
        if self.grid[new_row][new_col] is not None:
            # Restore block to original position
            for pos_row, pos_col in old_positions:
                self.grid[pos_row][pos_col] = block
            self.blocks.append(block)
            return False
    
    # Add to new positions
    for new_row, new_col in new_positions:
        self.grid[new_row][new_col] = new_block
    self.blocks.append(new_block)
        
    return True 