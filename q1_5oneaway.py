def areOneAway(value1, value2):
    idx1 = idx2 = 0
    error_count = 0
    longer = None
    if len(value1) > len(value2):
        longer = 0
    elif len(value1) < len(value2):
        longer = 1
    while idx1 < len(value1) - 1:
        if value1[idx1] != value2[idx2]:
            if longer == 0:
                idx1 += 1
            if longer == 1:
                idx2 += 1
            error_count += 1
            if error_count > 1:
                return False
        else:
            idx1 += 1
            idx2 += 1
    return True


# key insight for the correct solution is that the pointer into the longer string should
# increment on every loop iteration
def areOneAwaySecondAttempt(value1, value2):
    if abs(len(value1) - len(value2)) > 1:
        return False
    has_errored = False
    idxLonger = 0
    idxShorter = 0
    if len(value1) > len(value2):
        longer = value1
        shorter = value2
    elif len(value1) <= len(value2):
        longer = value2
        shorter = value1
    while idxShorter < len(shorter):
        mismatched = longer[idxLonger] != shorter[idxShorter]
        if mismatched:
            if has_errored:
                return False
            has_errored = True
        if not mismatched or len(value1) == len(value2):
            idxShorter += 1
        idxLonger += 1
    return True


if __name__ == "__main__":
    for v1, v2 in [
        ("pez", "piez"),
        ("emmett", "emmettbb"),
        ("cat", "fat"),
        ("cart", "fact"),
        ("hello", "hell"),
    ]:
        print("%s, %s: %s" % (v1, v2, areOneAwaySecondAttempt(v1, v2)))
