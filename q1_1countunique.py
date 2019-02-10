def containsUniqueChars(value):
    found = dict()
    for c in value:
        if c not in found:
            found[c] = True
        else:
            return False
    return True


if __name__ == "__main__":
    for s in ("aaaaa", "abstract", "abcdef"):
        print(s, containsUniqueChars(s))
