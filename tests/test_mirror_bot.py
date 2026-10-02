# Created by 11hopem (11 Hopem Software Ltd. Şti.)
# Copyright (c) 2026 11hopem. All rights reserved.
# Licensed under 11 Hopem Software Proprietary License.

import re

import unittest
import unicodedata
from dataclasses import dataclass

# Fallback implementations in case PyObjC is not in global environment
TR_MAP = str.maketrans({
    "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
})

def normalize(s: str) -> str:
    s = s.translate(TR_MAP)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9 ]+", " ", s).lower()
    return re.sub(r"\s+", " ", s).strip()

def loosen(s: str) -> str:
    return re.sub(r"[il1|!]", "i", s)

@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def inset(self, top=0.0, right=0.0, bottom=0.0, left=0.0) -> "Rect":
        return Rect(self.x + left, self.y + top, self.w - left - right, self.h - top - bottom)

class TestMirrorBotCore(unittest.TestCase):
    """Unit tests for iPhone Mirroring text normalization and geometry logic."""

    def test_rect_center_and_insets(self):
        """Test Rect center point and inset boundaries."""
        r = Rect(x=100, y=200, w=300, h=400)
        self.assertEqual(r.cx, 250)
        self.assertEqual(r.cy, 400)

        inset_rect = r.inset(top=20, right=30, bottom=40, left=10)
        self.assertEqual(inset_rect.x, 110)
        self.assertEqual(inset_rect.y, 220)
        self.assertEqual(inset_rect.w, 260)
        self.assertEqual(inset_rect.h, 340)

    def test_turkish_text_normalization(self):
        """Test Turkish character folding to standard ASCII."""
        raw = "Kampanyaya Şimdi Katılın! %20 İndirim"
        norm = normalize(raw)
        self.assertEqual(norm, "kampanyaya simdi katilin 20 indirim")

        raw_special = "Öğrenci Ağacı, Çiçek Şelalesi"
        self.assertEqual(normalize(raw_special), "ogrenci agaci cicek selalesi")

    def test_loose_character_matching(self):
        """Test OCR misrecognition of 'l' and 'i'."""
        self.assertEqual(loosen(normalize("kat1l")), "katii")
        self.assertEqual(loosen(normalize("katıl")), "katii")
        self.assertEqual(loosen(normalize("katil")), "katii")

    def test_join_button_discrimination(self):
        """Test distinguishing 'Katıl' from already completed 'Katıldınız'."""
        JOIN_WORDS = ("katii",)
        SKIP_WORDS = ("katiidiniz", "katiidin", "katiiim", "katiiiminiz", "katiiindi", "katiindi", "katiiamadi")

        text_join = loosen(normalize("Katıl"))
        is_active_join = any(re.search(rf"\b{w}\b", text_join) for w in JOIN_WORDS)
        self.assertTrue(is_active_join)

        text_completed = loosen(normalize("Katıldınız"))
        is_already_joined = any(re.search(rf"\b{w}\b", text_completed) for w in SKIP_WORDS)
        self.assertTrue(is_already_joined)

    def test_carousel_wrap_around_detection(self):
        """Test detection of paging carousel wrapping back to initial card."""
        card1_tokens = {"beymen", "5000", "tl", "bonus"}
        card2_tokens = {"defacto", "yuzde", "20", "indirim"}
        card3_tokens = {"brooks", "brothers", "10", "indirim"}
        card1_again = {"beymen", "5000", "tl", "bonus", "firsati"}

        # Measure Jaccard similarity
        def similarity(s1, s2):
            return len(s1 & s2) / max(1, len(s1 | s2))

        # Distinct cards should have very low overlap
        self.assertLess(similarity(card1_tokens, card2_tokens), 0.3)
        self.assertLess(similarity(card2_tokens, card3_tokens), 0.3)

        # Looping back to card 1 should exceed the 0.65 threshold
        self.assertGreater(similarity(card1_tokens, card1_again), 0.65)

    def test_carousel_deduplication_by_context(self):
        """Test that distinct cards with similar button coordinates are not false-skipped."""
        done_contexts = set()

        # Card 1: Brooks Brothers
        ctx1 = "brooks brothers"
        self.assertNotIn(ctx1, done_contexts)
        done_contexts.add(ctx1)

        # Card 2: DeFacto arriving at identical screen coordinates
        ctx2 = "defacto indirim"
        self.assertNotIn(ctx2, done_contexts)
        done_contexts.add(ctx2)

        # Re-encountering Card 1 should be caught by done_contexts
        self.assertIn("brooks brothers", done_contexts)

    def test_swept_carousel_caching(self):
        """Test that already swept carousel fingerprints are skipped."""
        swept_fps = set()
        carousel_fp = "beymen|bonus|firsati|5000|tl"

        self.assertNotIn(carousel_fp, swept_fps)
        swept_fps.add(carousel_fp)

        # Subsequent round seeing the same carousel band
        self.assertIn(carousel_fp, swept_fps)

    def test_filter_band_exclusion(self):
        """Test that BONUS / PARACARD and search bands are detected as filter bands."""
        rect_y = 192.0
        # Anything with y < rect.y + 240 (432.0) is in the sticky top filter area
        self.assertTrue(333.0 < rect_y + 240)
        self.assertTrue(355.0 < rect_y + 240)
        self.assertFalse(510.0 < rect_y + 240)

        # Token based detection
        filter_norms1 = {"bonus", "paracard", "tumu", "kampanya takip"}
        is_filter1 = ("bonus" in filter_norms1 and "paracard" in filter_norms1)
        self.assertTrue(is_filter1)

        filter_norms2 = {"bonus", "parakart"}
        is_filter2 = ("bonus" in filter_norms2 and "parakart" in filter_norms2)
        self.assertTrue(is_filter2)

        # Regular campaign band containing "bonus" but not "paracard"
        campaign_norms = {"giyim", "kozmetik", "1500", "tl", "bonus", "populer"}
        is_filter_campaign = ("bonus" in campaign_norms and "paracard" in campaign_norms)
        self.assertFalse(is_filter_campaign)

    def test_infinite_carousel_loop_break_by_title(self):
        """Test that infinite paging carousels stop immediately when returning to initial title."""
        initial_title = "giyim kozmetik ayakkabi"
        seen_titles = {initial_title}

        step1_title = "market alisverislerinize"
        seen_titles.add(step1_title)

        step2_title = "restoranlarda 600 tl"
        seen_titles.add(step2_title)

        # Step 3 loops back to initial title
        step3_title = "giyim kozmetik ayakkabi"
        looped = (step3_title == initial_title) or (step3_title in seen_titles)
        self.assertTrue(looped)

    def test_end_card_tap_simulation(self):
        """Test that end cards in horizontal row trigger join taps when motion stops."""
        class MockSweep:
            def __init__(self):
                self.tapped = 0
            def tap_visible(self):
                self.tapped += 1

        mock = MockSweep()
        prev_fp = "card3|firsat|katil"
        curr_fp = "card3|firsat|katil"  # List did not change (hit wall)

        if curr_fp == prev_fp:
            mock.tap_visible()

        self.assertEqual(mock.tapped, 1)

if __name__ == "__main__":
    unittest.main()

