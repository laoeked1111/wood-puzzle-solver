
"""
SAT solver for wooden tiling puzzle.
"""

from itertools import combinations
from pysat.solvers import Minisat22

class Grid:
    """
    Grid of available squares on the board.
    """
    def __init__(self, squares, tiles):
        assert isinstance(squares, set), AssertionError("Grid.squares must be a set.")
        assert len(squares) == sum(len(tile.squares) for tile in tiles), \
            AssertionError("Grid size must match number of squares in tiles.")

        self.squares = squares
        self.tiles = tiles

class Tile:
    """
    Individual tile placed on the Grid. 
    """
    def __init__(self, squares):
        self.squares = squares

def orientations(squares, allow_reflection=True):
    """
    All distinct rotations/reflections of a tile, each normalised so its
    top-left-most square is at (0, 0).
    """
    def normalise(s):
        min_r = min(r for r, _ in s)
        min_c = min(c for _, c in s)
        return frozenset((r - min_r, c - min_c) for r, c in s)

    seen = set()
    current = set(squares)
    for _ in range(2):
        for _ in range(4):
            seen.add(normalise(current))
            current = {(c, -r) for r, c in current}     # rotate cw
        if not allow_reflection:
            break
        current = {(r, -c) for r, c in current}         # reflect
    return seen

def placements(grid, allow_reflection=True):
    """
    [(tile_index, frozenset_of_board_cells)] for every legal placement.
    """
    out = []
    for i, tile in enumerate(grid.tiles):
        for shape in orientations(tile.squares, allow_reflection):
            for anchor_r, anchor_c in grid.squares:
                cells = frozenset(
                    (anchor_r + r, anchor_c + c) for r, c in shape
                )
                if cells <= grid.squares:
                    out.append((i, cells))
    return sorted(set(out), key=lambda p: (p[0], sorted(p[1])))

def to_cnf(grid, allow_reflection=True):
    """
    Exact-cover CNF. Returns (clauses, placements) where clauses is a list of
    lists of ints in DIMACS convention and var (k+1) means placements[k] is used.
    """
    places = placements(grid, allow_reflection)
    var = lambda k: k + 1

    by_tile = {}
    by_cell = {}
    for k, (tile_idx, cells) in enumerate(places):
        by_tile.setdefault(tile_idx, []).append(k)
        for cell in cells:
            by_cell.setdefault(cell, []).append(k)

    clauses = []
    for group in list(by_tile.values()) + list(by_cell.values()):
        clauses.append([var(k) for k in group])                       # at least one
        clauses += [[-var(a), -var(b)] for a, b in combinations(group, 2)]  # at most one
    return clauses, places

def solve_sat(grid, allow_reflection=True):
    """
    Solve with pysat. Returns [(tile_index, cells)] or None.
    """
    clauses, places = to_cnf(grid, allow_reflection)
    with Minisat22(bootstrap_with=clauses) as m:
        if not m.solve():
            return None
        model = set(m.get_model())
        return [places[k] for k in range(len(places)) if (k + 1) in model]

if __name__ == "__main__":

    # real life puzzle
    squares = {(r,c) for r in range(8) for c in range(8)}
    tile1 = Tile({(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)})
    tile2 = Tile({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)})
    tile3 = Tile({(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)})
    tile4 = Tile({(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)})
    tile5 = Tile({(0, 0), (0, 1), (1, 0), (2, 0), (3, 0), (3, 1)})
    tile6 = Tile({(0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1)})
    tile7 = Tile({(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)})
    tile8 = Tile({(0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (3, 1)})
    tile9 = Tile({(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)})
    tile10 = Tile({(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (3, 0)})
    tile11 = Tile({(0, 0), (0, 1), (1, 0), (2, 0), (3, 0), (4, 0)})

    grid = Grid(squares, [tile1, tile2, tile3, tile4, tile5, 
                          tile6, tile7, tile8, tile9, tile10, tile11])
    sol = solve_sat(grid, allow_reflection=True)

    board = {}
    for i, cells in sol:
        for cell in cells:
            board[cell] = "ABCDEFGHIJK"[i] # letters A-K for the tiles
    for r in range(min(r for r,_ in squares), max(r for r,_ in squares)+1):
        print(" | ".join(board.get((r,c), ".") 
                         for c in range(min(c for _,c in squares), max(c for _,c in squares)+1)))
