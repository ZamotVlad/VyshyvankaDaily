"""Збирання SVG сорочки 2.0: тканина, об'єм, вишивка, комір із шиєю, шнурки."""

from html import escape

from . import geometry as G
from .colors import shade
from .shirt import Shirt
from .stitches import StitchWriter

W = G.W


def _sleeve_wrap(pid: str, content: str, clip: str = "sl") -> str:
    """Вміст у рамці лівого рукава + дзеркальна копія для правого."""
    inner = f'<g transform="{G.SLEEVE_MATRIX}">{content}</g>'
    return (
        f'<g clip-path="url(#{pid}{clip})">{inner}</g>'
        f'<g transform="translate({W:g} 0) scale(-1 1)"><g clip-path="url(#{pid}{clip})">{inner}</g></g>'
    )


def _both(svg: str) -> str:
    return svg + f'<g transform="translate({W:g} 0) scale(-1 1)">{svg}</g>'


def _defs(pid: str, linen: str) -> str:
    return (
        f'<filter id="{pid}tex" x="0" y="0" width="1" height="1"><feTurbulence type="fractalNoise" '
        f'baseFrequency="1 .6" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 .35  0 0 0 0 .28  '
        f'0 0 0 0 .2  0 0 0 .55 -.18"/><feComposite in2="SourceGraphic" operator="in"/></filter>'
        f'<pattern id="{pid}wv" width="1.9" height="1.9" patternUnits="userSpaceOnUse">'
        f'<rect width="1.9" height="1.9" fill="{linen}"/><rect width="1.9" height=".6" fill="{shade(linen, -0.05)}"/>'
        f'<rect width=".6" height="1.9" fill="{shade(linen, 0.3)}" opacity=".5"/></pattern>'
        f'<pattern id="{pid}gl" width="1.3" height="1.3" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">'
        f'<rect width="1.3" height="1.3" fill="#fff"/><rect width=".45" height="1.3" fill="#e4dfd6"/></pattern>'
        f'<linearGradient id="{pid}tor" x1="0" x2="1"><stop offset=".27" stop-color="#2a1d12" stop-opacity=".07"/>'
        f'<stop offset=".36" stop-color="#2a1d12" stop-opacity=".02"/><stop offset=".5" stop-color="#2a1d12" '
        f'stop-opacity="0"/><stop offset=".64" stop-color="#2a1d12" stop-opacity=".02"/><stop offset=".73" '
        f'stop-color="#2a1d12" stop-opacity=".07"/></linearGradient>'
        f'<linearGradient id="{pid}cyl" x1="0" x2="1"><stop offset="0" stop-color="#2a1d12" stop-opacity=".2"/>'
        f'<stop offset=".12" stop-color="#fff" stop-opacity=".2"/><stop offset=".32" stop-color="#fff" '
        f'stop-opacity="0"/><stop offset=".8" stop-color="#2a1d12" stop-opacity=".02"/><stop offset=".95" '
        f'stop-color="#2a1d12" stop-opacity=".04"/></linearGradient>'
        f'<linearGradient id="{pid}vt" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#fff" '
        f'stop-opacity=".1"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/><stop offset="1" '
        f'stop-color="#2a1d12" stop-opacity=".14"/></linearGradient>'
        f'<linearGradient id="{pid}cg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#fff" '
        f'stop-opacity=".22"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/><stop offset="1" '
        f'stop-color="#2a1d12" stop-opacity=".2"/></linearGradient>'
        f'<linearGradient id="{pid}nk" x1="0" x2="1"><stop offset="0" stop-color="#262626"/>'
        f'<stop offset=".15" stop-color="#4c4c4c"/><stop offset=".58" stop-color="#9d9d9d"/>'
        f'<stop offset=".85" stop-color="#666"/><stop offset="1" stop-color="#2e2e2e"/></linearGradient>'
        f'<linearGradient id="{pid}nf" gradientUnits="userSpaceOnUse" x1="0" x2="0" y1="{G.NECK_TOP:g}" '
        f'y2="{G.NECK_TOP + 22:g}"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="#fff"/></linearGradient>'
        f'<mask id="{pid}nm"><rect x="0" y="-10" width="{W:g}" height="140" fill="url(#{pid}nf)"/></mask>'
        f'<linearGradient id="{pid}nb" gradientUnits="userSpaceOnUse" x1="0" x2="0" y1="18" '
        f'y2="{G.V_TIP[1]:.1f}"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" '
        f'stop-color="#000" stop-opacity=".35"/></linearGradient>'
        f'<linearGradient id="{pid}fl" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#fff" '
        f'stop-opacity=".22"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/><stop offset="1" '
        f'stop-color="#2a1d12" stop-opacity=".12"/></linearGradient>'
        f'<clipPath id="{pid}b"><path d="{G.poly(G.BODY)}"/></clipPath>'
        f'<clipPath id="{pid}sl"><path d="{G.poly(G.SLEEVE)}"/></clipPath>'
        f'<clipPath id="{pid}cf"><path d="{G.poly(G.CUFF)}"/></clipPath>'
        f'<clipPath id="{pid}fc"><path d="{G.poly(G.FLAP)}"/></clipPath>'
        f'<filter id="{pid}bl" x="-.2" y="-.2" width="1.4" height="1.4"><feGaussianBlur stdDeviation="2.6"/></filter>'
        f'<filter id="{pid}sf" x="-.1" y="-.1" width="1.2" height="1.2"><feGaussianBlur stdDeviation=".7"/></filter>'
        f'<filter id="{pid}sh" x="-.1" y="-.1" width="1.2" height="1.25"><feDropShadow dx="0" dy="7" '
        f'stdDeviation="7" flood-color="#000" flood-opacity=".55"/></filter>'
        f'<filter id="{pid}em"><feDropShadow dx=".3" dy=".45" stdDeviation=".3" flood-color="#2a1d12" '
        f'flood-opacity=".45"/></filter>'
    )


