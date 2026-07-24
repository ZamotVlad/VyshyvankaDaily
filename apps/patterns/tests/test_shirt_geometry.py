"""Тести геометрії вишиванки (Stage 5): реєстр кроїв, валідність
трасованого контуру (Shapely), зони на тканині, піксельний рендер (ADR 39)."""

import re
import sys

import pytest
from shapely.geometry import Polygon
from shapely.validation import explain_validity
from svgpathtools import parse_path

sys.path.insert(0, ".")
from apps.patterns.models import Motif, Region
from apps.patterns.services.pixel_motifs import (
    mirror_horizontal,
    render_grid_in_zone,
    validate_grid,
)
from apps.patterns.services.svg_render import (
    EMBROIDERY_ZONES,
    PLACKET_AXIS_X,
    PLACKET_SLIT,
    SHIRT_CUT_REGISTRY,
    SHIRT_OUTLINE,
    SHIRT_VIEWBOX,
    render_pattern_svg,
)

CUT = SHIRT_CUT_REGISTRY["standard"]


def subpath_polygon(subpath, samples_per_seg=8):
    pts = []
    for seg in subpath:
        for k in range(samples_per_seg):
            p = seg.point(k / samples_per_seg)
            pts.append((p.real, p.imag))
    return Polygon(pts)


class TestRegistry:
    def test_standard_cut_present_with_required_keys(self):
        required = {
            "viewbox",
            "body",
            "outline",
            "outline_fill",
            "embroidery_zones",
            "placket_axis_x",
            "placket_slit",
        }
        assert "standard" in SHIRT_CUT_REGISTRY
        assert required <= set(CUT)

    def test_module_aliases_point_to_standard_cut(self):
        assert SHIRT_VIEWBOX is CUT["viewbox"]
        assert SHIRT_OUTLINE is CUT["outline"]
        assert EMBROIDERY_ZONES is CUT["embroidery_zones"]


class TestOutlineGeometry:
    def test_outline_has_two_closed_subpaths(self):
        subs = parse_path(CUT["outline"]).continuous_subpaths()
        assert len(subs) == 2
        for sp in subs:
            assert sp.isclosed()

    @pytest.mark.parametrize("idx,name", [(0, "outer"), (1, "body")])
    def test_no_self_intersection(self, idx, name):
        sp = parse_path(CUT["outline"]).continuous_subpaths()[idx]
        poly = subpath_polygon(sp)
        assert poly.is_valid, f"{name}: {explain_validity(poly)}"

    def test_body_inside_outer_silhouette(self):
        subs = parse_path(CUT["outline"]).continuous_subpaths()
        outer, body = subpath_polygon(subs[0]), subpath_polygon(subs[1])
        assert outer.contains(body.representative_point())

    def test_outline_band_has_positive_area(self):
        subs = parse_path(CUT["outline"]).continuous_subpaths()
        band = subpath_polygon(subs[0]).symmetric_difference(subpath_polygon(subs[1]))
        assert band.area > 0


class TestZonesAndSlit:
    def test_zones_within_viewbox(self):
        _, _, w, h = (float(v) for v in CUT["viewbox"].split())
        for name, z in CUT["embroidery_zones"].items():
            assert 0 <= z["x"] and z["x"] + z["width"] <= w, name
            assert 0 <= z["y"] and z["y"] + z["height"] <= h, name

    def test_hem_zone_consciously_absent(self):
        # рішення Stage 5 (відхилення від 5 зон розділу 8.5 ТЗ) — див. DECISIONS.md
        assert "hem" not in CUT["embroidery_zones"]

    def test_zones_do_not_touch_gray_elements(self):
        """Комір — ПІД стійкою (низ стійки y=44), манжети — НАД смугами
        (верх смуг y=554): зони прилягають до сірого, не перетинаючись."""
        z = CUT["embroidery_zones"]
        assert z["collar"]["y"] >= 44
        assert z["placket"]["y"] >= z["collar"]["y"] + z["collar"]["height"]
        for cuff in ("cuff_left", "cuff_right"):
            assert z[cuff]["y"] + z[cuff]["height"] <= 554

    def test_slit_on_symmetry_axis_inside_placket(self):
        z = CUT["embroidery_zones"]["placket"]
        assert PLACKET_SLIT["x"] == PLACKET_AXIS_X
        assert z["x"] < PLACKET_SLIT["x"] < z["x"] + z["width"]
        assert PLACKET_SLIT["y1"] < PLACKET_SLIT["y2"]


class TestRender:
    PIXEL_DIAMOND = {
        "format": "pixel_grid_v1",
        "grid": [".#.", "#o#", ".#."],
        "palette": {"#": 0, "o": 1},
    }

    def _region(self):
        return Region(name="Тест", dominant_colors=["#111111", "#c00000"])

    def test_pixel_motifs_render_as_rects_under_outline(self):
        svg = render_pattern_svg(self._region(), [Motif(geometry_parameters=self.PIXEL_DIAMOND)])
        assert svg.count("<rect") > 0
        assert "<polygon" not in svg
        # мотиви ПІД контуром: перший rect раніше за контурний path
        assert svg.index("<rect") < svg.index('fill-rule="evenodd"')
        assert 'aria-label="Орнамент Тест"' in svg

    def test_render_is_byte_deterministic(self):
        args = (self._region(), [Motif(geometry_parameters=self.PIXEL_DIAMOND)])
        assert render_pattern_svg(*args) == render_pattern_svg(*args)

    def test_legacy_polygon_format_still_renders(self):
        legacy = Motif(
            geometry_parameters={
                "base_points": [[2.5, 0], [0, 2.5], [2.5, 5]],
                "symmetry": "reflection_vertical",
                "params": {},
            }
        )
        svg = render_pattern_svg(self._region(), [legacy])
        assert "<polygon" in svg

    def test_unknown_cut_raises_keyerror(self):
        with pytest.raises(KeyError):
            render_pattern_svg(self._region(), [], cut="hutsul")


class TestPixelGrid:
    def test_validate_grid_rejects_ragged_and_unknown_symbols(self):
        with pytest.raises(ValueError):
            validate_grid({"grid": ["##", "#"], "palette": {"#": 0}})
        with pytest.raises(ValueError):
            validate_grid({"grid": ["#x"], "palette": {"#": 0}})

    def test_mirror_horizontal_reverses_rows(self):
        assert mirror_horizontal(["#.o"]) == ["o.#"]

    def test_rects_stay_inside_zone(self):
        zone = {"x": 10, "y": 20, "width": 60, "height": 30}
        markup = render_grid_in_zone(
            {"grid": ["#o#", ".#."], "palette": {"#": 0, "o": 1}},
            zone,
            ["#000", "#c00"],
        )
        rect_re = r'<rect x="([0-9.]+)" y="([0-9.]+)" width="([0-9.]+)" height="([0-9.]+)"'
        matches = list(re.finditer(rect_re, markup))
        assert matches
        for m in matches:
            x, y, w, h = map(float, m.groups())
            assert zone["x"] - 0.01 <= x and x + w <= zone["x"] + zone["width"] + 0.01
            assert zone["y"] - 0.01 <= y and y + h <= zone["y"] + zone["height"] + 0.01
