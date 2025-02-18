from get_game_board import get_game_board

def main():
    board = get_game_board()
    print(board)
    if board:
        print("\nGame Board:")
        for row in board:
            print(' '.join(row))
    else:
        print("Failed to get game board")

if __name__ == "__main__":
    main() 