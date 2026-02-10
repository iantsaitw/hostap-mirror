#!/bin/bash

# --- Configuration ---
INTERFACE="wlp174s0"
SUPPLICANT="./wpa_supplicant"
LOG_FILE="wpa_dev.log"
OLD_LOG="wpa_dev_old.log"

# Check if config file is provided
if [ -z "$1" ]; then
    echo "Usage: ./wpa_dev.sh <config_file>"
    exit 1
fi

TARGET_CONF=$1

# --- Log Rotation ---
# 如果發現已有 log，將其更名為 old.log (會覆蓋之前的 old.log)
if [ -f "$LOG_FILE" ]; then
    echo "[*] Found existing log, renaming to $OLD_LOG"
    mv "$LOG_FILE" "$OLD_LOG"
fi

# --- Environment Initialization ---
echo "------------------------------------------"
echo "[*] Cleaning up existing network processes..."
sudo systemctl stop NetworkManager 2>/dev/null
sudo killall wpa_supplicant 2>/dev/null
# Ensure the interface is clean
sudo ip addr flush dev $INTERFACE
sudo ip link set $INTERFACE down
sudo ip link set $INTERFACE up
sudo iw dev $INTERFACE set power_save off

echo "------------------------------------------"
echo "[*] Starting Live Debug Mode (Foreground)"
echo "[*] Using Config: $TARGET_CONF"
echo "[*] Log file: $LOG_FILE"
echo "[*] Press Ctrl+C to stop and cleanup"
echo "------------------------------------------"

# Launch wpa_supplicant in foreground
# 2>&1: 將標準錯誤(stderr)也轉向到標準輸出(stdout)，確保 error 也能被紀錄
# | tee "$LOG_FILE": 同時輸出到螢幕與檔案
sudo $SUPPLICANT -i $INTERFACE -D nl80211 -c "$TARGET_CONF" -t -dd -K 2>&1 | tee "$LOG_FILE"

# --- Post-Cleanup ---
echo -e "\n\n[*] Interrupt detected, cleaning up environment..."
sudo ip addr flush dev $INTERFACE
# Optional: restart NetworkManager
# sudo systemctl start NetworkManager
echo "[OK] Interface $INTERFACE IP flushed. Log saved to $LOG_FILE. Exit."