def _volume(pid: str) -> tuple[str, str]:
    """Об'єм: світло на тулубі й рукавах, згини ліктя, збирання над манжетом."""
    body = [
        f'<rect width="{W:g}" height="430" fill="url(#{pid}tor)"/>'
        f'<rect width="{W:g}" height="430" fill="url(#{pid}vt)"/>'
    ]
    folds = []
    for y, a in ((150, -6), (175, 5), (205, -4)):
        folds.append(
            f'<path d="M-4,{y} q16,{a} 32,{a / 2:g} t32,{-a}" stroke="#3b2c1e" stroke-width="5" opacity=".09"/>'
            f'<path d="M-4,{y - 4} q16,{a} 32,{a / 2:g} t32,{-a}" stroke="#fff" stroke-width="4" opacity=".12"/>'
        )
    for i in range(13):
        x = 2 + i * 4.6
        folds.append(
            f'<path d="M{x:.1f},{G.SL_LEN - 22:g} q1.4,11 0,22" stroke="#3b2c1e" stroke-width="1.8" opacity=".22"/>'
            f'<path d="M{x + 2.4:.1f},{G.SL_LEN - 20:g} q1.4,10 0,19" stroke="#fff" stroke-width="1.3" opacity=".35"/>'
        )
    sleeve = (
        f'<rect x="-8" y="-30" width="82" height="{G.SL_LEN + 40:g}" fill="url(#{pid}cyl)"/>'
        f'<g filter="url(#{pid}bl)" fill="none">{"".join(folds)}</g>'
    )
    drape = []
    for x, y1, y2, a in ((160, 300, 408, 8), (286, 300, 408, -8), (196, 330, 408, 4)):
        h = y2 - y1
        drape.append(
            f'<path d="M{x},{y1} q{a},{h / 2:g} 0,{h}" stroke="#3b2c1e" stroke-width="8" opacity=".06"/>'
            f'<path d="M{x + 6},{y1 + 6} q{a},{h / 2:g} 0,{h - 8}" stroke="#fff" stroke-width="6" opacity=".1"/>'
        )
    body.append(f'<g filter="url(#{pid}bl)" fill="none">{"".join(drape)}</g>')
    return "".join(body), _sleeve_wrap(pid, sleeve)


