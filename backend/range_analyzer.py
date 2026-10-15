"""Motor d'anàlisi de rangs: classifica cada combo del rival contra el board.

Classificació (jerarquia treys + subcategories estil Flopzilla):
  - Reavaluem el millor handcode amb una carta del board eliminada per detectar
    TRIPS (si en treure-la la categoria baixa a "parell") i per calcular projectes:
      * Flush Draw: 4 al color, encara no fet
      * OESD / Gutshot: 4 escales obertes / interiors (només flop&turn)
      * Backdoor FD / SD: 3 al color o 4 consecutives/gap per arribar-hi en 2 cartes
  - One Pair es desglossa comparant el rang de la parella amb els rangs del board:
      * Overpair: parella de butxaca per sobre de tot el board
      * Top/Second/Third/Bottom(Fourth/Fifth) Pair: la posició del rang emparellat
        dins dels rangs ordenats del board (top = més alt).
  - High Card es desglossa en "As Alt" (te un As que juga com a carta alta) i altres.
"""
from typing import List, Tuple, Dict, Set
from collections import Counter
from itertools import combinations
from treys import Card, Evaluator

_evaluator = Evaluator()


def evaluate_best(cards: List[str]) -> int:
    """Millor mà de 5 cartes sobre qualsevol combinació (flop/turn/river).

    Cas general: amb <5 cartes retorna la suma de valors (no és una mano
    vàlida; només s'usa per a comparacions internes de "downgrade")."""
    n = len(cards)
    if n == 5:
        return _evaluator.evaluate(cards[:2], cards[2:])
    if n < 5:
        # Valor sintètic alt (pitjor que qualsevol mà real) per a comparacions
        return 9_999_999
    return min(_evaluator.evaluate(list(c[:2]), list(c[2:]))
               for c in combinations(cards, 5))

RANKS_ORDER = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
RANK_VALUE = {r: i for i, r in enumerate(RANKS_ORDER)}  # 2->0 ... A->12


def _rank(card: str) -> str:
    return card[0]


def _suit(card: str) -> str:
    return card[1]


def get_available_deck(board_cards: List[str]) -> List[str]:
    """Baralla restant excloent les cartes del board."""
    all_cards = [Card.new(r + s) for r in "AKQJT98765432" for s in "shdc"]
    bs = {Card.new(c) for c in board_cards}
    return [c for c in all_cards if c not in bs]


# Classes de treys (get_rank_class): 0=Royal, 1=Straight Flush, 2=Quads, 3=Full House,
# 4=Flush, 5=Straight, 6=Trips, 7=Two Pair, 8=One Pair, 9=High Card.
CAT_NAMES = {
    0: ("SF", "Royal Flush / Straight Flush"),
    1: ("SF", "Royal Flush / Straight Flush"),
    2: ("QUADS", "Quads (Poker)"),
    3: ("FH", "Full House"),
    4: ("FLUSH", "Flush (Color)"),
    5: ("STRAIGHT", "Straight (Escala)"),
    6: ("TRIPS", "Trips (Three of a Kind)"),
    7: ("TWOPAIR", "Two Pair (Doble Parella)"),
    8: ("PAIR", "One Pair (Una Parella)"),
    9: ("HIGH", "High Card (Carta Alta)"),
}
CATEGORY_ORDER = ["SF", "QUADS", "FH", "FLUSH", "STRAIGHT", "TRIPS", "TWOPAIR",
                  "PAIR", "HIGH"]

PAIR_SUB_ORDER = ["OVERPAIR", "TOPPAIR", "SECONDPAIR", "THIRDPAIR",
                  "FOURTHPAIR", "BOTTOMPAIR"]
PAIR_SUB_NAMES = {
    "OVERPAIR": "Overpair",
    "TOPPAIR": "Top Pair",
    "SECONDPAIR": "Second Pair",
    "THIRDPAIR": "Third Pair",
    "FOURTHPAIR": "Fourth Pair",
    "BOTTOMPAIR": "Bottom / Low Pair",
}
DRAW_ORDER = ["FD", "OESD", "GUTSHOT", "BDFD", "BSD"]
DRAW_NAMES = {
    "FD": "Flush Draw",
    "OESD": "Open-Ended Straight Draw",
    "GUTSHOT": "Gutshot (Inside Draw)",
    "BDFD": "Backdoor Flush Draw",
    "BSD": "Backdoor Straight Draw",
}


