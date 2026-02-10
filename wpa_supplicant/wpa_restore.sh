#!/bin/bash

# --- Configuration ---
INTERFACE="wlp3s0"

echo "------------------------------------------"
echo "[*] Restoring System Network Environment..."
echo "------------------------------------------"

# 1. Kill manual testing processes
echo "[1/4] Stopping manual test processes..."
sudo killall wpa_supplicant 2>/dev/null
sudo killall wpa_cli 2>/dev/null

# 2. Cleanup Network Interface
echo "[2/4] Cleaning up interface $INTERFACE..."
# Flush the static IP we manually assigned
sudo ip addr flush dev $INTERFACE
# Bring the link down and up to reset hardware state
sudo ip link set $INTERFACE down
sudo ip link set $INTERFACE up
# Re-enable WiFi Power Save (Optional, good for laptops)
sudo iw dev $INTERFACE set power_save on
sudo rfkill unblock wifi

# 3. Restart NetworkManager
echo "[3/4] Restarting NetworkManager service..."
sudo systemctl start NetworkManager

# 4. Wait for NM to initialize and take control
echo "[4/4] Waiting for NetworkManager to re-scan..."
sleep 3

# Show current status
echo "------------------------------------------"
echo "Current Device Status:"
nmcli device status | grep -E "DEVICE|TYPE|STATE|$INTERFACE"
echo "------------------------------------------"
echo "[OK] Restoration Complete!"
echo "[*] Your Wi-Fi icon should reappear shortly."