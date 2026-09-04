# iPhone Mirroring "Katıl" botu
*by 11hopem*

> Projenin amacı, kuralları, sahada doğrulanmış bulgular ve açık işler: **[PROJE.md](PROJE.md)**.
> Devralıyorsan önce onu oku.

Bonus Flaş / Maximum Mobil gibi kampanya listelerini iPhone Mirroring penceresi üzerinden
gezer, ekranda gördüğü **Katıl** butonlarını bulup üstlerine tıklar, yatay kaydırmalı kart
satırlarını da sağa doğru tarar. Uygulamanın içine hiç girmez — tamamen ekran okuma +
fare olayı üretme ile çalışır.

- Ekran okuma: `screencapture` (sadece pencere bölgesi) + macOS **Vision OCR / tr-TR**
- Girdi: CoreGraphics olayları (tık, dikey/yatay scroll, swipe)
- Şifre yazmaz, form doldurmaz, ödeme adımına girmez. Sadece "Katıl" metinlerine dokunur.

## Kurulum

```bash
cd ~/intetra/iphone-bot && ./setup.sh
```

### İzinler (bir defalık)

Botu **hangi uygulamadan çalıştıracaksanız** (Terminal.app / iTerm) o uygulamaya
Sistem Ayarları → Gizlilik ve Güvenlik altında şunları verin:

| İzin | Ne için |
|---|---|
| **Ekran Kaydı ve Sistem Sesi** | pencere görüntüsünü almak |
| **Erişilebilirlik** | tık / scroll / swipe olayı üretmek |
| **Otomasyon → System Events** | pencereyi öne almak ve ekran dışına taşmışsa geri almak |

İzin yoksa `could not create image from rect` hatası alırsınız.

## Kullanım

### Bonus Flaş (veya Genel Liste)
```bash
~/intetra/iphone-bot/bonusflas.sh           # gerçek çalıştırma
~/intetra/iphone-bot/bonusflas.sh --dry-run # prova (tıklamadan)
```

### Maximum Mobil (Arama ile "Katıl" Filtreleme)
Maximum Mobil'de yüzlerce kampanya arasından katılım gerektirenleri arama çubuğuna **"katıl"** yazıp bularak listeler ve katılır:
```bash
~/intetra/iphone-bot/maximum.sh             # "katıl" arar ve sonuçlara katılır
~/intetra/iphone-bot/maximum.sh --dry-run   # prova (tıklamadan)
```

`kampanya.sh` genel amaçlı başlatıcıdır. `bonusflas.sh` ve `maximum.sh` uygulamalara göre optimize edilmiş parametrelerle çalışır.

Alt komutlar:

```bash
./bot windows           # iPhone Mirroring penceresi görünüyor mu
./bot calibrate         # tek kare oku, hangi metinlerin "KATIL" sayıldığını yazdır
./bot run --dry-run     # tıklamadan tur at
./bot run               # ham çalıştırma (ayarlar için aşağıya bakın)
```

Sıra: iPhone Mirroring bağlıyken uygulamada **kampanya listesi ekranını açın**, sonra
komutu çalıştırın. Bot pencereyi öne alır, `--warmup` kadar bekler ve başlar.

### Durdurma

- Fareyi oynatın → bot anında durur (`--no-guard` ile kapatılabilir)
- Ctrl-C
- Başka bir terminalden `./stop`
- Telefon penceresinin önüne başka bir pencere gelirse bot kendi kendine durur

## Ne yapar (tur döngüsü)

1. Pencereyi bulur, ekran dışına taşmışsa içeri geri alır, önünü kapatan pencere varsa durur
2. Yansıtma kopmuşsa ("iPhone in Use") anlar, `--auto-connect` ile Connect'e basmayı dener
3. Açık uygulamanın **alt menü yazılarını imza olarak öğrenir** (sheet/detay tespiti için)
4. `--to-top` ile listenin başına döner
5. Görünen ekrandaki tüm **Katıl** butonlarına dokunur
6. Her dokunuştan sonra açılan **sheet**'i (aşağı swipe) veya **detay sayfasını**
   (kenardan geri swipe) kapatıp listeye döner
7. Yatay kaydırmalı kart satırlarını bant bant sağa tarar, oradaki Katıl'lara da dokunur
8. Aşağı kaydırıp tekrarlar; ekran iki tur değişmezse liste bitmiştir

## Faydalı ayarlar

```bash
./bot run --max-taps 25 --after-tap 2.5       # daha yavaş, sınırlı
./bot run --scroll -380                       # daha küçük dikey adım
./bot run --inset 150,0,60,0                  # otomatik kırpmayı elle geçersiz kıl
./bot run --hscroll -320 --band 170           # yatay tarama adımı ve bant yüksekliği
./bot run --no-hsweep                         # yatay kaydırmalı satırları hiç tarama
./bot run --popup-ok "tamam,kapat,anladım"    # dokunuş sonrası bilgi kutusunu kapat
./bot run --match '\bfirsati kap\b'           # ek buton metni (normalize edilmiş halde)
./bot run -v                                  # her turda okunan tüm metinleri yazdır
```

