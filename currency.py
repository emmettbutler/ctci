from collections import defaultdict
from typing import Optional

currencies = [
    ["USD", "GBP", "10"],
    ["GBP", "CNY", "20"],
    ["MXD", "CND", ".1"],
    ["ABC", "CND", "44"],
]

INDEX = None


def _build_index(
    currencies: list[list[str]],
) -> dict[str, list[tuple[str, str, float]]]:
    global INDEX
    if INDEX:
        return INDEX
    INDEX = defaultdict(list)
    for f, t, r in currencies:
        r = float(r)
        INDEX[f].append((f, t, r))
        INDEX[t].append((t, f, 1 / r))
    return INDEX


def convert(iter: str, to_curr: str, currencies: list[list[str]]) -> Optional[float]:
    keyed = _build_index(currencies)
    final_rate = 1
    seen = set((iter,))
    while iter != to_curr and iter in keyed:
        for _, link, r_mul in keyed[iter]:
            if link not in seen:
                iter = link
                seen.add(iter)
                final_rate *= r_mul
                break
    return final_rate if iter in keyed else None


assert convert("USD", "GBP", currencies) == 10
assert convert("USD", "CNY", currencies) == 10 * 20
assert convert("MXD", "ABC", currencies) == 0.1 * (1 / 44)
assert convert("bananah", "ABC", currencies) == None
