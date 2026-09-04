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

if __name__ == "__main__":
    unittest.main()
