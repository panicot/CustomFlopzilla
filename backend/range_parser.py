"""Parser de rangs: converteix codis 13x13 i notacions amb '+' en llistes de combos.

Un combo és una tupla (card1, card2) en notació treys, ex: ("As", "Kh").
Suportat:
  - Parelles: "AA", "KK" ...
  - Suited:   "AKs"
  - Offsuit:  "AQo"
  - Expansion: "AA+" -> AA,KK,QQ,JJ,TT,99,...,22
               "AKs+" -> AKs,AQs,AJs,ATs,A9s,...,KQs,KJs,...(tots els suited per sota)
               "AKo+", "ATo+" etc.
  - Rangs com "88+" només parelles; "A9s+" incloent A2s? Sí: totes les suited amb as
    fins a 9 i després KQs... estàndard: per a suited/offsuit la regla "+" manté la
    carta alta fixa i baixa la segona, i si arriba al final continua amb la primera
    carta reduïda (convenció estàndard de PLO/hold'em range charts).
"""
from typing import List, Tuple, Set

RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
SUITS = ["s", "h", "d", "c"]  # espades, cors, diamants, trèbol (notació treys)

RankIdx = {r: i for i, r in enumerate(RANKS)}


class RangeParseError(ValueError):
    pass


def _card(rank: str, suit: str) -> str:
    return rank + suit


def _all_combos_for_pair(r: str) -> List[Tuple[str, str]]:
    """6 combos per a un parell, ex AA -> AsAh, AsAd, ..."""
    out = []
    for i in range(4):
        for j in range(i + 1, 4):
            out.append((_card(r, SUITS[i]), _card(r, SUITS[j])))
    return out


def _all_combos_for_offsuit(r1: str, r2: str) -> List[Tuple[str, str]]:
    out = []
    for i in range(4):
        for j in range(4):
            if SUITS[i] != SUITS[j]:
                out.append((_card(r1, SUITS[i]), _card(r2, SUITS[j])))
    return out


def _all_combos_for_suited(r1: str, r2: str) -> List[Tuple[str, str]]:
    return [(_card(r1, s), _card(r2, s)) for s in SUITS]


