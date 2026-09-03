#!/bin/sh
# Maximum Mobil uygulamasında "katıl" araması yapıp çıkan tüm kampanyalara katılır.
#
#   ./maximum.sh              gerçek çalıştırma
#   ./maximum.sh --dry-run    tıklamadan prova
#
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/bot" run \
  --search "katıl" \
  --to-top \
  --max-taps 80 \
  --max-rounds 50 \
  --after-tap 2.2 \
  --after-scroll 1.2 \
  --popup-ok "tamam,kapat,onayla,devam,harika" \
  "$@"