def _seams(pid: str, linen: str) -> str:
    """Пройма без різкої лінії: лише м'який перехід світла."""
    d = G.polyline(G.SEAM)
    return _both(
        f'<g fill="none"><path d="{d}" transform="translate(-2.5 0)" stroke="#2a1d12" stroke-width="6" '
        f'opacity=".045" filter="url(#{pid}bl)"/><path d="{d}" transform="translate(2 0)" stroke="#fff" '
        f'stroke-width="4" opacity=".18" filter="url(#{pid}bl)"/>'
        f'<path d="{G.polyline(G.SEAM[:4])}" stroke="{shade(linen, -0.1)}" stroke-width=".5" opacity=".6"/></g>'
    )


def _ties(pid: str, color: str) -> str:
    """Шнурки з-під кінців коміра, вузол спереду, дві китиці."""
    dk = shade(color, -0.4)
    out = []
    for d in ("M218.4,59.2 C214.5,73 218,82 222,90", "M228.6,59.2 C232.5,73 229,82 225,90"):
        out.append(
            f'<path d="{d}" stroke="{dk}" stroke-width="1.8"/><path d="{d}" stroke="{color}" stroke-width="1.1"/>'
        )
    for dx, length in ((-5, 46), (5, 40)):
        x0, y0 = 223.5 + dx * 0.3, 94
        d = f"M{x0:g},{y0} C{x0 + dx * 0.6:g},{y0 + 8} {x0 + dx:g},{y0 + 14} {x0 + dx * 1.2:g},{y0 + 20}"
        out.append(
            f'<path d="{d}" stroke="{dk}" stroke-width="1.5"/><path d="{d}" stroke="{color}" stroke-width=".9"/>'
        )
        tx, ty = x0 + dx * 1.2, y0 + 20
        out.append(f'<ellipse cx="{tx:g}" cy="{ty + 1.5:g}" rx="2.6" ry="2.2" fill="{dk}"/>')
        strands = []
        for k in range(13):
            sx, ex = tx - 4 + k * 0.66, tx - 6.5 + k * 1.08
            col = color if k % 3 else shade(color, 0.3)
            strands.append(
                f'<path d="M{sx:.1f},{ty + 2:g} Q{(sx + ex) / 2:.1f},{ty + length * 0.25 + 6:g} '
                f'{ex:.1f},{ty + length * 0.4 + 6:g}" stroke="{col}" stroke-width=".9"/>'
            )
        out.append(
            f'<g opacity=".95">{"".join(strands)}</g>'
            f'<rect x="{tx - 3:g}" y="{ty + 3:g}" width="6" height="2" rx="1" fill="{dk}"/>'
        )
    out.append(
        f'<circle cx="223.9" cy="93.2" r="4" fill="#000" opacity=".25" filter="url(#{pid}bl)"/>'
        f'<circle cx="223.5" cy="92.4" r="3.7" fill="{dk}"/><circle cx="223.3" cy="92.1" r="3.2" fill="{color}"/>'
        f'<ellipse cx="222.3" cy="90.9" rx="1.3" ry=".9" fill="#fff" opacity=".35"/>'
    )
    return f'<g fill="none">{"".join(out)}</g>'


