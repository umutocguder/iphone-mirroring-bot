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

### [2026-09-05 01:08] Ürünleştirme ve Ticari Sürüm Başlangıcı (Productization by 11hopem)
- **Görev ve Amaç**: `iphone-bot` motorunun son kullanıcıya yönelik ticari bir macOS ürününe dönüştürülmesi ve ürünleşme yol haritasının başlatılması.
- **İmza / Marka**: `by 11hopem`
- **Ürünleşme Yol Haritası & Tasarım Kararları**:
  1. **Kullanıcı Deneyimi & Form Faktörü**: Terminal ve Python bağımlılıklarından arındırılmış, macOS Menu Bar (Menü Çubuğu) üzerinde tek tıkla çalışan şık bir uygulama (SwiftUI / standalone binary).
  2. **Güvenlik & Gizlilik Odaklı Mimari**: "Hiçbir bankacılık şifresi, API anahtarı veya kart bilgisi istemez; sunucuya sıfır veri gönderir." Apple'ın yerel iPhone Mirroring ekranını yerel Vision OCR ile okuyan %100 gizlilik odaklı mimari.
  3. **Geniş Uygulama & Kampanya Havuzu**:
     - Bonus Flaş (Garanti BBVA)
     - Maximum Mobil (İş Bankası)
     - World Mobil (Yapı Kredi)
     - Juzdan (Akbank)
     - Bankkart (Ziraat)
     - Hopi & Boyner
  4. **Gelir Modeli (Monetization)**:
     - Gumroad / LemonSqueezy üzerinden tek seferlik lisans veya yıllık abonelik.
     - "Ayda kazandırdığı bonus ve puanlar kendi ücretini fazlasıyla çıkarır" değer önerisi.