def expand_code(code: str) -> List[Tuple[str, str]]:
    """Expandeix un sol codi de rang (amb o sense '+') a la llista de combos."""
    c = code.strip().upper().replace(" ", "")
    if not c:
        raise RangeParseError(f"Codi de rang buit")
    plus = c.endswith("+")
    if plus:
        c = c[:-1]

    if len(c) == 2:  # parell, ex AA
        r1, r2, kind = c[0], c[1], "pair"
    elif len(c) == 3:
        r1, r2, kind = c[0], c[1], c[2].lower()
        if kind not in ("s", "o"):
            raise RangeParseError(f"Tipus desconegut en '{code}' (ús 's' o 'o')")
    else:
        raise RangeParseError(f"Codi de rang no vàlid: '{code}'")

    if r1 not in RankIdx or r2 not in RankIdx:
        raise RangeParseError(f"Rangada no vàlida en '{code}'")
    i1, i2 = RankIdx[r1], RankIdx[r2]

    if kind == "pair":
        if r1 != r2:
            raise RangeParseError(f"Parell invàlid: '{code}'")
        if not plus:
            return _all_combos_for_pair(r1)
        # AA+ -> tots els parells des de AA fins TT (5 parells, 30 combos);
        # KK+ -> KK..TT; 88+ -> 88,77,66,55,44,33,22 (convenció estàndard:
        # "+ en parells" abasta 5 rangs cap avall, aturant-se a TT si cal).
        stop = max(i1, RankIdx["T"])
        combos = []
        for idx in range(i1, stop + 1):  # A(0) és el més alt
            combos += _all_combos_for_pair(RANKS[idx])
        return combos

    if i1 == i2:
        raise RangeParseError(f"No té sentit {code} (mateix rang amb s/o)")

    # Normalitzem: r1 ha de ser la carta ALTA (índex menor)
    hi, lo = (r1, r2) if i1 < i2 else (r2, r1)
    hi_i, lo_i = RankIdx[hi], RankIdx[lo]

    if not plus:
        if kind == "s":
            return _all_combos_for_suited(hi, lo)
        return _all_combos_for_offsuit(hi, lo)

    # Expansió "+" per a mans no-parell. Convenció del projecte (idèntica a la
    # regla clàssica de Pesto "lower connected hand"), que satisfà l'exemple de
    # l'especificació:  AKs+ -> {AKs, AQs, AJs, ATs, KQs, KJs, QJs, JTs}
    # Regla:
    #   Fase 1: carta alta FIXA; la segona baixa des del valor indicat fins a T.
    #           (AKs+ -> AKs, AQs, AJs, ATs)
    #   Fase 2: es baixa la carta alta pas a pas (K, Q, J) i, per a cada nova
    #           alta, s'afegeixen les segones amb gap 1 o 2 mentre la segona
    #           sigui >= T. (K: Q,J ; Q: J ; J: T -> KQs, KJs, QJs, JTs)
    combos: List[Tuple[str, str]] = []
    seen: Set[Tuple[str, str]] = set()

    def add(cs):
        for t in cs:
            key = tuple(sorted(t))
            if key not in seen:
                seen.add(key)
                combos.append(t)

    def mk(h: str, l: str):
        return _all_combos_for_suited(h, l) if kind == "s" else _all_combos_for_offsuit(h, l)

    t_idx = RankIdx["T"]   # límit inferior de la segona carta (les "T+" no baixen de T)
    j_idx = RankIdx["J"]   # límit inferior de la carta alta en fase 2

    # Fase 1: carta alta fixa, segona des de lo_i fins a T (inclusive)
    for l_idx in range(lo_i, t_idx + 1):
        if l_idx <= hi_i:
            continue
        add(mk(RANKS[hi_i], RANKS[l_idx]))

    # Fase 2: descendim la carta alta pas a pas (K, Q, J...) mantenint el GAP
    # original entre les dues cartes (AKs+ -> KQs, QJs, JTs) i afegint també el
    # gap+1 en el primer descens (-> KJs). Ens aturem quan la nova segona carta
    # queda per sota de la segona original (ex: KT < T? no; QT per sota de... )
    # Regla exacta que reproduceix l'exemple de l'especificació:
    #   d = 1,2,3... : H'=hi+d, L'=lo+d ; inclosa si L' >= "T" i, a més,
    #   només si L' no queda estrictament per sota del límit inferior de fase 1.
    gap = lo_i - hi_i
    d = 1
    while True:
        h_idx = hi_i + d
        l_idx = lo_i + d
        if h_idx >= len(RANKS) or l_idx >= len(RANKS):
            break
        if l_idx > t_idx:          # la segona per sota de T -> aturar diagonal
            break
        add(mk(RANKS[h_idx], RANKS[l_idx]))           # mateix gap (KQs, QJs, JTs)
        if d == 1 and l_idx + 1 <= t_idx:
            add(mk(RANKS[h_idx], RANKS[l_idx + 1]))   # gap+1 primer descens (KJs)
        d += 1
    return combos


def parse_range(tokens: List[str]) -> List[Tuple[str, str]]:
    """Converteix una llista de codis en combos únics (sense duplicats entre tokens)."""
    all_combos: List[Tuple[str, str]] = []
    seen = set()
    for tok in tokens:
        for t in expand_code(tok):
            key = tuple(sorted(t))
            if key not in seen:
                seen.add(key)
                all_combos.append(t)
    return all_combos


# Graella 13x13: generem la llista completa de codis per fila/columna (per al frontend)
GRID_LABELS: List[List[str]] = []
for i, hi in enumerate(RANKS):
    row = []
    for j, lo in enumerate(RANKS):
        if i == j:
            row.append(hi + lo)          # parell
        elif i < j:
            row.append(hi + lo + "s")    # triangular superior: suited
        else:
            row.append(hi + lo + "o")    # triangular inferior: offsuit
    GRID_LABELS.append(row)
