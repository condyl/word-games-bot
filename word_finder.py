from typing import List, Set, Tuple

def load_word_lists() -> Set[str]:
    """Load the filtered Collins word list into a set of valid words."""
    all_words = set()
    
    try:
        with open('word_lists/collins-word-list-2019-filtered.txt', 'r', encoding='utf-8') as f:
            words = f.read().splitlines()
            all_words.update(w.upper() for w in words)  # Convert to uppercase
    except FileNotFoundError:
        raise FileNotFoundError("Could not find word list file. Please ensure 'word_lists/collins-word-list-2019-filtered.txt' exists.")
    
    return all_words

def get_neighbors(x: int, y: int, board_size: int) -> List[Tuple[int, int]]:
    """Get all valid neighboring positions (including diagonals)."""
    neighbors = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < board_size and 0 <= new_y < board_size:
                neighbors.append((new_x, new_y))
    return neighbors

def find_words(board: List[List[str]], min_length: int = 3):
    """
    Find all valid words in the game board.
    Returns a generator of tuples (word, path) as words are found.
    """
    valid_words = load_word_lists()
    board_size = len(board)
    
    def dfs(x: int, y: int, current_word: str, path: List[Tuple[int, int]], visited: Set[Tuple[int, int]]):
        # Add current letter to word (ensure uppercase for comparison)
        current_word += board[x][y].upper()
        
        # If word is long enough and valid, yield it
        if len(current_word) >= min_length and current_word in valid_words:
            yield (current_word, path.copy())
            
        # Explore neighbors
        for next_x, next_y in get_neighbors(x, y, board_size):
            if (next_x, next_y) not in visited:
                visited.add((next_x, next_y))
                path.append((next_x, next_y))
                yield from dfs(next_x, next_y, current_word, path, visited)
                path.pop()
                visited.remove((next_x, next_y))
    
    # Start DFS from each position on the board
    for x in range(board_size):
        for y in range(board_size):
            visited = {(x, y)}
            yield from dfs(x, y, "", [(x, y)], visited)

def calculate_score(words: dict[str, List[Tuple[int, int]]]) -> int:
    """Calculate total score based on word lengths."""
    score = 0
    for word in words:
        length = len(word)
        if length == 3:
            score += 100
        elif length == 4:
            score += 400
        elif length == 5:
            score += 800
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