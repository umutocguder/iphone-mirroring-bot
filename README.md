<!-- Created by 11Hopem -->
# 📱 macOS iPhone Mirroring Campaign Bot

[![Platform](https://img.shields.io/badge/platform-macOS%2015%2B%20(Sequoia)-lightgrey.svg)](https://apple.com)
[![Engine](https://img.shields.io/badge/engine-macOS%20Vision%20OCR%20%7C%20CoreGraphics-blue.svg)](#architecture)
[![Safety](https://img.shields.io/badge/safety-read--only%20OCR%20%7C%20zero%20form%20entry-brightgreen.svg)](#safety--privacy)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://11hopem.com)
[![Created by 11Hopem](https://img.shields.io/badge/created%20by-11Hopem-orange.svg)](https://11hopem.com)

An automated accessibility assistant for macOS Sequoia (15.0+) that navigates banking and rewards apps inside the native **iPhone Mirroring** (`iPhone Mirroring.app`) window, detects "Join Campaign" / "Katıl" action buttons via **macOS Vision OCR**, and automatically participates in eligible credit card reward campaigns.

---

## 🌟 How It Works

- **Non-Invasive Vision Pipeline**: Operates purely outside the iOS sandbox using standard macOS accessibility tools. Takes window-scoped captures via `screencapture`, runs high-speed OCR using Apple's native **Vision Framework** (`VNRecognizeTextRequestRevision3`), and synthesizes low-level input events via `CoreGraphics`.
- **Horizontal & Vertical Carousel Scanning**: Discovers horizontally scrollable reward cards, swiping through carousel banners to register for hidden card bonuses.
- **Auto-Dismiss Dialogs**: Detects confirmation modals and dialogs ("Tamam", "Devam", "Kapat") to clear prompts automatically and resume campaign sweeps.
- **Zero Credential Access**: Never inputs passwords, never enters OTPs, and never interacts with payment or transfer flows. Restricts actions strictly to campaign enrollment labels.

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│     iPhone Mirroring Window     │
│   (Bonus Flaş, Maximum Mobil)   │
└────────────────┬────────────────┘
                 │ screencapture (Window Rect)
                 ▼
┌─────────────────────────────────┐
│     macOS Vision OCR Engine     │
│   Token Bounding Boxes & Text   │
└────────────────┬────────────────┘
                 │ Match Action Target ("Katıl")
                 ▼
┌─────────────────────────────────┐
│     CoreGraphics Synthesizer    │
│  Tap, Smooth Scroll & Swipe     │
└─────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- macOS 15.0+ Sequoia with iPhone Mirroring configured
- Python 3.10+
- Accessibility & Screen Recording permissions granted to your terminal emulator (`Terminal.app` or `iTerm2.app`)

### 1. Clone & Setup

```bash
git clone https://github.com/umutocguder/iphone-mirroring-bot.git
cd iphone-mirroring-bot
./setup.sh
```

### 2. Usage

Open your target rewards application inside **iPhone Mirroring**, then run:

```bash
# Dry run: detects buttons and prints bounding boxes without tapping
./kampanya.sh --dry-run

# Live run: automatically taps detected campaign join buttons
./kampanya.sh

# Search-focused sweep (e.g. for Maximum Mobil)
./maximum.sh
```

---

## 🛡️ License & Attribution

Created by [11Hopem](https://11hopem.com).  
Copyright © 2026 11Hopem. All rights reserved.  
Licensed under the [MIT License](LICENSE).  
Official website: [https://11hopem.com](https://11hopem.com)
