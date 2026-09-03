#!/bin/sh
# Geriye dönük kısayol: kampanya.sh uygulamadan bağımsız çalışır.
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/kampanya.sh" "$@"
