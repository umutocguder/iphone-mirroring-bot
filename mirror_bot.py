#!/usr/bin/env python3
"""iPhone Mirroring penceresindeki kampanya kartlarını gezip 'Katıl' butonlarına dokunan bot.

Ekran okuma  : screencapture (bölge) + macOS Vision OCR (tr-TR)
Girdi üretme : CoreGraphics event'leri (tık / scroll / swipe)

    ./mirror_bot.py windows
    ./mirror_bot.py calibrate
    ./mirror_bot.py run --dry-run
    ./mirror_bot.py run --mode list --max-taps 30
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import Quartz
import Vision
from AppKit import NSApplicationActivateIgnoringOtherApps, NSWorkspace
from Foundation import NSURL

APP_NAMES = ("iPhone Mirroring", "iPhone Yansıtma", "iPhone Aynalama")
RUN_DIR = Path.home() / ".cache" / "mirror-bot"
STOP_FILE = RUN_DIR / "STOP"

SESSION_ENDED_WORDS = ("iphone in use", "lock your iphone", "mirroring ended",
                       "iphone kullanimda", "iphone unuzu kilitleyin", "yansitma sona erdi",
                       "unlock your iphone", "iphone unuzun kilidini")
UNLOCK_WORDS = ("unlock your iphone", "iphone unuzun kilidini")
CONNECT_WORDS = ("connect", "baglan")

JOIN_WORDS = ("katii",)
SKIP_WORDS = ("katiidiniz", "katiidin", "katiiim", "katiindi", "katiiamadi")


# ---------------------------------------------------------------- yardımcılar

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


@dataclass
class TextBox:
    text: str
    conf: float
    rect: Rect

    @property
    def norm(self) -> str:
        return normalize(self.text)

    @property
    def loose(self) -> str:
        return loosen(self.norm)


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


def is_join(tb: TextBox, extra: re.Pattern | None, max_chars: int = 24) -> bool:
    if len(tb.text.strip()) > max_chars:
        return False
    loose = tb.loose
    if any(re.search(rf"\b{w}\b", loose) for w in SKIP_WORDS):
        return False
    if any(re.search(rf"\b{w}\b", loose) for w in JOIN_WORDS):
        return True
    return bool(extra and extra.search(tb.norm))


def png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


# ------------------------------------------------------------------- pencere

SKIP_WINDOW_NAMES = ("welcome", "hos geldin", "hosgeldin")


def list_windows(onscreen_only: bool = True) -> list[dict]:
    opts = Quartz.kCGWindowListExcludeDesktopElements
    opts |= Quartz.kCGWindowListOptionOnScreenOnly if onscreen_only else Quartz.kCGWindowListOptionAll
    return list(Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID) or [])


def mirror_windows(onscreen_only: bool = True) -> list[tuple[Rect, str, str]]:
    out = []
    for w in list_windows(onscreen_only):
        owner = str(w.get("kCGWindowOwnerName", ""))
        if owner not in APP_NAMES:
            continue
        name = str(w.get("kCGWindowName", "") or "")
        b = w.get("kCGWindowBounds") or {}
        rect = Rect(float(b.get("X", 0)), float(b.get("Y", 0)),
                    float(b.get("Width", 0)), float(b.get("Height", 0)))
        if rect.w < 200 or rect.h < 300:
            continue
        if any(s in normalize(name) for s in SKIP_WINDOW_NAMES):
            continue
        out.append((rect, owner, name))
    out.sort(key=lambda t: (t[2] not in APP_NAMES, -t[0].w * t[0].h))
    return out


def display_rects() -> list[Rect]:
    err, ids, count = Quartz.CGGetActiveDisplayList(16, None, None)
    out = []
    for d in list(ids)[:count]:
        b = Quartz.CGDisplayBounds(d)
        out.append(Rect(b.origin.x, b.origin.y, b.size.width, b.size.height))
    return out


def on_display(r: Rect, tol: float = 2.0) -> bool:
    """Pencere bir ekranın tamamen içinde mi (Space'ler arası park edilmiş değil mi)."""
    return any(r.x >= d.x - tol and r.y >= d.y - tol
               and r.x + r.w <= d.x + d.w + tol and r.y + r.h <= d.y + d.h + tol
               for d in display_rects())


def reposition_window(r: Rect) -> bool:
    """Pencere ekrandan taştıysa (swipe sırasında sürüklenmiş olabilir) içeri geri alır."""
    disp = display_rects()
    if not disp:
        return False
    d = disp[0]
    x = min(max(r.x, d.x + 8), d.x + d.w - r.w - 8)
    y = min(max(r.y, d.y + 33), d.y + d.h - r.h - 8)
    if abs(x - r.x) < 1 and abs(y - r.y) < 1:
        return False
    for name in APP_NAMES:
        rc = subprocess.run(
            ["osascript", "-e",
             f'tell application "System Events" to tell process "{name}" to '
             f'set position of (first window whose name is "{name}") to {{{int(x)}, {int(y)}}}'],
            capture_output=True)
        if rc.returncode == 0:
            print(f"pencere ekran içine alındı: ({int(x)},{int(y)})")
            time.sleep(0.5)
            return True
    return False


def find_mirror_window(activate: bool = False) -> tuple[Rect, str]:
    """Space'ler arasında park edilmiş (negatif koordinatlı) pencereyi de çözer."""
    cands = mirror_windows(False)
    visible = [c for c in cands if on_display(c[0])]
    for _ in range(3 if activate else 0):
        if visible:
            break
        activate_mirror()
        for rect, _, _ in cands:
            reposition_window(rect)
        time.sleep(0.6)
        cands = mirror_windows(False)
        visible = [c for c in cands if on_display(c[0])]
    if not visible:
        if cands:
            raise SystemExit(
                "iPhone Mirroring penceresi ekran dışında (başka Space veya simge durumunda).\n"
                "Pencereyi bu masaüstüne getirip tekrar deneyin.")
        if any(str(w.get("kCGWindowOwnerName", "")) in APP_NAMES for w in list_windows(False)):
            raise SystemExit(
                "iPhone Mirroring açık ama telefona bağlı değil "
                "(sadece karşılama penceresi görünüyor). Bağlanıp tekrar deneyin.")
        raise SystemExit("iPhone Mirroring penceresi bulunamadı. Uygulamayı açıp bağlanın.")
    rect, owner, _ = visible[0]
    return rect, owner


def occluders(rect: Rect) -> list[str]:
    """z-sırasında pencerenin önünde durup tarama alanını kapatan pencereler."""
    blockers = []
    for w in list_windows(True):
        if w.get("kCGWindowLayer") != 0:
            continue
        owner = str(w.get("kCGWindowOwnerName", ""))
        b = w.get("kCGWindowBounds") or {}
        r = Rect(float(b.get("X", 0)), float(b.get("Y", 0)),
                 float(b.get("Width", 0)), float(b.get("Height", 0)))
        hit = rect.x < r.x + r.w and rect.x + rect.w > r.x and \
            rect.y < r.y + r.h and rect.y + rect.h > r.y
        if owner in APP_NAMES:
            if hit:
                return blockers
            continue
        if hit:
            blockers.append(owner)
    return blockers


def frontmost_name() -> str:
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return str(app.localizedName()) if app else ""


def activate_mirror() -> None:
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if str(app.localizedName()) in APP_NAMES:
            app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            time.sleep(0.6)
            break
    if frontmost_name() in APP_NAMES:
        return
    for name in APP_NAMES:
        rc = subprocess.run(
            ["osascript", "-e",
             f'tell application "System Events" to tell process "{name}" to set frontmost to true'],
            capture_output=True)
        if rc.returncode == 0:
            time.sleep(0.6)
            return


# ------------------------------------------------------------- ekran + OCR

def capture(rect: Rect, path: Path) -> tuple[int, int, float]:
    region = f"{int(round(rect.x))},{int(round(rect.y))},{int(round(rect.w))},{int(round(rect.h))}"
    subprocess.run(["screencapture", "-x", "-R", region, "-t", "png", str(path)], check=True)
    iw, ih = png_size(path)
    return iw, ih, iw / rect.w


_vision_langs: list[str] | None = None


def vision_languages() -> list[str]:
    global _vision_langs
    if _vision_langs is None:
        req = Vision.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        supported, _ = req.supportedRecognitionLanguagesAndReturnError_(None)
        supported = [str(s) for s in (supported or [])]
        _vision_langs = [l for l in ("tr-TR", "en-US") if l in supported] or ["en-US"]
    return _vision_langs


def ocr(path: Path, rect: Rect, scale: float, min_conf: float = 0.25) -> list[TextBox]:
    iw, ih = png_size(path)
    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(
        NSURL.fileURLWithPath_(str(path)), None)
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    req.setRecognitionLanguages_(vision_languages())
    req.setUsesLanguageCorrection_(False)
    ok, err = handler.performRequests_error_([req], None)
    if not ok:
        raise RuntimeError(f"OCR hatası: {err}")

    boxes: list[TextBox] = []
    for obs in req.results() or []:
        cands = obs.topCandidates_(1)
        if not cands:
            continue
        cand = cands[0]
        conf = float(cand.confidence())
        if conf < min_conf:
            continue
        bb = obs.boundingBox()
        px = bb.origin.x * iw
        py = (1.0 - bb.origin.y - bb.size.height) * ih
        pw = bb.size.width * iw
        ph = bb.size.height * ih
        boxes.append(TextBox(
            text=str(cand.string()),
            conf=conf,
            rect=Rect(rect.x + px / scale, rect.y + py / scale, pw / scale, ph / scale),
        ))
    boxes.sort(key=lambda b: (b.rect.y, b.rect.x))
    return boxes


# ------------------------------------------------------------------- girdi

class Aborted(Exception):
    pass


def ensure_clear(rect: Rect) -> None:
    """Pencere kapandıysa bir kez öne almayı dener, olmuyorsa durdurur."""
    for i in range(8):
        blocked = occluders(rect)
        if not blocked:
            return
        if i == 2:
            print(f"    ↳ önde pencere var ({', '.join(sorted(set(blocked)))}), bekleniyor…")
        activate_mirror()
        time.sleep(1.0)
    blocked = occluders(rect)
    if blocked:
        raise Aborted(f"pencerenin önünde başka pencere var: {', '.join(sorted(set(blocked)))}")


class Input:
    def __init__(self, dry_run: bool, delay: float, guard: bool = True,
                 require_focus: bool = False, area: Rect | None = None):
        self.dry_run = dry_run
        self.delay = delay
        self.guard = guard
        self.require_focus = require_focus
        self.area = area
        self.last_pos: tuple[float, float] | None = None

    def cursor(self) -> tuple[float, float]:
        p = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
        return float(p.x), float(p.y)

    def check(self) -> None:
        if STOP_FILE.exists():
            raise Aborted(f"STOP dosyası bulundu: {STOP_FILE}")
        if self.require_focus and frontmost_name() not in APP_NAMES:
            raise Aborted(f"iPhone Mirroring ön planda değil (ön plan: {frontmost_name() or '?'})")
        if self.area is not None:
            ensure_clear(self.area)
        if self.guard and self.last_pos:
            x, y = self.cursor()
            dx, dy = abs(x - self.last_pos[0]), abs(y - self.last_pos[1])
            if dx > 40 or dy > 40:
                raise Aborted("fare kullanıcı tarafından oynatıldı")

    def _post(self, event) -> None:
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    def move(self, x: float, y: float) -> None:
        self._post(Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, (x, y), Quartz.kCGMouseButtonLeft))
        self.last_pos = (x, y)

    def click(self, x: float, y: float) -> None:
        self.check()
        if self.dry_run:
            self.move(x, y)
            return
        self.move(x, y)
        time.sleep(0.12)
        self._post(Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft))
        time.sleep(0.06)
        self._post(Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft))
        time.sleep(self.delay)

    def scroll(self, x: float, y: float, amount: int, steps: int = 8) -> None:
        self.check()
        self.move(x, y)
        time.sleep(0.1)
        per = int(amount / steps)
        for _ in range(steps):
            self._post(Quartz.CGEventCreateScrollWheelEvent(
                None, Quartz.kCGScrollEventUnitPixel, 1, per))
            time.sleep(0.03)
        time.sleep(self.delay)

    def hscroll(self, x: float, y: float, amount: int, steps: int = 6) -> None:
        self.check()
        self.move(x, y)
        time.sleep(0.1)
        per = int(amount / steps)
        for _ in range(steps):
            self._post(Quartz.CGEventCreateScrollWheelEvent(
                None, Quartz.kCGScrollEventUnitPixel, 2, 0, per))
            time.sleep(0.03)
        time.sleep(self.delay)

    def swipe(self, x1: float, y1: float, x2: float, y2: float, steps: int = 22) -> None:
        self.check()
        self.move(x1, y1)
        time.sleep(0.1)
        self._post(Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDown, (x1, y1), Quartz.kCGMouseButtonLeft))
        time.sleep(0.05)
        for i in range(1, steps + 1):
            t = i / steps
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            self._post(Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseDragged, (x, y), Quartz.kCGMouseButtonLeft))
            time.sleep(0.012)
        self._post(Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseUp, (x2, y2), Quartz.kCGMouseButtonLeft))
        self.last_pos = (x2, y2)
        time.sleep(self.delay)

    def require_mirror_focus(self, what: str) -> None:
        """Klavye girişi odaklı uygulamaya gider; yanlış pencereye yazmayı engeller."""
        if frontmost_name() in APP_NAMES:
            return
        activate_mirror()
        if frontmost_name() not in APP_NAMES:
            raise Aborted(
                f"{what} iptal: iPhone Mirroring ön planda değil "
                f"(ön plan: {frontmost_name() or '?'}). Yazı yanlış pencereye giderdi.")

    def type_text(self, text: str) -> None:
        self.check()
        self.require_mirror_focus("metin yazma")
        if self.dry_run:
            print(f"    [dry-run] metin yazılıyor: {text!r}")
            return
        escaped = text.replace('\\', '\\\\').replace('"', '\\"')
        cmd = f'tell application "System Events" to keystroke "{escaped}"'
        res = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"    ↳ UYARI: klavye girişi başarısız: {res.stderr.strip()}")
        time.sleep(0.4)

    def press_key(self, key_code: int = 36) -> None:
        self.check()
        self.require_mirror_focus("tuş basma")
        if self.dry_run:
            print(f"    [dry-run] tuşa basılıyor (kod {key_code})")
            return
        cmd = f'tell application "System Events" to key code {key_code}'
        res = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"    ↳ UYARI: tuş basımı başarısız: {res.stderr.strip()}")
        time.sleep(self.delay)


