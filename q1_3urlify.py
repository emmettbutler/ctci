def urlify(value, length):
    value = list(value)
    src_idx = length - 1
    dest_idx = len(value) - 1
    while src_idx >= 0 and dest_idx >= src_idx:
        if value[src_idx] != " ":
            value[dest_idx] = value[src_idx]
        else:
            value[dest_idx] = "0"
            value[dest_idx - 1] = "2"
            value[dest_idx - 2] = "%"
            dest_idx -= 2
        dest_idx -= 1
        src_idx -= 1
    return "".join(value)


if __name__ == "__main__":
    for s in (
        "a little string    ",
        "a longer string with some  space runs              ",
        "none",
    ):
        print(s, urlify(s, len(s.strip())))
