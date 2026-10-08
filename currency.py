from collections import defaultdict
from typing import Optional

currencies = [
    ["USD", "GBP", "10"],
    ["GBP", "CNY", "20"],
    ["MXD", "CND", ".1"],
    ["ABC", "CND", "44"],
]


def convert(
    from_curr: str, to_curr: str, currencies: list[list[str]]
) -> Optional[float]:
    keyed = defaultdict(list)
    for f, t, r in currencies:
        r = float(r)
        keyed[f].append((f, t, r))
        keyed[t].append((t, f, 1 / r))
    iter = from_curr
    final_rate = 1
    seen = set((iter,))
    while iter != to_curr:
        if iter not in keyed:
            return
        for link in keyed[iter]:
            if link[1] not in seen:
                iter = link[1]
                seen.add(iter)
                final_rate *= link[2]
                break
    return final_rate


assert convert("USD", "GBP", currencies) == 10
assert convert("USD", "CNY", currencies) == 10 * 20
assert convert("MXD", "ABC", currencies) == 0.1 * (1 / 44)
assert convert("bananah", "ABC", currencies) == None
