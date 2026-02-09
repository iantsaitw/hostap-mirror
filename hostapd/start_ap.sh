#!/bin/bash

# 檢查是否有輸入 config 檔案路徑
if [ -z "$1" ]; then
    echo "[!] Usage: $0 <your_config_file.conf>"
    exit 1
fi

CONF_FILE=$1
# 指向你剛編好的新版執行檔路徑 (請根據你的實際目錄修改)
HOSTAPD_PATH="./hostapd" 
IFACE="wlo1"

echo "[*] Using config: $CONF_FILE"
echo "[*] Cleaning environment..."

# 1. 停用 NM 對該網卡的控制
sudo nmcli device set $IFACE managed no 2>/dev/null
# 2. 殺掉舊的進程
sudo killall hostapd 2>/dev/null
# 3. 確保 Wi-Fi 硬體沒被鎖住
sudo rfkill unblock wifi

# 4. 重置 IP 與介面
sudo ip addr flush dev $IFACE
sudo ip link set $IFACE up
sudo ip addr add 192.168.10.1/24 dev $IFACE

echo "[*] Starting NEW hostapd with Wi-Fi 7 support..."
# 使用 -dd 模式，我們才能看到 6.19 Kernel 跟 hostapd 握手的底層訊息
sudo $HOSTAPD_PATH -dd "$CONF_FILE"