`--max-chars 24`: uzun satırlar buton sayılmaz, böylece "Kampanyaya katıl ve 100 TL kazan"
gibi açıklama metinlerine tıklanmaz.

## Eşleştirme mantığı

Metin normalize edilir (`ı→i`, `ş→s`, …) ve OCR'ın karıştırdığı `i/l/1/|` karakterleri tek
harfe indirgenir. Sonuç `katii` tam kelimesine eşitse tıklanır:

| Metin | Sonuç |
|---|---|
| `Katıl`, `KATIL`, `Hemen Katıl`, `Kampanyaya Katıl`, OCR bozulmaları (`Katll`, `Kat1l`, `KatıI`) | ✅ tıklar |
| `Katıldınız`, `Katıldın`, `Katılım Sağla`, `Katkı`, `Katalog` | ⛔ atlar |
| 24 karakterden uzun açıklama satırları | ⛔ atlar |

Aynı butona `--dedupe-radius` (70pt) yarıçapında ve `--dedupe-seconds` (25 sn) içinde
ikinci kez dokunulmaz.

> **Not:** Bonus Flaş katıldıktan sonra buton metnini `Katıldınız` yapmıyor —
> katılmış kartlar **`Takip Et` / `Takip ve Detay`** gösteriyor. Yani "katılmışları
> metninden ayırt etme" garantisi yok; tekrar çalıştırmada aynı karta dokunabilir.

## Çalıştığını nasıl anlarım

Yeni bir uygulamada sırayla şu üç şeye bakın:

**1. `./bot calibrate`** — tek kare okur, gördüğü her metni koordinatıyla listeler.
Katıl sayılan satırların başında `KATIL →` yazar. Burada uygulamanın gerçek ekranını
görüyorsanız (kampanya isimleri, alt menü yazıları) okuma doğru demektir. Alakasız içerik
görüyorsanız yanlış pencere yakalanmıştır — telefon penceresinin önünü açın.

**2. `./kampanya.sh --dry-run`** — hiç tıklamadan listeyi kaydırır ve
`→ tık: 'Hemen Katıl' @ (x,y)` satırlarıyla **neye dokunacağını** yazar. Kaç tane hedef
bulduğunu buradan sayın. Yanlış bir şeye (açıklama metni, "Katıldınız") dokunacağını
görürseniz gerçek turu çalıştırmayın, bana çıktıyı gönderin.

**3. Gerçek tur** — çalışırken şu satırlar sağlıklı gidişin işaretidir:

| Çıktı | Anlamı |
|---|---|
| `alt menü imzası öğrenildi: ana sayfa, kampanyalar, …` | uygulama doğru tanındı |
| `→ tık: 'Hemen Katıl' @ (202,872)` | bir kampanyaya dokundu |
| `↳ sheet kapatılıyor (aşağı swipe)` | katılım sonrası açılan kutuyu kapattı |
| `↳ detay sayfasından geri dönülüyor` | dokunuş detay sayfası açtı, listeye döndü |
| `↔ yatay kaydırmalı satır: y=538` | yatay karusel buldu, sağa doğru tarıyor |
| `liste sonu (ekran değişmiyor)` | listeyi bitirdi, düzgün kapandı |
| `toplam dokunuş: 13` | kaç kampanyaya dokunduğu |

Şu satırlar ise **durmuş** demektir, sorun sizde değil ortamda:
`iPhone Mirroring bağlantısı kesilmiş` (telefonu kilitleyip Connect'e basın),
`pencerenin önünde başka pencere var: X` (X penceresini telefon penceresinin üstünden çekin),
`fare kullanıcı tarafından oynatıldı` (fareye dokunmayın veya `--no-guard` ekleyin).

**4. Telefonda son kontrol** — katılınan kartlar `Takip Et / Takip ve Detay`e döner.
Aynı komutu tekrar çalıştırmak zararsızdır (katılım tekrarı bir şey bozmaz) ama
katılmışları metninden ayırt edemediği için onlara tekrar dokunabilir.

## Kayıtlar

Her çalıştırma `~/.cache/mirror-bot/<tarih-saat>/` altına `log.jsonl` (her tık, koordinat,
zaman) ve son kareyi yazar.

## Bilinen sınırlar

- **Telefonu elinize alırsanız yansıtma kopar** ("iPhone Mirroring ended due to iPhone use").
  Bot bunu anlar ve durur; telefonu kilitleyip tekrar çalıştırın.
- Telefon penceresinin önüne başka pencere gelirse (WhatsApp bildirimi, Takvim vb.) bot
  durur — yanlış pencereye tıklamaması için kasıtlı.
- Katıl butonu yalnızca kart detayına girilince çıkan kampanyalar listede yakalanmaz.
- OCR görüntüye bağlıdır: pencereyi büyütmek isabeti artırır.
- Uygulamaların otomasyon karşıtı kuralları olabilir; kendi hesabınızda, başında durarak ve
  makul hızda kullanın. Yeni bir uygulamada önce `--dry-run` ile deneyin.
