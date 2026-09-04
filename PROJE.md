# Fatura & Kampanya Botu — Proje Notları

> Bu dosya devralan için yazıldı. Kod `mirror_bot.py`, kullanım `README.md`.
> Burada **niçin** ve **nerede kaldık** var. Değişiklik yaparsan bu dosyayı da güncelle.

## 1. Umut'un asıl hedefi

Her ay tekrarlayan şu döngüyü otomatikleştirmek:

1. **Kampanyalara katıl** — Bonus Flaş (Garanti BBVA) ve Maximum Mobil (İş Bankası)
   uygulamalarındaki tüm kampanyalara katıl.
2. **Faturaları öde** — kampanya şartlarını dolduracak şekilde, uygulamadan:
   - Kablo Mobil
   - Enerjisa
   - Başkent Doğalgaz

Kampanya katılımı hedefin kendisi değil; asıl amaç **fatura ödemelerinden kampanya
kazancı elde etmek**. Yani "önce katıl, sonra o kanaldan öde" sırası önemli.

Erişim yolu: Mac'ten **iPhone Mirroring**. Uygulamaların API'si yok, her şey ekran
okuma (OCR) + sentetik fare/klavye olayı ile yapılıyor.

## 2. Kurallar

**Ödemeyi onaylayan son tuşa bot basmaz.** Bu bilinçli bir tasarım kararı:

- Para transferi geri alınamaz. OCR yanlış okursa yanlış tutar / yanlış kurum / çift ödeme olur.
- Bot fatura listesini **okur**, tutarı ve son ödeme tarihini raporlar, ödeme onay
  ekranını **açar ve durur**. Son dokunuşu Umut yapar (fatura başına ~2 saniye).
- Kampanyaya katılmak zararsız olduğu için orada tam otomasyon var; ödeme farklı.

Bunun dışında bot: şifre yazmaz, hesap açmaz, ayar değiştirmez, sadece "Katıl"
metinlerine ve kendi navigasyon adımlarına dokunur.

**Alternatif hatırlatması:** "her ay otomatik ödensin" için en doğru araç bu bot değil,
**bankanın kendi otomatik ödeme talimatı**. Tek risk: bazı kampanyalar "mobil
uygulamadan yapılan ödeme" şartı arıyor ve talimatı saymayabiliyor — kampanya şartları
bu gözle okunmalı.

## 3. Mevcut durum

### Çalışan ve sahada doğrulanmış

| Özellik | Durum |
|---|---|
| Pencere bulma, Space'ler arası park edilmiş pencereyi çözme | ✅ |
| Pencere ekrandan taşarsa otomatik geri alma | ✅ |
| Önünü kapatan pencere varsa durma / öne alıp devam etme | ✅ |
| Vision OCR tr-TR ile ekran okuma, koordinat eşleme | ✅ isabetli |
| "Katıl" eşleştirme (OCR bozulmaları dahil) | ✅ test edildi |
| Dikey liste tarama + katılım | ✅ gerçek katılımlar yapıldı |
| Katılım sonrası sheet kapatma (aşağı swipe) | ✅ |
| Detay sayfasından geri dönme (kenar swipe) | ✅ |
| Alt menü imzasını uygulamadan otomatik öğrenme | ✅ |
| Yansıtma koptuğunda ("iPhone in Use") anlama | ✅ |

Bonus Flaş'ta gerçek katılımlar yapıldı (ör. DeFacto kampanyası, `DGRN92W4WK` indirim
kodu ekrana geldi). Kabaca 11-13 kampanyaya katılındı.

### Test edilmemiş

- **Maximum Mobil hiç denenmedi.** `maximum.sh` + `--search "katıl"` yazıldı ama gerçek
  uygulamada çalıştırılmadı. Alt menü imzası otomatik öğrenildiği için çalışması
  beklenir; doğrulanması gerek.
- **Fatura akışı hiç yazılmadı.** Ödemeler ekranının yapısı bilinmiyor.

## 4. Sahada doğrulanmış bulgular (tahmin değil, ölçüm)

Bunlar deneyerek bulundu, devralan aynı hataları tekrar etmesin:

