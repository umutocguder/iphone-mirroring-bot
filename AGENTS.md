# iphone-bot — AI çalışma kuralları

macOS iPhone Mirroring penceresi üzerinden ekran okuma (Vision OCR) ve
CoreGraphics olaylarıyla kampanya butonlarına tıklayan Python otomasyon botu.

> ### Tek dosya kuralı
> Bu depoda AI talimatları **yalnızca bu dosyada** tutulur. `CLAUDE.md` tek
> satırlık `@AGENTS.md` importudur. Araç adıyla ikinci bir kural dosyası
> (`GEMINI.md`, `.cursorrules`, `.clinerules`, `copilot-instructions.md`)
> **açılmaz** — aynı metnin kopyaları birbirinden ayrışıyor.

## 0. Önce ortak bağlamı oku

Umut birden çok AI aracı kullanıyor (Claude Code, Antigravity/Gemini, Cline).
Ortak bağlam tek yerde:

```
/Users/umut/ai-context/
├── README.md        ← önce burayı oku
├── 00-umut.md       ← kullanıcı profili ve çalışma tarzı
├── 01-projeler.md   ← proje indeksi
├── kurallar/        ← UYULMASI ZORUNLU kurallar
├── projeler/        ← proje başına tam bağlam
└── bilgi-bankasi/   ← derin teknik notlar
```

Öğrendiğin kalıcı her bilgiyi oraya **geri yaz** —
bkz. `/Users/umut/ai-context/kurallar/baglami-md-ye-yaz.md`.

## 1. Proje

- **Dil:** Python 3.10+ — macOS Vision Framework, CoreGraphics, PyObjC
- Ekran okuma `screencapture` (yalnız pencere bölgesi) + Vision OCR (tr-TR)
- Girdi: CoreGraphics olayları (tık, dikey/yatay scroll, swipe)

## 2. Sınırlar — genişletilmez

Bot **şifre yazmaz, form doldurmaz, ödeme adımına girmez.** Yalnızca ekranda
gördüğü "Katıl" metinlerine dokunur. Uygulamanın içine hiç girmez.
Bu sınırı genişleten bir özellik önerme; istenirse önce Umut'a sor.

## 3. Değişiklik sonrası

- Değişiklikler `WORKLOG.md`'ye işlenir.
- Uzak depo: `https://github.com/umutocguder/iphone-mirroring-bot.git`
  (private, dal `main`).
