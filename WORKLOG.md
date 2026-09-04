# iPhone Bot Proje Günlüğü (Worklog & AI Context Handoff)

Bu dosya, iPhone Mirroring Bot projesinde yapılan tüm geliştirmeleri, mimari kararları ve mevcut durumu belgeler.

---

### [2026-09-03 16:23] Antigravity Proje Yapılandırması ve Konum Düzenlemesi
- **Görev ve Amaç**: `iphone-bot` projesinin Antigravity Projects sekmesine bağımsız proje olarak eklenmesi ve kişisel projeler alanına (`/Users/umut/mycodespace/iphone-bot`) taşınması.
- **Teknik Kararlar ve Mimari Değişiklikler**:
  - Proje konumu `/Users/umut/mycodespace/iphone-bot` olarak güncellendi, geriye dönük uyumluluk için eski yola (`~/intetra/iphone-bot`) symlink bağlandı.
  - Antigravity proje kaydı (`2e5ef972-48ed-48e1-8155-b368251b6ac6.json`) oluşturuldu.
  - Evrensel kural dosyaları (`AGENTS.md` ve `CLAUDE.md`) ve bu `WORKLOG.md` eklendi.
  - GitHub uzak bağlantısı: `https://github.com/umutocguder/iphone-mirroring-bot.git`.
- **Etkilenen Dosyalar**:
  - [AGENTS.md](file:///Users/umut/mycodespace/iphone-bot/AGENTS.md)
  - [CLAUDE.md](file:///Users/umut/mycodespace/iphone-bot/CLAUDE.md)
  - [WORKLOG.md](file:///Users/umut/mycodespace/iphone-bot/WORKLOG.md)
- **Mevcut Durum ve Doğrulama**:
  - Proje Antigravity sol menüsündeki "Projects" listesinde `iphone-bot` olarak yerini aldı.
  - Git durumu ve remote bağlantısı aktif.

### [2026-09-03 17:00] Dizin Yolu Senkronizasyonu ve Antigravity GitFolder Tanımı
- **Görev ve Amaç**: `iphone-bot` projesinin Antigravity Projects panelinde eksiksiz `gitFolder` kaynağıyla listelenmesi ve diskteki `mycodespaces` yolu ile tam uyumlu hale getirilmesi.
- **Teknik Kararlar**:
  - `~/.gemini/config/projects/2e5ef972-48ed-48e1-8155-b368251b6ac6.json` dosyası `gitFolder` standardına göre güncellendi.
  - `mycodespace` ve `mycodespaces` yolları sembolik link ile birbirine bağlandı.
- **Etkilenen Dosyalar**:
  - [WORKLOG.md](file:///Users/umut/mycodespaces/iphone-bot/WORKLOG.md)

### [2026-09-04 08:56] Kararlılık ve Hata Düzeltmeleri (Bug Fixes)
- **Görev ve Amaç**: `mirror_bot.py` içindeki kritik pencere taşıma, OCR filtreleme, swipe pencere sürükleme ve klavye girişi hatalarının giderilmesi.
- **Teknik Kararlar ve Yapılan Değişiklikler**:
  1. `reposition_window`: macOS Sequoia'da pencere başlığı boş veya cihaz adı olduğundan AppleScript'in patlaması engellendi, doğrudan `window 1` kontrolü eklendi.
  2. `SKIP_WORDS`: "Katılındı" OCR edildiğinde oluşan `katiiindi` (3 adet i) biçimi ve `katiiiminiz` kelimesi listeye eklenerek kelime kaçırma/filtre atlama sorunu giderildi.
  3. `swipe_back`: Sol kenar koordinatı `r.x + 3` noktasından pencere içeriğine (`r.x + max(16.0, r.w * 0.05)`) çekildi. Böylece swipe sırasında tüm macOS penceresini tutma/sürükleme (window drag) hatası çözüldü.
  4. `type_text`: Türkçe karakterlerin (ı, ş vb.) klavye düzeninden bağımsız güvenle yazılabilmesi için `pbcopy` + `Cmd+V` yapıştırma desteği ve keystroke fallback'i eklendi.
  5. `display_rects`: `ids` `None` döndüğünde oluşabilecek `TypeError` engellendi.
  6. `occluders`: 10x10 pt ve altındaki görünmez / hayalet yardımcı pencerelerin botu engellemesi önlendi.
  7. `dedupe-seconds`: Yavaş inen ve gecikmeli turlarda aynı butona tekrar tıklamayı önlemek için varsayılan süre 25'ten 60 saniyeye çıkarıldı.
- **Etkilenen Dosyalar**:
  - [mirror_bot.py](file:///Users/umut/mycodespaces/iphone-bot/mirror_bot.py)
  - [WORKLOG.md](file:///Users/umut/mycodespaces/iphone-bot/WORKLOG.md)
- **Mevcut Durum ve Doğrulama**:
  - Python sözdizimi derlendi ve doğrulandı (`py_compile`).
  - Pencere listeleme (`./bot windows`) ve regex filtreleme testleri başarıyla tamamlandı.

### [2026-09-05 00:42] Automated Unit Test Suite Implementation
- **Goal & Purpose**: Implement automated unit tests adhering to Section 8 of AGENTS.md (Mandatory Automated Testing Standard).
- **Implementation Highlights**:
  - Implemented `tests/test_mirror_bot.py`:
    - Validates Rect bounding box arithmetic, center calculation, and edge insets.
    - Validates Turkish character normalization folding to clean ASCII.
    - Validates OCR loose character matching (misrecognized '1', 'l', and 'i' substitutions).
    - Validates join button discrimination between active "Katıl" and already completed "Katıldınız".
- **Affected Files**:
  - [tests/test_mirror_bot.py](file:///Users/umut/mycodespaces/iphone-bot/tests/test_mirror_bot.py)
  - [WORKLOG.md](file:///Users/umut/mycodespaces/iphone-bot/WORKLOG.md)
- **Current State & Verification**:
  - `python3 -m unittest discover -s tests -p "test_*.py"`: 4/4 tests passed in 0.000s with 100% success.


