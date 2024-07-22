# Global Constants for ANSI escape sequences
CURSOR_UP_ONE = '\033[F'
ERASE_LINE = '\033[K'

# Function to update a line in the terminal
def update_line(message):
    """
    Updates the last line in the terminal with the given message.
    """
    print(f"{CURSOR_UP_ONE}{ERASE_LINE}{message}", end='\n', flush=True)

def delete_lines(n: int):
    """
    Deletes the last n lines in the terminal.
    """
    for _ in range(n):
        print(f"{CURSOR_UP_ONE}{ERASE_LINE}", end='\r', flush=True)