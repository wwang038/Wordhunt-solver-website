

class Board:
    def __init__(self, grid_string: str, rows: int = None, cols: int = None):
        grid_string = grid_string.lower().strip().replace(" ", "")
        
        if rows is None or cols is None:
            grid_size = len(grid_string)
            if grid_size == 16:
                rows, cols = 4, 4
            elif grid_size == 25:
                rows, cols = 5, 5
            elif grid_size == 36:
                rows, cols = 6, 6
            else:
                import math
                sqrt = int(math.sqrt(grid_size))
                if sqrt * sqrt == grid_size:
                    rows, cols = sqrt, sqrt
                else:
                    raise ValueError(f"Cannot determine grid dimensions for {grid_size} letters")
        
        if len(grid_string) != rows * cols:
            raise ValueError(f"Grid string length ({len(grid_string)}) doesn't match dimensions ({rows}x{cols}={rows*cols})")
        
        self.rows = rows
        self.cols = cols
        self.grid = [[grid_string[i * cols + j] for j in range(cols)] for i in range(rows)]
    
    def get_letter(self, row: int, col: int) -> str:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None
    
    def get_neighbors(self, row: int, col: int) -> list:
        neighbors = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)
        ]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.rows and 0 <= new_col < self.cols:
                neighbors.append((new_row, new_col))
        
        return neighbors
    
    def get_all_positions(self) -> list:
        return [(i, j) for i in range(self.rows) for j in range(self.cols)]
    
    def __str__(self) -> str:
        return "\n".join(" ".join(row) for row in self.grid)
    
    def __repr__(self) -> str:
        return f"Board({self.rows}x{self.cols})"

