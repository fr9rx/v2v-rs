#!/usr/bin/env sh
set -eu

if [ "${1-}" = "" ] || [ "${2-}" = "" ]; then
    echo "Usage: run-firmware.sh gateway|transceiver esp32|esp32s2|esp32s3|esp32c3|esp32c5|esp32c6"
    exit 1
fi

PROJECT="$1"
BOARD="$2"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

case "$BOARD" in
    esp32) TARGET="xtensa-esp32-none-elf" ;;
    esp32s2) TARGET="xtensa-esp32s2-none-elf" ;;
    esp32s3) TARGET="xtensa-esp32s3-none-elf" ;;
    esp32c3) TARGET="riscv32imc-unknown-none-elf" ;;
    esp32c5) TARGET="riscv32imac-unknown-none-elf" ;;
    esp32c6) TARGET="riscv32imac-unknown-none-elf" ;;
    *)
        echo "Unknown board: $BOARD"
        exit 1
        ;;
esac

cd "$ROOT/$PROJECT"
exec cargo run --release --no-default-features --features "$BOARD" --target "$TARGET"