def classify_pair_subtype(hole: Tuple[str, str], board: List[str]) -> str:
    """Subcategoria de One Pair: on és la parella respecte del board."""
    hole_ranks = {RANK_VALUE[_rank(c)] for c in hole}
    board_ranks_sorted = sorted({RANK_VALUE[_rank(c)] for c in board}, reverse=True)
    paired = [rv for rv in board_ranks_sorted if rv in hole_ranks]
    if not paired:
        # Parella de butxaca per sobre de tot el board (o board amb parella interna)
        if len(hole_ranks) == 1:
            hv = next(iter(hole_ranks))
            return "OVERPAIR" if hv > board_ranks_sorted[0] else "BOTTOMPAIR"
        return "HIGH"
    pos = board_ranks_sorted.index(paired[0])
    n = len(board_ranks_sorted)
    if n == 3:
        names = ["TOPPAIR", "SECONDPAIR", "THIRDPAIR"]
    elif n == 4:
        names = ["TOPPAIR", "SECONDPAIR", "THIRDPAIR", "BOTTOMPAIR"]
    else:
        names = ["TOPPAIR", "SECONDPAIR", "THIRDPAIR", "FOURTHPAIR", "BOTTOMPAIR"]
    # Si hi ha dues cartes del board del mateix rank (board parell) la posició ja
    # reflecteix l'ordre de rangs únics.
    return names[min(pos, len(names) - 1)]


def straight_draw_info(cards: List[str]) -> Tuple[bool, bool]:
    """Analitza els rangs presents: retorna (OESD, gutshot). Només 4 rangs distints
    formen part d'un possible 5; cal que NO hi hagi escala feta."""
    vals = sorted({RANK_VALUE[_rank(c)] for c in cards})
    has_5_consec = any(vals[i + 4] - vals[i] == 4 for i in range(len(vals) - 4)) if len(vals) >= 5 else False
    if has_5_consec:
        return False, False  # escala ja feta -> no és draw
    oesd = False
    gut = False
    # mirar totes les finestres de mida 5 amb exactament 4 rangs ocupats.
    # A més, per ser OESD real la carta que falta ha d'estar a un extrem ADJACENT
    # al bloc de 4 (si el forat és llunyà, només seria gutshot).
    for low in range(0, 12 - 5 + 1):
        window = set(range(low, low + 5))
        distinct_present = {v for v in vals if v in window}
        if len(distinct_present) == 4:
            missing = (window - distinct_present).pop()
            others = sorted(distinct_present)
            if missing == low or missing == low + 4:
                # obert només si els altres 4 són consecutius i l'extrem és contigu
                rest = [v for v in others if v != missing]
                contiguous_extreme = (missing == low and others[0] == low + 1) or \
                                     (missing == low + 4 and others[-1] == low + 3)
                if contiguous_extreme:
                    oesd = True
                else:
                    gut = True
            else:
                gut = True
    return oesd, gut


def is_real_trips(hole: Tuple[str, str], board: List[str]) -> bool:
    """True si la mano conté REALMENT tres cartes del mateix rang (trips), és a
    dir, existeix un rang amb freqüència >= 3 entre les 5-7 cartes.

    Evita falsos positius de la heurística "downgrade": p. ex. JTo vs T9x té
    class 8 (One Pair) i en treure el 2 del board sembla TRIPS (class 6), però
    només hi ha dues Tes -> és Top Pair, no Trips."""
    freq = Counter(_rank(c) for c in list(hole) + list(board))
    return any(v >= 3 for v in freq.values())


def analyze_combo(hole: Tuple[str, str], board: List[str]) -> Dict:
    """Retorna {cat, pair_sub, draws:set, high_sub} per a un combo vàlid."""
    hc = [Card.new(c) for c in hole]
    bc = [Card.new(c) for c in board]
    full = hc + bc
    ev = evaluate_best(full)
    cat_code = _evaluator.get_rank_class(ev)
    cat = CAT_NAMES[cat_code][0]

    # Correcció de classificació amb subgames (només quan hi ha mà de 5 cartes):
    #   * PAIR que realment té 3 cartes del mateix rang -> TRIPS
    #   * TWOPAIR on un dels parells n'és realment triple -> TRIPS o FH
    if len(full) >= 5 and cat == "PAIR" and is_real_trips(hole, board):
        cat = "TRIPS"
    elif len(full) >= 5 and cat == "TWOPAIR" and is_real_trips(hole, board):
        freq = Counter(_rank(c) for c in list(hole) + list(board))
        trips_ranks = sum(1 for v in freq.values() if v >= 3)
        cat = "FH" if trips_ranks >= 2 else "TRIPS"

    draws: Set[str] = set()
    pair_sub = ""
    high_sub = ""

    if cat == "PAIR":
        pair_sub = classify_pair_subtype(hole, board)
    if cat == "HIGH":
        board_vals = {RANK_VALUE[_rank(c)] for c in board}
        hole_vals = {RANK_VALUE[_rank(c)]: _rank(c) for c in hole}
        # La carta alta que JUGA és la més alta de les 7; si és una carta de butxaca
        # i és un As, comptem com a "As Alt".
        max_hole_val = max(hole_vals)
        if max_hole_val > max(board_vals) and hole_vals[max_hole_val] == "A":
            high_sub = "ACE"
        else:
            high_sub = "OTHER"

    # Projectes (només té sentit en flop/turn; al river no hi ha draws pendents)
    if len(board) < 5 and cat not in ("SF", "QUADS", "FH", "FLUSH", "STRAIGHT"):
        all_cards = list(hole) + list(board)   # cadenes, ex: "As","Kh"

        # Si la mà ja conté un carrer o color de 5 cartes *com a subgame* (p. ex.
        # AA vs KKQJTx fa straight amb el board i les dues alta restants), els
        # projectes queden ofegats per la mà feta: no se'n mostren.
        made_straight = made_flush = False
        if len(all_cards) >= 5:
            card_objs = [Card.new(c) for c in all_cards]
            for comb in combinations(card_objs, 5):
                k = _evaluator.get_rank_class(
                    _evaluator.evaluate(list(comb[:2]), list(comb[2:])))
                if k == 5:
                    made_straight = True
                elif k == 4:
                    made_flush = True
                if made_straight and made_flush:
                    break

        suits = Counter(_suit(c) for c in all_cards)
        max_suit_n = max(suits.values())
        flush_done = cat in ("FLUSH", "SF") or made_flush
        if max_suit_n == 4 and not flush_done:
            draws.add("FD")
        elif max_suit_n == 3 and not flush_done and len(board) == 3:
            # backdoor flush: només té sentit al flop (calen 2 cartes del mateix pal)
            draws.add("BDFD")
        oesd, gut = straight_draw_info(all_cards)
        if not made_straight:
            if oesd:
                draws.add("OESD")
            elif gut:
                draws.add("GUTSHOT")
            else:
                # backdoor straight: cal un bloc de 4 rangs consecutius (runner-runner)
                vals = sorted({RANK_VALUE[_rank(c)] for c in all_cards})
                vset = set(vals)
                for low in range(0, 9):
                    if {low, low + 1, low + 2, low + 3} <= vset or \
                       {low + 1, low + 2, low + 3, low + 4} <= vset:
                        draws.add("BSD")
                        break

    return {"cat": cat, "pair_sub": pair_sub, "high_sub": high_sub, "draws": draws}


