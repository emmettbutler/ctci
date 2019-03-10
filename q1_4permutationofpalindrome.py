import random

from collections import Counter


def isPermutationOfPalindrome(value):
    characters = Counter(value)
    isPermutation = len([v for v in characters.values() if v % 2 != 0]) <= 1
    if not isPermutation:
        return False, None

    # everything from here on was not included in CTCI 6th edition
    # but was requested in the problem definition

    if len(value) % 2 != 0:
        pivot = [k for k, v in characters.items() if v % 2 != 0][0]
    else:
        pivot = None

    examples = []
    for _ in range(5):
        example = []
        for k, v in characters.items():
            if v % 2 == 0:
                example.extend([k] * v)
            random.shuffle(example)
        if pivot:
            example.insert(len(value) / 2, pivot)
        examples.append("".join(example))
    return True, examples


if __name__ == "__main__":
    for s in ("aabbccdeeffgg", "abcdefgh", "tacocat", "emmett"):
        isPermutation, examples = isPermutationOfPalindrome(s)
        print(s, isPermutation)
        if isPermutation:
            print(examples)
