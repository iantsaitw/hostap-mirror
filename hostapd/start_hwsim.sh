#!/bin/bash

# --- Configuration ---
INTERFACE="wlan1"
HOSTAPD_PATH="./hostapd"
LOG_FILE="start_hwsim.log"
OLD_LOG="start_hwsim_old.log"

# 檢查是否有輸入 config 檔案路徑
if [ -z "$1" ]; then
    echo "[!] Usage: $0 <your_config_file.conf>"
    exit 1
fi

CONF_FILE=$1

# --- Log Rotation (將舊 Log 重新命名為 _old.log) ---
if [ -f "$LOG_FILE" ]; then
    echo "[*] Found existing log, renaming to $OLD_LOG"
    mv "$LOG_FILE" "$OLD_LOG"
fi

echo "[*] Using config: $CONF_FILE"
echo "[*] Log file: $LOG_FILE"
echo "[*] Cleaning environment..."

# 1. 停用 NM 對該網卡的控制
sudo nmcli device set $INTERFACE managed no 2>/dev/null
# 2. 殺掉舊的進程
sudo killall hostapd 2>/dev/null
# 3. 確保 Wi-Fi 硬體沒被鎖住
sudo rfkill unblock wifi

# 4. 重置 IP 與介面
sudo ip addr flush dev $INTERFACE
sudo ip link set $INTERFACE up
sudo ip addr add 192.168.10.1/24 dev $INTERFACE

echo "------------------------------------------"
echo "[*] Starting hostapd (Raw Timestamp Mode)"
echo "[*] Press Ctrl+C to stop"
echo "------------------------------------------"

# 直接執行並存檔，保留原始 12345678.999 格式
# 2>&1 確保 stderr 的錯誤訊息也會被存入檔案
sudo $HOSTAPD_PATH -dd "$CONF_FILE" 2>&1 | tee "$LOG_FILE"

# --- Post-Cleanup ---
echo -e "\n[*] hostapd stopped, cleaning up..."
sudo ip addr flush dev $INTERFACE
echo "[OK] Log saved to $LOG_FILE. Exit."