- **Etkilenen Dosyalar**:
  - [README.md](file:///Users/umut/mycodespaces/iphone-bot/README.md)
  - [WORKLOG.md](file:///Users/umut/mycodespaces/iphone-bot/WORKLOG.md)
- **Mevcut Durum**:
  - `by 11hopem` imzası belgelere işlendi, GitHub'a pushlanacak.





---

## 2026-09-28 08:28 - Zorunlu Marka Kimliği ve Logo Standardı
- **Görev ve Amaç**: Projeye özgün vektör logo (`assets/logo.svg`) eklenmesi ve marka kimliği standardının sağlanması.
- **Doğrulama**: 7 adet otomatik test çalıştırıldı (All Passed).
- **Etkilenen Dosyalar**: `assets/logo.svg`, `WORKLOG.md`.

---

## 2026-10-02 15:05 - Turbo Hız Optimizasyonu ve Bağlamsal Kampanya Doğruluğu
- **Görev ve Amaç**: Botun tarama hızının 4-5 kat artırılması, yatay kaydırma kaynaklı takılmaların ve buton kaçırma / aynı butona mükerrer dokunma sorunlarının çözülmesi.
- **Teknik Kararlar ve Yapılan İyileştirmeler**:
  1. **Bağlamsal (Context-Based) Tekilleştirme**:
     - Sabit koordinat dedupe'u yerine her "Katıl" butonu üzerindeki en yakın kampanya başlığı (`get_context`) ile ilişkilendirildi.
     - Yeni kart eski kartın koordinatına kaysa bile başlığı farklı olduğu için asla kaçırılmıyor.
     - Aynı kart ekranda kalsa bile mükerrer tıklama riski sıfırlandı.
  2. **Genişletilmiş Kelime ve Boyut Eşleme**:
     - `JOIN_WORDS` tuple'ına `"katiiin"` ("Katılın") ve `"katiimak"` eklendi.
     - `max_chars` sınırı 24'ten 36'ya çıkarılarak uzun kampanya metinlerinin elenmesi önlendi.
  3. **Yatay Kaydırma (H-Sweep) Tasfiyesi**:
     - Bonus Flaş dikey listesinde karusel olmadığı için turları 10-15 sn kilitleyen `sweep_rows` dikey modda `--no-hsweep` ile devre dışı bırakıldı.
  4. **Turbo Gecikmeler**:
     - `after-tap`: 2.2s -> 0.8s
     - `after-scroll`: 1.2s -> 0.6s
     - `delay`: 0.35s -> 0.15s
     - Mouse down/up: 0.12s -> 0.04s
- **Doğrulama**: `py_compile` ve 7/7 test paketi başarıyla tamamlandı.
- **Etkilenen Dosyalar**: `mirror_bot.py`, `kampanya.sh`, `WORKLOG.md`.

---

## 2026-10-02 15:21 - Akıllı Karusel Taraması ve Sayfalı Kart (Paging) İyileştirmeleri
- **Görev ve Amaç**: Kullanıcı sahasından gelen 4 kritik karusel probleminin çözülmesi:
  1. **Son Kart Dokunuşu**: Yatay kaydırmanın bittiği son karttaki "Katıl" butonuna dokunulmadan çıkılması engellendi (`curr_fp == prev_fp` anında dokunuş yapılıp çıkılıyor).
  2. **Gereksiz Sola Geri Sarmanın Kaldırılması**: Sağa doğru tarama yapıldıktan sonra tüm yolu tekrar sola sararak vakit kaybeden `back=True` döngüsü tamamen iptal edildi.
  3. **Mükerrer Bant Taramalarının Önlenmesi**: `sweep_bands` adım aralığı (`step`) kart yüksekliğine (`band * 0.85`) optimize edildi; aynı fiziksel kart sırasını birden çok kez tarama sorunu çözüldü.
  4. **Başa Dönen (Infinite Loop / Paging) Karusel Algılama**: İlk kartın başlığı (`initial_ctx`) ve token kümesi (`initial_tokens`) kaydedilerek, karusel başa sardığında (`overlap > 0.65` veya başlık tekrarı) anında tespit edilip döngüden çıkılması sağlandı.
- **Doğrulama**: `py_compile` ve 7/7 unit test başarıyla geçti.
- **Etkilenen Dosyalar**: `mirror_bot.py`, `kampanya.sh`, `WORKLOG.md`.

---

## 2026-10-02 15:27 - Otomatik Uygulama Başlatma (Spotlight) ve Karusel Doğrulama Test Paketi
- **Görev ve Amaç**: 
  1. Uygulama açık değilse veya başka bir uygulama öndeyse iPhone Mirroring Spotlight menüsü üzerinden otomatik "Bonus" yazıp açma ve "Kampanyalar" sekmesine dokunma otomasyonu (`ensure_bonus_app_open`).
  2. Karuselin sonundaki "Katıl" butonuna dokunulmadan çıkılmasını engelleyen kesin dokunuş garantisi.
  3. Paging karusellerde sola gereksiz geri sarmayı (`back=True`) iptal etme ve mükerrer yatay bant taramasını `swept_carousel_fps` ile engelleme.
  4. 3 yeni otomatik birim testi ile tüm bu mantıkların (wrap-around, context dedupe, cache) doğrulanması.
- **Doğrulama**: `python3 -m unittest discover -s tests -p "test_*.py"` ile 10/10 test 0.22s içinde %100 başarıyla geçti.
- **Etkilenen Dosyalar**: `mirror_bot.py`, `tests/test_mirror_bot.py`, `WORKLOG.md`.

---

## 2026-10-02 15:55 - Üst Filtre Bandı İzolasyonu, Başa Dönen Paging Karuseli ve Spotlight İkon Dokunuşu
- **Görev ve Amaç**:
  1. **BONUS ve PARACARD Filtre Bandının İzolasyonu**: Ekranın üst kısmındaki (`y < self.rect.y + 240`, `y ≈ 333`) sabit filtre sekmelerine (`BONUS | PARACARD | Tümü`) farenin gitmesi `is_filter_band` ve `sweep_bands` alt sınırı ile kesin olarak engellendi.
  2. **İlk Kampanyayı Tekrar Görünce Durma (Infinite Paging Loop)**: Sayfanın başındaki dönen kart yapısının ilk kampanya başlığı (`get_card_title_in_band`) kaydedilerek, sağa kaydırdıkça başa dönüldüğü an (`curr_title == initial_title`) anında tespit edilip satır sonlandırılıyor.
  3. **Yatay Scrolları Sonuna Kadar Gezme & Son Kart Katıl Dokunuşu**: `max_hscroll` sınırı 25'e çıkarıldı. Sağa doğru kaydırmanın sonuna ulaşıldığında (`curr_fp == prev_fp`), duvara çarpmış son karttaki "Katıl" butonu asla kaçırılmadan tıklandıktan sonra satırdan çıkılıyor.
  4. **Otomatik Spotlight Başlatma**: Bonus Flaş açık değilse `View -> Home Screen` ve `View -> Spotlight` üzerinden "bonus" yazılarak, Top Hit altındaki `BonusFlaş` uygulama ikonuna (`cy - 35`) tıklanıp "Kampanyalar" sekmesi açılıyor.
  5. **Birim Test Paketi**: 13/13 test %100 başarıyla geçti.
- **Etkilenen Dosyalar**: `mirror_bot.py`, `tests/test_mirror_bot.py`, `WORKLOG.md`.
---

## 2026-10-02 16:04 - Güvenli Görüş Alanı, Kart Boyu Buton Tarama ve Karusel Tekrarı Engelleme
- **Görev ve Amaç**:
  1. **Kart Altında Kalan Butonların Kaçırılmasını Önleme (`card_y` aralığı)**:
     - Kart başlığı ile butonu arasında 160+ pt fark olduğu için eski ±85 pt bant kısıtı kaldırıldı. `card_y` parametresi eklenerek `[card_y - 50, card_y + 220]` aralığındaki tüm butonlar kapsama alındı.
  2. **Ekran Dışında/Altında Kalan Butonların Taranmasını Önleme (Güvenli Bant Aralığı)**:
     - `sweep_bands` üst sınırı `rect.y + 240` (filtre başlığı altı), alt sınırı ise `rect_bottom - 180` (tab bar üstü) olarak sınırlandırıldı. Kartın butonu ekranın altında kesik kalırken karuselin taranması engellendi; dikey kaydırmayla kartın güvenli orta bölgeye gelmesi garanti edildi.
  3. **Aynı Karuseli Tekrar Kaydırmayı Kesin Olarak Önleme**:
     - `swept_carousel_titles` ve `swept_carousel_sections` eklendi. Taranan karuselin gördüğü tüm kart başlıkları ve ait olduğu bölüm adı (örn: "EN SEVİLEN KAMPANYALAR") kaydedilerek sonraki dikey turlarda bu karuselin tekrar taranması %100 engellendi.
  4. **Paging Kartlarda Yüksek Momentumlu Adım (`hscroll -380`)**:
     - Sayfalı kartların snap eşiğini rahatça aşması için varsayılan adım `-380` px'e yükseltildi, "ufak swipe / takılma" sorunu giderildi.
  5. **Birim Test Paketi**: 16/16 test %100 başarıyla geçti.
- **Etkilenen Dosyalar**: `mirror_bot.py`, `tests/test_mirror_bot.py`, `WORKLOG.md`.

