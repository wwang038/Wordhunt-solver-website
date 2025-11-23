from backend import Board, TrieMap

class Solver:
    
    def __init__(self, dictionary: TrieMap):
        self.dictionary = dictionary
        self.found_words: set[str] = set()
    
    def solve(self, board: Board) -> list[tuple[str, int]]:
        self.found_words.clear()
        
        for row in range(board.rows):
            for col in range(board.cols):
                visited = set()
                current_path = []
                self._dfs(board, row, col, visited, current_path, "")
        
        words_with_scores = [(word, self._calculate_score(word)) for word in self.found_words]
        
        words_with_scores.sort(key=lambda x: (-x[1], x[0]))
        
        return words_with_scores
    
    def _dfs(self, board: Board, row: int, col: int, visited: set[tuple[int, int]], 
             current_path: list[tuple[int, int]], current_word: str) -> None:
        letter = board.get_letter(row, col)
        if letter is None or (row, col) in visited:
            return
        
        current_word += letter
        visited.add((row, col))
        current_path.append((row, col))
        
        if not self.dictionary.starts_with(current_word):
            visited.remove((row, col))
            current_path.pop()
            return
        
        if len(current_word) >= 3 and self.dictionary.search(current_word):
            self.found_words.add(current_word)
        
        neighbors = board.get_neighbors(row, col)
        for new_row, new_col in neighbors:
            if (new_row, new_col) not in visited:
                self._dfs(board, new_row, new_col, visited, current_path, current_word)
        
        visited.remove((row, col))
        current_path.pop()
    
    def _calculate_score(self, word: str) -> int:
        length = len(word)
        
        if length == 3:
            return 100
        if length > 3 and length < 6:
            return (length - 3) * 400
        return (length - 3) * 400 + 200

    def get_total_score(self, found_words: list[tuple[str, int]]) -> int:
        return sum(score for _, score in found_words)

def load_dictionary(dictionary_path: str | None = None) -> TrieMap:
    trie = TrieMap()
    
    if dictionary_path:
        trie.load_from_file(dictionary_path)
    else:

        trie.load_from_file("backend/dictionary.txt")
    
    return trie

# Console solver for the command line
# Testing purposes only
def console_solver():
    dictionary = load_dictionary()

    
    print("\nEnter the letter grid (left-to-right, top-to-bottom):")
    print("Example for 4x4: abcdefghijklmnop")
    grid_string = input().strip()
    
    if not grid_string:
        print("Error: No input provided")
        return
    
    try:
        board = Board(grid_string)
        print(board)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    solver = Solver(dictionary)
    results = solver.solve(board)
    
    print(f"\nWords found: {len(results)}")
    print("-" * 50)
    for i, (word, score) in enumerate(results, 1):
        print(f"{i}. {word} ({score})")

def web_solver(input_grid: str) -> tuple[list[tuple[str, int]], int]:

    dictionary = load_dictionary()
    board = Board(input_grid)
    solver = Solver(dictionary)
    results = solver.solve(board)
    total_score = solver.get_total_score(results)
    return results, total_score

if __name__ == "__main__":
    console_solver()

