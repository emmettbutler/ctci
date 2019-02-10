def ringCoords(N, idxring):
    """Nastiest part of the attempt, and probably the reason that the solution is
    preferable. Generating an ordered sequence of the coordinates in a layer is hard to
    reduce to code simpler than this.
    """
    first = idxring
    last = N - idxring - 1
    for x in range(first, last):
        yield (x, first)
    for y in range(first, last):
        yield (last, y)
    for x in reversed(range(first + 1, last + 1)):
        yield (x, last)
    for y in reversed(range(first + 1, last + 1)):
        yield (first, y)


def rotateMatrixAttempt(matrix):
    """For each layer, generate an array representing the layer starting with the
    top-left and looping around the ring clockwise. Then, circularly walk this array
    starting from the new top-left position and write the values back to the original
    matrix

    O(n) where n is the number of cells in the matrix, or O(n^2) where n is the size of
    each dimension
    """
    for idxring in range(len(matrix) / 2):
        swap = []
        ringgen = ringCoords(len(matrix), idxring)
        for x, y in ringgen:
            swap.append(matrix[y][x])
        ringgen = ringCoords(len(matrix), idxring)
        start_idx = len(matrix) - 1 - idxring
        for swapidx in range(-1 * start_idx, len(swap) - start_idx):
            x, y = ringgen.next()
            matrix[y][x] = swap[swapidx]


def rotateMatrixSolution(matrix):
    """For each layer, for each position in the layer, do a four-part swap that moves
    the value at each position to the next position in order

    Same time complexity as attempt, but code is slightly cleaner as two straightforward
    nested loops. "offset" is identified as an abstract "position in side" independent
    from which side we're on, and all work for a given offset is done in the same loop
    iteration.
    """
    if len(matrix) == 0 or len(matrix) != len(matrix[0]):
        return False
    N = len(matrix)
    for layer in range(N / 2):
        first = layer
        last = N - 1 - layer
        for i in range(first, last):
            offset = i - first
            top = matrix[first][i]
            matrix[first][i] = matrix[last - offset][first]
            matrix[last - offset][first] = matrix[last][last - offset]
            matrix[last][last - offset] = matrix[i][last]
            matrix[i][last] = top


if __name__ == "__main__":
    in_matrix = [[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]]
    print(in_matrix)
    rotateMatrixAttempt(in_matrix)
    print(in_matrix)
    rotateMatrixSolution(in_matrix)
    print(in_matrix)