def evaluate_range_distribution(range_combos: List[Tuple[str, str]],
                                board: List[str]) -> Dict:
    """Itera tots els combos del rang, exclou duplicats amb el board i calcula
    la distribució de categories, subparelles, high cards i draws."""
    board_set = set(board)
    warnings: List[str] = []
    valid: List[Tuple[str, str]] = []
    excluded = 0
    for combo in range_combos:
        if combo[0] in board_set or combo[1] in board_set:
            excluded += 1
        else:
            valid.append(combo)

    total = len(valid)
    cat_counts = Counter()
    pair_counts = Counter()
    high_counts = Counter()
    draw_counts = Counter()
    details = []

    for combo in valid:
        res = analyze_combo(combo, board)
        cat_counts[res["cat"]] += 1
        if res["cat"] == "PAIR" and res["pair_sub"]:
            pair_counts[res["pair_sub"]] += 1
        if res["cat"] == "HIGH" and res["high_sub"]:
            high_counts[res["high_sub"]] += 1
        for d in res["draws"]:
            draw_counts[d] += 1
        details.append({
            "combo": list(combo),
            "cat": res["cat"],
            "pair_sub": res["pair_sub"],
            "high_sub": res["high_sub"],
            "draws": sorted(res["draws"]),
        })

    def pct(n):
        return round(100.0 * n / total, 2) if total else 0.0

    categories = [{"key": k, "label": CAT_NAMES_k(k), "combos": cat_counts.get(k, 0),
                   "pct": pct(cat_counts.get(k, 0))}
                  for k in CATEGORY_ORDER if cat_counts.get(k, 0) > 0]
    pair_breakdown = [{"key": k, "label": PAIR_SUB_NAMES[k],
                       "combos": pair_counts.get(k, 0), "pct": pct(pair_counts.get(k, 0))}
                      for k in PAIR_SUB_ORDER if pair_counts.get(k, 0) > 0]
    high_breakdown = [
        {"key": "ACE", "label": "As Alt (Ace High)", "combos": high_counts.get("ACE", 0),
         "pct": pct(high_counts.get("ACE", 0))},
        {"key": "OTHER", "label": "Alta Carta (altres)", "combos": high_counts.get("OTHER", 0),
         "pct": pct(high_counts.get("OTHER", 0))},
    ] if cat_counts.get("HIGH", 0) > 0 else []
    draws = [{"key": k, "label": DRAW_NAMES[k], "combos": draw_counts.get(k, 0),
              "pct": pct(draw_counts.get(k, 0))}
             for k in DRAW_ORDER if draw_counts.get(k, 0) > 0]

    if excluded:
        warnings.append(f"{excluded} combos exclosos per cartes duplicades amb el board")

    return {
        "total_combos_grid": len(range_combos),
        "excluded_dupes": excluded,
        "valid_combos": total,
        "categories": categories,
        "pair_breakdown": pair_breakdown,
        "high_card_breakdown": high_breakdown,
        "draws": draws,
        "warnings": warnings,
        "combo_details": details,
    }


_LABEL_LOOKUP = {v[0]: v[1] for v in CAT_NAMES.values()}


def CAT_NAMES_k(k: str) -> str:
    return _LABEL_LOOKUP.get(k, k)
