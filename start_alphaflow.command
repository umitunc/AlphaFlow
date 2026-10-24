#!/bin/bash
# AlphaFlow Studio Pro — macOS Çift Tıklama Başlatıcısı (.command)
cd "$(dirname "$0")"
echo "[AlphaFlow Studio Pro - macOS] Başlatılıyor ve bağımlılıklar kontrol ediliyor..."

if command -v python3 &>/dev/null; then
    python3 main.py
else
    echo "HATA: macOS üzerinde Python 3 bulunamadı. Lütfen 'brew install python' veya python.org üzerinden kurun."
    read -p "Çıkmak için Enter tuşuna basın..."
fi