# -------------------------------------------------------------------- bot

class Bot:
    def __init__(self, args):
        self.args = args
        self.rect_full, self.owner = find_mirror_window(activate=True)
        self.rect = self.rect_full.inset(*self.insets())
        self.inp = Input(args.dry_run, args.delay, guard=not args.no_guard,
                         require_focus=args.require_focus, area=self.rect)
        self.session = RUN_DIR / time.strftime("%Y%m%d-%H%M%S")
        self.session.mkdir(parents=True, exist_ok=True)
        self.shot = self.session / "frame.png"
        self.taps = 0
        self.log: list[dict] = []
        self.extra = re.compile(args.match) if args.match else None
        self.popup_words = {normalize(w) for w in args.popup_ok.split(",") if w.strip()}
        self.tab_words = [normalize(w) for w in args.tab_words.split(",") if w.strip()]
        self.tab_sig: list[str] = []
        self.recent: list[tuple[str, float, float, float]] = []

    def insets(self) -> tuple[float, float, float, float]:
        """--inset verilmediyse pencere yüksekliğinden hesapla (uygulamadan bağımsız)."""
        if self.args.inset is not None:
            return self.args.inset
        h = self.rect_full.h
        return (h * 0.06, 0.0, h * 0.09, 0.0)

    def refresh_rect(self) -> None:
        self.rect_full, self.owner = find_mirror_window(activate=True)
        self.rect = self.rect_full.inset(*self.insets())
        self.inp.area = self.rect

    def look(self) -> list[TextBox]:
        self.refresh_rect()
        ensure_clear(self.rect)
        try:
            _, _, scale = capture(self.rect, self.shot)
        except subprocess.CalledProcessError:
            self.refresh_rect()
            _, _, scale = capture(self.rect, self.shot)
        return ocr(self.shot, self.rect, scale, self.args.min_conf)

    def fingerprint(self, boxes: list[TextBox]) -> str:
        return "|".join(sorted(b.norm for b in boxes if b.norm))

    def record(self, action: str, **kw) -> None:
        entry = {"t": round(time.time(), 3), "action": action, **kw}
        self.log.append(entry)
        with (self.session / "log.jsonl").open("a") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def look_full(self) -> list[TextBox]:
        self.refresh_rect()
        ensure_clear(self.rect_full)
        shot = self.session / "full.png"
        _, _, scale = capture(self.rect_full, shot)
        return ocr(shot, self.rect_full, scale, self.args.min_conf)

    def check_session(self) -> None:
        """Yansıtma 'iPhone kullanımda' diye sonlandıysa anlaşılır şekilde durur."""
        boxes = self.look_full()
        texts = [b.norm for b in boxes]
        if not any(w in t for w in SESSION_ENDED_WORDS for t in texts):
            return
        connect = [b for b in boxes if b.norm in CONNECT_WORDS]
        if self.args.auto_connect and connect and not self.args.dry_run:
            print("yansıtma kopmuş, Connect'e basılıyor…")
            self.inp.click(connect[0].rect.cx, connect[0].rect.cy)
            time.sleep(3.0)
            texts = [b.norm for b in self.look_full()]
            if not any(w in t for w in SESSION_ENDED_WORDS for t in texts):
                print("yeniden bağlanıldı.")
                return
        if any(w in t for w in UNLOCK_WORDS for t in texts):
            raise SystemExit(
                "iPhone Mirroring telefonun kilidinin açılmasını bekliyor "
                "(\"Unlock Your iPhone\").\n"
                "Telefondaki adımları izleyip kilidi açın, Connect'e basın, "
                "uygulamada kampanya listesini açın, sonra botu tekrar çalıştırın.")
        raise SystemExit(
            "iPhone Mirroring bağlantısı kesilmiş (\"iPhone in Use / Lock your iPhone to connect\").\n"
            "Telefonu kilitleyin, iPhone Mirroring'de Connect'e basın, sonra botu tekrar çalıştırın.")

    def learn_tab_bar(self) -> None:
        """Açık olan uygulamanın alt menü yazılarını imza olarak öğrenir."""
        r = self.rect_full
        floor = r.y + r.h * 0.88
        sig = sorted({b.norm for b in self.look_full()
                      if b.rect.cy >= floor and len(b.norm) >= 3})
        if len(sig) >= 2:
            self.tab_sig = sig
            print(f"alt menü imzası öğrenildi: {', '.join(sig)}")
        else:
            print("alt menü imzası okunamadı — --tab-words listesine düşülüyor")

    def on_list(self) -> bool:
        """Alt menü görünüyorsa listedeyiz; yoksa sheet veya detay sayfası açık."""
        sig = self.tab_sig or self.tab_words
        if not sig:
            return True
        texts = [b.norm for b in self.look_full()]
        need = 2 if len(sig) <= 3 else max(2, len(sig) // 2)
        return sum(1 for w in sig if any(w in t for t in texts)) >= need

    def swipe_sheet_down(self) -> None:
        r = self.rect_full
        self.inp.swipe(r.cx, r.y + r.h * 0.55, r.cx, r.y + r.h * 0.88)

    def swipe_back(self) -> None:
        r = self.rect_full
        self.inp.swipe(r.x + 3, r.cy, r.x + r.w * 0.75, r.cy)

    def recover_to_list(self) -> bool:
        """Katılım sonrası açılan sheet'i veya detay sayfasını kapatıp listeye döner."""
        if self.args.no_sheet_close or self.args.dry_run:
            return True
        for step in ("popup", "sheet", "back", "back"):
            if self.on_list():
                return True
            if step == "popup":
                if self.dismiss_popup():
                    time.sleep(self.args.after_tap)
                continue
            if step == "sheet":
                print("    ↳ sheet kapatılıyor (aşağı swipe)")
                self.swipe_sheet_down()
            else:
                print("    ↳ detay sayfasından geri dönülüyor (kenar swipe)")
                self.swipe_back()
            self.record("recover", step=step)
            time.sleep(self.args.after_tap)
        if self.on_list():
            return True
        print("    ↳ UYARI: listeye dönülemedi")
        return False

    def dismiss_popup(self) -> bool:
        if not self.popup_words:
            return False
        for tb in self.look():
            if tb.norm in self.popup_words:
                print(f"    ↳ popup kapatılıyor: {tb.text!r}")
                self.inp.click(tb.rect.cx, tb.rect.cy)
                self.record("dismiss", text=tb.text)
                return True
        return False

    def tap_visible_joins(self, band: tuple[float, float] | None = None) -> int:
        """Görünen ekrandaki tüm Katıl butonlarına sırayla dokunur."""
        tapped = 0
        radius = self.args.dedupe_radius
        now = time.time()
        self.recent = [r for r in self.recent if now - r[3] < self.args.dedupe_seconds]
        done: list[tuple[str, float, float, float]] = list(self.recent)

        def already(b: TextBox) -> bool:
            return any(t == b.norm and abs(x - b.rect.cx) < radius and abs(y - b.rect.cy) < radius
                       for t, x, y, _ in done)

        for _ in range(self.args.max_taps_per_screen):
            if self.taps >= self.args.max_taps:
                return tapped
            targets = [b for b in self.look() if is_join(b, self.extra, self.args.max_chars)]
            if band is not None:
                targets = [b for b in targets if abs(b.rect.cy - band[0]) <= band[1] / 2]
            targets = [b for b in targets if not already(b)]
            if not targets:
                return tapped
            tb = targets[0]
            done.append((tb.norm, tb.rect.cx, tb.rect.cy, time.time()))
            self.recent = done[-40:]
            print(f"  → tık: {tb.text!r} @ ({tb.rect.cx:.0f},{tb.rect.cy:.0f}) conf={tb.conf:.2f}")
            self.inp.click(tb.rect.cx, tb.rect.cy)
            self.record("tap", text=tb.text, x=round(tb.rect.cx), y=round(tb.rect.cy),
                        dry_run=self.args.dry_run)
            self.taps += 1
            tapped += 1
            time.sleep(self.args.after_tap)
            self.recover_to_list()
        return tapped

    def band_fingerprint(self, y: float) -> str:
        half = self.args.band / 2
        return "|".join(sorted(b.norm for b in self.look()
                               if abs(b.rect.cy - y) <= half and b.norm))

    def sweep_row(self, y: float, back: bool = False) -> int:
        """Yatay kaydırmalı kart satırını sağa gezer; her adımda ekranın tamamını tarar.

        Bant yalnızca satırın hangi noktadan kaydırılacağını ve karusel olup olmadığını
        anlamak için kullanılır; dokunuş taraması bant ile sınırlı değildir, çünkü yeni
        kartın Katıl butonu bandın biraz dışına düşebilir.
        """
        tapped = 0
        prev = self.band_fingerprint(y)
        seen = {prev}
        settle = max(self.args.after_scroll, 1.25)
        announced = False
        for _ in range(self.args.max_hscroll):
            self.hstep(y, back=back)
            time.sleep(settle)
            fp = self.band_fingerprint(y)
            if fp == prev:
                return tapped
            if fp in seen:
                if announced:
                    print(f"  ↔ satır başa sardı, bırakılıyor: y={y:.0f}")
                return tapped
            seen.add(fp)
            prev = fp
            if not announced:
                print(f"  ↔ yatay kaydırmalı satır: y={y:.0f}")
                announced = True
            # Yeni karta kaydırıldı: bu banttaki eski butonların dedupe koordinat kilidini kaldır
            half = self.args.band / 2
            self.recent = [r for r in self.recent if abs(r[2] - y) > half]
            tapped += self.tap_visible_joins()
            if self.taps >= self.args.max_taps:
                return tapped
        return tapped

    def hstep(self, y: float, back: bool = False) -> None:
        amount = -self.args.hscroll if back else self.args.hscroll
        if self.args.hmode == "swipe":
            a, b = (0.22, 0.78) if back else (0.78, 0.22)
            self.inp.swipe(self.rect.x + self.rect.w * a, y,
                           self.rect.x + self.rect.w * b, y, steps=22)
        else:
            self.inp.hscroll(self.rect.cx, y, amount)

    def sweep_bands(self) -> list[float]:
        """Kartın tamamının görünebildiği güvenli orta bölgedeki bant merkezleri.

        Görüntü kenarına yapışık bantlarda yatay kaydırma yapılmaz: orada kart yarım
        görünür ve sağa geçince yeni kartın Katıl butonu ekran dışında kalır.
        """
        margin = self.args.edge_margin if self.args.edge_margin is not None else self.args.band
        first = self.rect.y + margin + self.args.band / 2
        last = self.rect.y + self.rect.h - margin - self.args.band / 2
        if last < first:
            return [self.rect.cy]
        out, y = [], first
        step = self.args.band / 2
        while y <= last + 1:
            out.append(y)
            y += step
        return out

    def sweep_rows(self) -> int:
        if self.args.no_hsweep:
            return 0
        tapped = 0
        for y in self.sweep_bands():
            tapped += self.sweep_row(y)
            if self.taps >= self.args.max_taps:
                return tapped
            if not self.args.no_hsweep_back:
                tapped += self.sweep_row(y, back=True)
                if self.taps >= self.args.max_taps:
                    return tapped
        return tapped

    def scroll_to_top(self) -> None:
        prev = ""
        for i in range(self.args.max_rounds):
            fp = self.fingerprint(self.look())
            if fp == prev:
                print(f"listenin başına dönüldü ({i} kaydırma).")
                return
            prev = fp
            self.inp.scroll(self.rect.cx, self.rect.cy, abs(self.args.scroll) * 2)
            time.sleep(self.args.after_scroll)

    def run_list(self) -> None:
        same = 0
        prev = ""
        if self.args.to_top:
            self.scroll_to_top()
        for rnd in range(1, self.args.max_rounds + 1):
            print(f"[tur {rnd}] kaydırma listesi taranıyor…")
            if not self.args.dry_run and not self.on_list():
                self.recover_to_list()
            boxes = self.look()
            if self.args.verbose:
                for b in boxes:
                    print(f"      {b.conf:.2f} ({b.rect.cx:.0f},{b.rect.cy:.0f}) {b.text}")
            fp = self.fingerprint(boxes)
            same = same + 1 if fp == prev else 0
            prev = fp
            if same >= 2:
                print("liste sonu (ekran değişmiyor).")
                return
            self.tap_visible_joins()
            self.sweep_rows()
            if self.taps >= self.args.max_taps:
                print("max-taps sınırına ulaşıldı.")
                return
            self.inp.scroll(self.rect.cx, self.rect.cy, self.args.scroll)
            self.record("scroll", amount=self.args.scroll)
            time.sleep(self.args.after_scroll)
        print("max-rounds sınırına ulaşıldı.")

    def run_carousel(self) -> None:
        same = 0
        prev = ""
        y = self.rect.cy
        x1 = self.rect.x + self.rect.w * 0.82
        x2 = self.rect.x + self.rect.w * 0.18
        for card in range(1, self.args.max_rounds + 1):
            print(f"[kart {card}] taranıyor…")
            self.tap_visible_joins()
            if self.taps >= self.args.max_taps:
                print("max-taps sınırına ulaşıldı.")
                return
            fp = self.fingerprint(self.look())
            same = same + 1 if fp == prev else 0
            prev = fp
            if same >= 2:
                print("son kart (ekran değişmiyor).")
                return
            self.inp.swipe(x1, y, x2, y)
            self.record("swipe", direction="left")
            time.sleep(self.args.after_scroll)
        print("max-rounds sınırına ulaşıldı.")

    def search_and_filter(self, query: str) -> bool:
        """Ekranda arama çubuğunu bulup arama kelimesini yazar ve Enter'a basar."""
        print(f"🔍 '{query}' için arama kutusu aranıyor…")
        SEARCH_TERMS = (
            "kampanya veya sektor arayin",
            "kampanyalarda ara",
            "kampanya ara",
            "firsat ara",
            "sektor arayin",
            "ara",
            "arama",
            "search",
        )
        target_x: float | None = None
        target_y: float | None = None
        target_label = ""

        if getattr(self.args, "search_coords", None):
            try:
                parts = [float(p.strip()) for p in self.args.search_coords.split(",")]
                if len(parts) == 2:
                    target_x, target_y = parts
                    target_label = "özel koordinat"
            except Exception as ex:
                print(f"  ⚠️ search-coords ayrıştırılamadı: {ex}")

        if target_x is None:
            boxes = self.look()
            for term in SEARCH_TERMS:
                for b in boxes:
                    if b.rect.cy > self.rect.y + self.rect.h * 0.45:
                        continue
                    if term == b.norm or term in b.norm:
                        target_x, target_y = b.rect.cx, b.rect.cy
                        target_label = b.text
                        break
                if target_x is not None:
                    break

            if target_x is None:
                for b in boxes:
                    if b.rect.cy <= self.rect.y + self.rect.h * 0.45 and "ara" in b.norm:
                        target_x, target_y = b.rect.cx, b.rect.cy
                        target_label = b.text
                        break

        if target_x is None or target_y is None:
            print("  ⚠️ Arama kutusu ekranda bulunamadı (sonuçlar zaten açık olabilir). Listeye devam ediliyor.")
            return False

        print(f"  → Arama kutusuna dokunuluyor: {target_label!r} @ ({target_x:.0f},{target_y:.0f})")
        self.inp.click(target_x, target_y)
        time.sleep(0.8)
        print(f"  → Arama terimi yazılıyor: {query!r}")
        self.inp.type_text(query)
        time.sleep(0.4)
        print("  → Enter (Return) tuşuna basılıyor…")
        self.inp.press_key(36)
        time.sleep(2.0)
        self.record("search", query=query, x=round(target_x), y=round(target_y))
        print("  ✓ Arama tamamlandı, sonuç listesi taranıyor…")
        return True

    def run(self) -> None:
        activate_mirror()
        self.refresh_rect()
        blocked = occluders(self.rect)
        if blocked:
            raise SystemExit(
                f"iPhone Mirroring penceresinin önünde başka pencere var: "
                f"{', '.join(sorted(set(blocked)))}\nPencereyi açıkta bırakıp tekrar deneyin.")
        print(f"pencere: {self.owner} {self.rect_full}")
        print(f"tarama alanı: {self.rect}")
        print(f"OCR dilleri: {', '.join(vision_languages())}")
        print(f"mod: {self.args.mode} | dry-run: {self.args.dry_run} | oturum: {self.session}")
        print(f"{self.args.warmup} sn sonra başlıyor — durdurmak için fareyi oynatın veya Ctrl-C.")
        time.sleep(self.args.warmup)
        started = time.time()
        try:
            self.check_session()
            self.learn_tab_bar()
            if getattr(self.args, "search", None):
                self.search_and_filter(self.args.search)
            if self.args.mode == "carousel":
                self.run_carousel()
            else:
                self.run_list()
        except (Aborted, SystemExit) as e:
            print(f"\nDURDURULDU: {e}")
        except KeyboardInterrupt:
            print("\nDURDURULDU: Ctrl-C")
        finally:
            self.record("summary", taps=self.taps, seconds=round(time.time() - started, 1))
            print(f"\ntoplam dokunuş: {self.taps} | süre: {time.time() - started:.0f}s")
            print(f"kayıt: {self.session}/log.jsonl")


# --------------------------------------------------------------------- cli

def cmd_windows(_args) -> None:
    onscreen_ids = {w.get("kCGWindowNumber") for w in list_windows(True)}
    for w in list_windows(False):
        owner = str(w.get("kCGWindowOwnerName", ""))
        b = w.get("kCGWindowBounds") or {}
        if owner not in APP_NAMES and float(b.get("Width", 0)) <= 400:
            continue
        if owner not in APP_NAMES and w.get("kCGWindowNumber") not in onscreen_ids:
            continue
        state = "" if w.get("kCGWindowNumber") in onscreen_ids else "  [ekranda değil]"
        flag = " ←" if owner in APP_NAMES else ""
        name = str(w.get("kCGWindowName", "") or "")
        print(f"{owner:<24} {int(b.get('X',0)):>5},{int(b.get('Y',0)):>5} "
              f"{int(b.get('Width',0)):>5}x{int(b.get('Height',0)):<5}{flag} {name}{state}")


def cmd_calibrate(args) -> None:
    rect_full, owner = find_mirror_window(activate=True)
    rect = rect_full.inset(*(args.inset or (rect_full.h * 0.06, 0.0, rect_full.h * 0.09, 0.0)))
    try:
        ensure_clear(rect_full)
    except Aborted as e:
        raise SystemExit(f"{e}\nPencereyi açıkta bırakıp tekrar deneyin.")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    shot = RUN_DIR / "calibrate.png"
    iw, ih, scale = capture(rect, shot)
    boxes = ocr(shot, rect, scale, args.min_conf)
    extra = re.compile(args.match) if args.match else None
    print(f"pencere : {owner} x={rect_full.x:.0f} y={rect_full.y:.0f} "
          f"{rect_full.w:.0f}x{rect_full.h:.0f}")
    print(f"görüntü : {iw}x{ih} px (ölçek {scale:g}) → {shot}")
    print(f"diller  : {', '.join(vision_languages())}")
    print(f"{len(boxes)} metin bulundu:\n")
    for b in boxes:
        mark = "KATIL →" if is_join(b, extra, args.max_chars) else "       "
        print(f"{mark} {b.conf:.2f} ({b.rect.cx:7.0f},{b.rect.cy:7.0f})  {b.text}")


def cmd_run(args) -> None:
    Bot(args).run()


def parse_inset(s: str) -> tuple[float, float, float, float]:
    parts = [float(p) for p in s.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("inset formatı: ust,sag,alt,sol")
    return tuple(parts)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="iPhone Mirroring 'Katıl' botu")
    sub = p.add_subparsers(dest="cmd", required=True)

    def shared(sp):
        sp.add_argument("--inset", type=parse_inset, default=None,
                        metavar="UST,SAG,ALT,SOL",
                        help="pencere kenarlarından kırpma (pt); boşsa yükseklikten hesaplanır")
        sp.add_argument("--min-conf", type=float, default=0.25)
        sp.add_argument("--max-chars", type=int, default=24,
                        help="bu uzunluktan uzun satırlar buton sayılmaz")
        sp.add_argument("--match", default=None, help="ek eşleşme regex'i (normalize metin üzerinde)")

    sp = sub.add_parser("windows", help="açık pencereleri listele")
    sp.set_defaults(func=cmd_windows)

    sp = sub.add_parser("calibrate", help="tek kare oku, bulunan metinleri yazdır")
    shared(sp)
    sp.set_defaults(func=cmd_calibrate)

    sp = sub.add_parser("run", help="botu çalıştır")
    shared(sp)
    sp.add_argument("--mode", choices=("list", "carousel"), default="list")
    sp.add_argument("--dry-run", action="store_true", help="tıklama yapma, sadece hedefleri göster")
    sp.add_argument("--max-taps", type=int, default=40)
    sp.add_argument("--max-taps-per-screen", type=int, default=8)
    sp.add_argument("--dedupe-radius", type=float, default=70,
                    help="bu yarıçap içinde aynı metne ikinci kez dokunma (pt)")
    sp.add_argument("--dedupe-seconds", type=float, default=25,
                    help="aynı butona tekrar dokunmama süresi (sn)")
    sp.add_argument("--max-rounds", type=int, default=40)
    sp.add_argument("--scroll", type=int, default=-300,
                    help="tur başına dikey scroll (px); küçük değer her satırı orta bölgeden geçirir")
    sp.add_argument("--delay", type=float, default=0.35, help="her girdiden sonra bekleme")
    sp.add_argument("--after-tap", type=float, default=1.4)
    sp.add_argument("--after-scroll", type=float, default=0.9)
    sp.add_argument("--warmup", type=float, default=3.0)
    sp.add_argument("--search", default=None,
                    help="taramaya başlamadan önce arama çubuğuna yazılacak kelime (örn: 'katıl')")
    sp.add_argument("--search-coords", default=None,
                    help="arama kutusu koordinatları (X,Y); verilmezse ekrandan otomatik bulunur")
    sp.add_argument("--popup-ok", default="tamam,kapat,onayla,devam,harika",
                    help="dokunuştan sonra kapatılacak buton metinleri (virgülle)")
    sp.add_argument("--auto-connect", action=argparse.BooleanOptionalAction, default=True,
                    help="yansıtma kopmuşsa Connect'e basmayı dene")
    sp.add_argument("--hmode", choices=("wheel", "swipe"), default="wheel",
                    help="yatay ilerletme yöntemi: trackpad scroll (güvenli) veya swipe")
    sp.add_argument("--hscroll", type=int, default=-200,
                    help="yatay kaydırmalı satırlarda adım (px, negatif = sağa ilerle)")
    sp.add_argument("--max-hscroll", type=int, default=8, help="bir satırda en fazla yatay adım")
    sp.add_argument("--band", type=float, default=170, help="yatay tarama bandı yüksekliği (pt)")
    sp.add_argument("--edge-margin", type=float, default=None,
                    help="yatay tarama için görüntü kenarlarından bırakılacak pay (pt, varsayılan=band)")
    sp.add_argument("--no-hsweep", action="store_true", help="yatay kaydırmalı satırları tarama")
    sp.add_argument("--no-hsweep-back", action="store_true",
                    help="yatay satırda geri yönde ikinci tarama yapma")
    sp.add_argument("--to-top", action="store_true",
                    help="taramaya başlamadan önce listenin en başına dön")
    sp.add_argument("--tab-words",
                    default="ana sayfa,kampanyalar,kartlar,odemeler,qr ile ode,hesaplar,"
                            "islemler,firsatlar,basvuru,menu,param,varliklar,maximum,pazarama",
                    help="alt menü imzası okunamazsa kullanılacak yedek metinler")
    sp.add_argument("--no-sheet-close", action="store_true",
                    help="katılım sonrası açılan sheet'i aşağı swipe ile kapatma")
    sp.add_argument("--no-guard", action="store_true",
                    help="fare hareketi algılanınca durdurma kapalı")
    sp.add_argument("--require-focus", action="store_true",
                    help="iPhone Mirroring ön planda değilse çalışma")
    sp.add_argument("--verbose", "-v", action="store_true",
                    help="her turda okunan tüm metinleri yazdır")
    sp.set_defaults(func=cmd_run)

    args = p.parse_args(argv)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if STOP_FILE.exists():
        STOP_FILE.unlink()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
