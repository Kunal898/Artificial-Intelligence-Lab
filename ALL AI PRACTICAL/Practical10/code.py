import numpy as np

# Game Configuration
ROWS = 6
COLS = 7

def create_board():
    """Initializes a 6x7 board with zeros."""
    return np.zeros((ROWS, COLS))

def drop_piece(board, row, col, piece):
    """Places a piece (1 or 2) in the specified cell."""
    board[row][col] = piece

def is_valid_location(board, col):
    """Checks if the top row of a column is empty."""
    return board[ROWS-1][col] == 0

def get_next_open_row(board, col):
    """Finds the lowest empty row in a given column."""
    for r in range(ROWS):
        if board[r][col] == 0:
            return r

def print_board(board):
    """Prints the board flipped so row 0 is at the bottom."""
    print(np.flip(board, 0))

def winning_move(board, piece):
    """Checks all horizontal, vertical, and diagonal lines for 4-in-a-row."""
    # Check horizontal
    for c in range(COLS-3):
        for r in range(ROWS):
            if all(board[r][c+i] == piece for i in range(4)):
                return True

    # Check vertical
    for c in range(COLS):
        for r in range(ROWS-3):
            if all(board[r+i][c] == piece for i in range(4)):
                return True

    # Check positively sloped diagonals
    for c in range(COLS-3):
        for r in range(ROWS-3):
            if all(board[r+i][c+i] == piece for i in range(4)):
                return True

    # Check negatively sloped diagonals
    for c in range(COLS-3):
        for r in range(3, ROWS):
            if all(board[r-i][c+i] == piece for i in range(4)):
                return True

# Main Game Loop Logic
board = create_board()
game_over = False
turn = 0

while not game_over:
    # Player 1 Input
    if turn == 0:
        col = int(input("Player 1 Make your Selection (0-6):"))
        if is_valid_location(board, col):
            row = get_next_open_row(board, col)
            drop_piece(board, row, col, 1)
            if winning_move(board, 1):
                print("PLAYER 1 WINS!")
                game_over = True

    # Player 2 Input
    else:
        col = int(input("Player 2 Make your Selection (0-6):"))
        if is_valid_location(board, col):
            row = get_next_open_row(board, col)
            drop_piece(board, row, col, 2)
            if winning_move(board, 2):
                print("PLAYER 2 WINS!")
                game_over = True

    print_board(board)
    turn = (turn + 1) % 2