def _collar(pid: str, linen: str, flap_embroidery: str) -> str:
    d = G.poly(G.FLAP)
    one = (
        f'<path d="{G.poly(G.STAND)}" fill="url(#{pid}wv)"/>'
        f'<path d="{d}" transform="translate(1.6 2.8)" fill="#1b130c" opacity=".38" filter="url(#{pid}bl)"/>'
        f'<path d="{d}" fill="url(#{pid}wv)"/>'
        f'<g clip-path="url(#{pid}fc)"><g filter="url(#{pid}em)">{flap_embroidery}</g>'
        f'<path d="{d}" fill="url(#{pid}fl)"/></g>'
        f'<path d="{d}" fill="none" stroke="#fff" stroke-width=".9" opacity=".75"/>'
        f'<path d="{d}" fill="none" stroke="{shade(linen, -0.35)}" stroke-width=".4"/>'
        f'<path d="M{G.NECK_X + 0.5:g},26 Q{G.NECK_X + 2:g},47 206,54" stroke="#2a1d12" stroke-width="1.6" '
        f'fill="none" opacity=".2" filter="url(#{pid}bl)"/>'
    )
    return _both(one)


def render_shirt(shirt: Shirt, label: str) -> str:
    pid, ln = shirt.pid, shirt.linen
    writer = StitchWriter(pid, shirt.pal)
    body = writer.layer(shirt.layers["body"])
    sleeve = writer.layer(shirt.layers["sleeve"])
    cuff = writer.layer(shirt.layers["cuff"])
    flap = writer.layer(shirt.layers["flap"])
    vol_body, vol_sleeve = _volume(pid)
    tex = f'<rect x="-10" y="-10" width="{W + 20:g}" height="450" fill="#000" filter="url(#{pid}tex)" opacity=".42"/>'
    sleeves = f"{G.poly(G.SLEEVE)} {G.poly([G.mirror(p) for p in G.SLEEVE])}"
    cuffs = f"{G.poly(G.CUFF)} {G.poly([G.mirror(p) for p in G.CUFF])}"
    neck = G.neck_path()
    return (
        f'<svg viewBox="{G.VIEWBOX}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{escape(label)}">'
        f"<defs>{_defs(pid, ln)}{writer.knot_defs()}{''.join(writer.defs)}</defs>"
        f'<g filter="url(#{pid}sh)" fill="url(#{pid}wv)"><path d="{G.poly(G.BODY)}"/>'
        f'<path d="{sleeves}"/><path d="{cuffs}"/></g>'
        f'<g clip-path="url(#{pid}b)">{tex}<g filter="url(#{pid}em)">{body}</g></g>'
        f'<g filter="url(#{pid}em)">{_sleeve_wrap(pid, sleeve)}</g>'
        f'<g clip-path="url(#{pid}b)">{vol_body}</g>'
        f"{_sleeve_wrap(pid, tex)}{vol_sleeve}{_seams(pid, ln)}"
        f'<g clip-path="url(#{pid}cf)"><rect x="-10" y="370" width="{W + 20:g}" height="60" '
        f'fill="url(#{pid}wv)"/>{tex}</g>'
        f'<g filter="url(#{pid}em)">{_sleeve_wrap(pid, cuff, "cf")}</g>'
        f'<g clip-path="url(#{pid}cf)"><rect x="-10" y="370" width="{W + 20:g}" height="60" '
        f'fill="url(#{pid}cg)"/></g>'
        f'<path d="{G.polyline(G.OUTLINE)}" fill="none" stroke="{shade(ln, -0.36)}" stroke-width=".9" '
        f'stroke-linejoin="round"/>'
        f'<g mask="url(#{pid}nm)" filter="url(#{pid}sf)"><path d="{neck}" fill="url(#{pid}nk)"/>'
        f'<path d="{neck}" fill="url(#{pid}nb)"/></g>'
        f"{_ties(pid, shirt.tie)}{_collar(pid, ln, flap)}"
        f'<path d="{cuffs}" fill="none" stroke="{shade(ln, -0.36)}" stroke-width=".9"/>'
        f"</svg>"
    )
