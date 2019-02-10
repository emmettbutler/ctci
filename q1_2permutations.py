from collections import defaultdict


def isPermutation(value1, value2):
    counts = defaultdict(lambda: defaultdict(int))
    for val in (value1, value2):
        for char in val:
            counts[val][char] += 1
    for char, count in counts[value1].items():
        if count != counts[value2][char]:
            return False
    return True


if __name__ == "__main__":
    for pair in [("abcdef", "abfedc"), ("ggg", "ggh"), ("taco cat", "attoca c")]:
        print(pair, isPermutation(pair[0], pair[1]))
