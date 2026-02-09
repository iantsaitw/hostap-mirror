#!/bin/bash
# God Mode: No cleanup needed!
echo "[*] Ensuring hwsim0 is UP..."
sudo ip link set hwsim0 up
echo "[*] Starting Wireshark on hwsim0..."
sudo -H wireshark -i hwsim0 -k