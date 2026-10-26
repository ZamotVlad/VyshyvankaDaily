"""Регіональні заповнення (низь, ромбові сітки, заволікання), спільні для сорочок і плиток."""

from . import motifs as M


def nyz(r, c):
    """Вінницька чорна низь: ромби, «вибрані» тлом полотна."""
    y, x = r - 9, (c % 18) - 9
    d = abs(x) + abs(y)
    if abs(y) > 8:
        return None
    if d in (4, 8) or d < 2:
        return 2 if d < 2 else None
    return 0


def curly_vine(r, c):
    """Кучерява гілка: зигзаг стебла й завитки обабіч."""
    curl = M.curl()
    t = r % 14
    if c == 2 + (t if t < 7 else 14 - t) // 2:
        return 0
    rr = r % 28
    if 3 <= rr < 10 and 6 <= c < 13:
        return curl(rr - 3, c - 6)
    if 17 <= rr < 24 and 0 <= c < 7 and curl(rr - 17, 6 - c) is not None:
        return 0
    return None


def borsh(order=(2, 4, 3)):
    """Борщівська вовна: чорне тло з кольоровими ромбиками."""

    def cell(r, c):
        y, x = r % 12 - 6, c % 12 - 6
        d = abs(x) + abs(y)
        if d == 4:
            return order[(r // 12 + c // 12) % 3]
        return 4 if d == 0 else 0

    return cell


def lattice(r, c):
    """Черкаська ромбова сітка з зірками."""
    y, x = r % 18 - 9, c % 18 - 9
    d, ax, ay = abs(x) + abs(y), abs(x), abs(y)
    if d in (8, 9) or (d == 11 and (x + y) % 2 == 0):
        return 1
    if (ax <= 1 and ay <= 5) or (ay <= 1 and ax <= 5) or (abs(ax - ay) <= 1 and ax <= 3):
        return 1 if ax == ay == 0 else 0
    if d >= 13 and (ax == 9 or ay == 9):
        return 0
    return None


def squares(r, c):
    """Луганські кольорові квадрати."""
    tr, tc, y, x = r // 11, c // 11, r % 11 - 5, c % 11 - 5
    m = max(abs(y), abs(x))
    if m == 5:
        return 1
    if m in (4, 3):
        return 0 if (tr + tc) % 2 else 2
    if abs(x) + abs(y) <= 2:
        return 3 if (tr + tc) % 2 else 0
    return None


def zavolikannia(r, c):
    """Поліське заволікання: концентричні ромби, як ткані."""
    return 0 if (abs(c % 20 - 10) + abs(r % 20 - 10)) % 5 in (0, 1) else None


def saw(r, c):
    """Подільська сувора низь: зубчасті лінії."""
    y, v = r % 8, abs(c % 8 - 4) * 2
    if r // 8 % 2 == 0:
        return 0 if y >= v else None
    return 0 if y <= 7 - v else (2 if y == 7 and c % 8 == 4 else None)


def chevron(r, c):
    """Гуцульські шеврони пазухи."""
    if c in (0, 19):
        return 1
    v = (r + abs(c - 10)) % 8
    return 3 if v < 3 else (0 if v < 6 else (2 if v == 6 else None))


def kryv_rows(order=(0, 1, 2, 3, 0, 4)):
    """Закарпатські кольорові кривульки рядами."""

    def cell(r, c):
        if r % 5 == round(abs(c % 6 - 3) * 4 / 3):
            return order[r // 5 % len(order)]
        return None

    return cell