1. **Bonus Flaş katılınca butonu `Katıldınız` yapmıyor.** Listeyi 21 dikey konumda
   taradım, tek bir `Katıldınız` yok. Katılmış kartlar **`Takip Et` / `Takip ve Detay`**
   gösteriyor. (README'de bir dönem yanlış yazıyordu, düzeltildi.)

2. **Bonus Flaş kampanya listesinde kalıcı yatay kaydırmalı satır yok.** 10 dikey
   konumun hepsinde test edildi, hiçbiri kalıcı yatay kaydırma yapmadı. Wheel ile
   içerik oynayıp **eski hâline dönüyor** — bu rubber-band sekmesi, karusel değil.
   Bu yüzden "içerik değişti → karusel" tespiti yanlış pozitif veriyordu; artık
   sekme kontrolü var (aynı parmak izi tekrar görülürse bırakıyor).
   *Not: Umut karusel gördüğünü söylüyor — muhtemelen başka bir ekranda
   (Kampanya Takip sekmesi veya Ana Sayfa/Cüzdan). Orada test edilmedi.*

3. **Aşağı swipe pencereyi sürükleyebiliyor.** Sheet kapatma swipe'ı pencerenin en alt
   kenarında bitince iPhone Mirroring penceresi 140pt aşağı kaydı ve ekrandan taştı.
   Swipe artık `%55 → %88` aralığında, kenara değmiyor.

4. **Klavye girişi odaktaki uygulamaya gider.** `--search` özelliği ön plan kontrolü
   yapmadığı için "katıl" kelimesi Claude'a/Terminal'e yazılabiliyordu. Artık
   `require_mirror_focus()` var — iPhone Mirroring önde değilse yazmıyor.

5. **`calibrate` yanlış pencereyi okuyabiliyordu.** Bir kez telefon yerine arkadaki
   Takvim penceresini okudu. Artık kapanma kontrolü var.

6. **Ön plan şartı yanlış kriterdi.** Tıklama, imleç altındaki pencereye gider; uygulama
   ön planda olmasa da olur. Doğru kriter: pencerenin önünde onu **kapatan** pencere
   olmaması (z-sırası kontrolü). Klavye girişi bunun istisnası — orada ön plan şart.

7. **Ortam turu bölüyor.** Claude, Finder, WhatsApp, Teams, Takvim pencereleri telefon
   penceresinin önüne geçince bot güvenlik gereği duruyor. Temiz tur için telefon
   penceresinin üstü boş olmalı.

## 5. Açık işler (öncelik sırasıyla)

1. **Bonus Flaş turunu sonuna kadar bir kez çalıştır** — son denemeler ortam yüzünden
   yarım kaldı (`liste sonu` mesajını görene kadar).
2. **Maximum Mobil'i doğrula** — önce `./maximum.sh --dry-run`, çıktıda hedefler doğruysa
   gerçek tur. Alt menü imzası ve "katıl" araması orada nasıl davranıyor, gör.
3. **Karuseli bul** — Umut'un gördüğü yatay kaydırmalı satır hangi ekranda? Kampanya
   Takip sekmesi ve Ana Sayfa/Cüzdan test edilmeli.
4. **Fatura okuma komutu** (`./bot faturalar` gibi): Ödemeler → Fatura Ödeme yoluna
   gidip Kablo Mobil / Enerjisa / Başkent Doğalgaz için kurum, tutar, son ödeme tarihi
   okuyup tablo hâlinde yazsın. Sadece okuma, sıfır risk.
5. **Ödeme onay ekranına götürme** — seçilen faturanın onay ekranını açıp ekranda ne
   yazdığını (kurum + tutar) teyit için basıp **durma**. Son tuş Umut'ta (bkz. §2).
6. **Aylık zamanlama** — `launchd` ile ayın belirli gününde kampanya turu + fatura
   raporu; sonucu bildirim olarak versin.

## 6. Mimari

```
mirror_bot.py     tek dosya, tüm mantık (~900 satır)
bot               venv'i çağıran ince sarmalayıcı
kampanya.sh       uygulamadan bağımsız kampanya turu
bonusflas.sh      kampanya.sh'e kısayol
maximum.sh        --search "katıl" ile Maximum turu
stop              çalışan botu durdurur (STOP dosyası)
setup.sh          venv + pyobjc kurulumu
```

**Tur döngüsü:** pencere bul → önü açık mı → yansıtma canlı mı → alt menü imzasını öğren
→ listenin başına dön → görünen Katıl'lara dokun → sheet/detay kapat → yatay satırları
tara → aşağı kaydır → ekran iki tur değişmezse bitir.

**Güvenlik mekanizmaları:** fare hareketi algılama (`--no-guard` ile kapanır), z-sırası
kapanma kontrolü, `--max-taps` / `--max-rounds` tavanları, `--dry-run`, `./stop`,
her dokunuşun `~/.cache/mirror-bot/<tarih>/log.jsonl` içine kaydı.

## 7. Nasıl test edilir

```bash
./bot calibrate            # ekranı oku, KATIL sayılanları göster
./kampanya.sh --dry-run    # tıklamadan tur, neye dokunacağını yaz
./kampanya.sh              # gerçek tur
```

Yeni bir uygulamada **önce `--dry-run`**. Çıktıdaki `→ tık:` satırları yanlış hedef
gösteriyorsa gerçek turu çalıştırma.

## 8. Ortam

- macOS 26.5, Python 3.14 (`.venv`), pyobjc (Quartz + Vision)
- Terminal'e gereken izinler: Ekran Kaydı, Erişilebilirlik, Otomasyon → System Events
- Vision OCR `tr-TR` destekliyor, ayrı OCR kurulumuna gerek yok
- iPhone Mirroring telefonu elinize alınca kopuyor; telefon kilitli olmalı
