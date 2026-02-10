#!/bin/bash

# --- Configuration ---
IFACE="wlan1"

echo "=========================================="
echo "   AP Operational Status Checker (v2.0)"
echo "=========================================="

# 1. Improved Process Check
# Using 'pidof' and wider 'pgrep' to find any hostapd instance
echo -n "[1] Hostapd Process: "
PID=$(pidof hostapd)
if [ -z "$PID" ]; then
    echo "FAILED (Not found via pidof)"
else
    echo "OK (PID: $PID)"
fi

# 2. Interface Status with Details
echo -n "[2] Interface $IFACE: "
# Check if interface exists and get its flags
IF_INFO=$(ip addr show $IFACE 2>/dev/null)
if [ -z "$IF_INFO" ]; then
    echo "FAILED (Interface does not exist)"
else
    # Check for 'UP' flag in ip link
    if echo "$IF_INFO" | grep -q "UP"; then
        IP_ADDR=$(echo "$IF_INFO" | grep "inet " | awk '{print $2}')
        echo "OK (UP, IP: ${IP_ADDR:-ASSIGNING...})"
    else
        echo "FAILED (Link is DOWN)"
    fi
fi

# 3. Wireless Radio Details
echo "[3] Wireless Hardware Status:"
IW_LINK=$(sudo iw dev $IFACE info 2>/dev/null)
if [ ! -z "$IW_LINK" ]; then
    # 提取頻率、頻道與頻寬 (Width)
    CHAN_INFO=$(echo "$IW_LINK" | grep "channel" | sed 's/^[ \t]*//')
    TYPE_INFO=$(echo "$IW_LINK" | grep "type" | awk '{print $2}')
    echo "    - Mode    : $TYPE_INFO"
    echo "    - $CHAN_INFO"
else
    echo "    - Error: Could not retrieve radio status."
fi

# 4. Station (Client) Count
echo "[4] Connected Clients:"
# 這裡嘗試從 iw dev 抓取，這比 hostapd_cli 有時候更直接
STATIONS=$(sudo iw dev $IFACE station dump | grep "Station" | awk '{print $2}')
if [ -z "$STATIONS" ]; then
    echo "    - No clients connected."
else
    COUNT=$(echo "$STATIONS" | wc -l)
    echo "    - Total: $COUNT station(s)"
    for mac in $STATIONS; do
        echo "    - MAC: $mac"
    done
fi

echo "=========================================="
