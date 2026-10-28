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

---

## Git Branch Model — `master` = production, `dev` = UAT  (MANDATORY)

Set by Umut on 2026-10-15. **This overrides any earlier branch or tagging
instruction in this file**, including "auto-bump and tag on every push".

| Branch | Meaning | Rule |
|---|---|---|
| `master` | **Production** — what is live / shipped right now | Never commit directly. Only released code is merged in. |
| `dev` | **UAT** — where development happens; always ahead of or equal to `master` | All work lands here. |

The branch name `main` is not used.

**The agent manages branch switching, commits, merges and tags itself — it does
not ask Umut which branch to work on.**

1. A code change is requested → if on `master`, **switch to `dev` immediately**.
   The change and the commit go to `dev`.
2. Builds and packages are produced from `dev`.
3. The moment it goes live — App Store approval, Vercel production, delivery to
   the client — merge `dev` into `master`.
4. Tag on `master`: `v<version>` (e.g. `v1.0`, `v1.1`). **A tag is only ever
   created for a version that actually shipped.** Never tag on every push.
5. Development continues on `dev`. After the merge, `dev` and `master` are equal.

If a merge conflict appears, stop and tell Umut — do not resolve it alone.

Full rule: `/Users/umut/ai-context/kurallar/git-dal-modeli-master-dev.md`
