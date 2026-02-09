#!/bin/bash

# --- Configuration ---
INTERFACE="wlp3s0" 
SUPPLICANT="./wpa_supplicant"
LOG_FILE="wpa_stable.log"
OLD_LOG="wpa_stable_old.log"

# Network Settings (模擬環境的 IP)
STATIC_IP="192.165.100.201/16"
AP_IP="192.165.100.221"

if [ -z "$1" ]; then
    echo "Usage: $0 <config_file>"
    exit 1
fi

TARGET_CONF=$1

# --- Function: Connection Monitor ---
check_and_monitor() {
    echo "[*] Monitoring connection state..."
    local count=0
    local max_wait=20
    
    while [ $count -lt $max_wait ]; do
        # 使用 sudo 執行 wpa_cli 確保權限
        local raw_status=$(sudo ./wpa_cli -i $INTERFACE status 2>/dev/null)
        local current_state=$(echo "$raw_status" | grep "wpa_state=" | cut -d= -f2)
        
        if [[ "$current_state" == "COMPLETED" ]]; then
            echo -e "\n[✓] L2 Connected (Completed)!"
            
            # --- IP Provisioning ---
            echo "[*] Setting Static IP: $STATIC_IP..."
            sudo ip addr add $STATIC_IP dev $INTERFACE 2>/dev/null
            
            local iw_link=$(sudo iw dev $INTERFACE link)
            echo "--------- Connection Summary ---------"
            echo "SSID   : $(echo "$raw_status" | grep "^ssid=" | cut -d= -f2)"
            echo "BSSID  : $(echo "$raw_status" | grep "^bssid=" | cut -d= -f2)"
            # hwsim 的訊號通常是固定的或由 cfg80211 模擬
            echo "Signal : $(echo "$iw_link" | grep "signal:" | awk '{print $2, $3}')"
            echo "--------------------------------------"
            
            echo "[*] Testing Reachability to AP ($AP_IP)..."
            # 先試 ping 3 次
            if ping -c 3 $AP_IP > /dev/null 2>&1; then
                echo "[✓] Ping Success!"
                echo "[*] Starting Continuous Ping. (Press Ctrl+C to return to menu)"
                ping $AP_IP
            else
                echo "[!] Ping Failed! Please check if hostapd is running and IP is set to $AP_IP."
            fi
            return 0
        fi
        echo -ne "\r[Status: ${current_state:-SCANNING}] [Wait: $((max_wait-count))s]...   "
        sleep 1
        ((count++))
    done
    echo -e "\n[!] Connection attempt timed out."
    return 1
}

# --- Initialization ---
echo "=========================================="
echo "   Hwsim Dev Tool - Stable Version"
echo "=========================================="

# 0. Load Hwsim Module (如果還沒載入)
if ! lsmod | grep -q "mac80211_hwsim"; then
    echo "[*] Loading mac80211_hwsim module (radios=2)..."
    sudo modprobe mac80211_hwsim radios=2
    sleep 1
fi

# 1. Log Rotation
if [ -f "$LOG_FILE" ]; then
    echo "[*] Rotating old log to $OLD_LOG"
    mv "$LOG_FILE" "$OLD_LOG"
fi

# 2. Network Cleanup
echo "[*] Cleaning up network environment..."
sudo systemctl stop NetworkManager 2>/dev/null
sudo killall wpa_supplicant 2>/dev/null

# 重置介面狀態
sudo ip addr flush dev $INTERFACE
sudo ip link set $INTERFACE down
sudo ip link set $INTERFACE up
sudo rfkill unblock wifi

# 3. Start Supplicant
echo "[*] Launching $SUPPLICANT in BACKGROUND..."
# -B: Background (背景執行)
# -t: Include timestamp (Unix Epoch)
# -f: Log to file
# -dd: Debug level
sudo $SUPPLICANT -i $INTERFACE -D nl80211 -c "$TARGET_CONF" -B -t -dd -f "$LOG_FILE"
sleep 1

# 修正 Log 權限，讓你不用 sudo 也能看
if [ -f "$LOG_FILE" ]; then
    sudo chown $USER:$USER "$LOG_FILE"
fi

echo "[TIP] To see live logs, run this in another terminal:"
echo "      tail -f $(pwd)/$LOG_FILE"
echo "------------------------------------------"

# Auto-connect on start
check_and_monitor

# --- Menu Loop ---
while true; do
    echo ""
    echo ">> Menu: [c]onnect | [d]isconnect | [r]estart | [l]og_clear | [q]uit"
    read -p ">> Action: " opt

    case $opt in
        [Cc]* ) 
            echo "[*] Reassociating..."
            sudo ./wpa_cli -i $INTERFACE reassociate > /dev/null
            check_and_monitor
            ;;
        [Dd]* ) 
            sudo ./wpa_cli -i $INTERFACE disconnect > /dev/null
            sudo ip addr flush dev $INTERFACE
            echo "[*] Disconnected and IP flushed." 
            ;;
        [Rr]* ) 
            echo "[*] Restarting wpa_supplicant..."
            sudo killall wpa_supplicant 2>/dev/null
            # 使用 exec 重新執行自己，達到完全重啟效果
            exec "$0" "$TARGET_CONF" 
            ;;
        [Ll]* )
            # 清空 Log 檔
            > "$LOG_FILE"
            echo "[*] Log file cleared ($LOG_FILE)."
            ;;
        [Qq]* ) 
            echo "[*] Cleaning up and Exiting..."
            sudo killall wpa_supplicant 2>/dev/null
            # 注意：這裡不卸載 mac80211_hwsim，避免影響其他視窗的 hostapd
            exit 0 
            ;;
        * ) echo "Invalid option." ;;
    esac
done
