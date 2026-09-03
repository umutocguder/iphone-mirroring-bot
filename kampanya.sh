#!/bin/sh
# Ekranda açık olan kampanya listesini (Bonus Flaş, Maximum Mobil, herhangi biri)
# baştan sona gezip bulduğu tüm "Katıl" butonlarına dokunur.
#
#   ./kampanya.sh              gerçek çalıştırma
#   ./kampanya.sh --dry-run    tıklamadan prova
#   ./kampanya.sh --max-taps 10 --after-tap 3   ayar ekleme
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/bot" run \
  --to-top \
  --max-taps 80 \
  --max-rounds 60 \
  --after-tap 2.2 \
  --after-scroll 1.2 \
  --hscroll -280 \
  "$@"
