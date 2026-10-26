#!/usr/bin/env bash
# ==============================================================================
# 第3回講義（コンピュータアーキテクチャ・デバイス管理）実践スクリプト
# - USBホストコントローラのツリー構造と帯域共有の確認
# - SO-101 サーボコントローラ (/dev/ttyACM*) のシリアル番号確認と udev ルール生成案
# - USBカメラ (/dev/video*) の認識・権限確認
# ==============================================================================
set -euo pipefail

echo "============================================================"
echo "[1/4] Checking User Groups (dialout / video)"
echo "============================================================"
id -nG | tr ' ' '\n' | grep -E '^(dialout|video)$' || echo "INFO: Consider adding user to dialout and video groups: sudo usermod -aG dialout,video \$USER"

echo ""
echo "============================================================"
echo "[2/4] Checking USB Tree & Bandwidth Sharing (Lecture 3)"
echo "============================================================"
if command -v lsusb >/dev/null 2>&1; then
  lsusb -t || true
else
  echo "lsusb not installed; checking /sys/bus/usb/devices..."
  ls -1 /sys/bus/usb/devices/ || true
fi

echo ""
echo "============================================================"
echo "[3/4] Checking Serial Ports for SO-101 Leader / Follower"
echo "============================================================"
shopt -s nullglob
serial_ports=(/dev/ttyACM* /dev/ttyUSB*)
if [ ${#serial_ports[@]} -eq 0 ]; then
  echo "No /dev/ttyACM* or /dev/ttyUSB* detected right now."
else
  for dev in "${serial_ports[@]}"; do
    echo "--- Device: $dev ---"
    if command -v udevadm >/dev/null 2>&1; then
      udevadm info -a -n "$dev" | grep -E 'ATTRS\{(idVendor|idProduct|serial)\}' | head -n 6 || true
    fi
  done
fi

echo ""
echo "============================================================"
echo "[4/4] Checking Cameras (/dev/video*)"
echo "============================================================"
video_ports=(/dev/video*)
if [ ${#video_ports[@]} -eq 0 ]; then
  echo "No /dev/video* detected right now."
else
  for vdev in "${video_ports[@]}"; do
    echo "Found camera node: $vdev"
  done
fi

cat << 'UDEV_EOF'

------------------------------------------------------------
[Recommended udev Rule Example: /etc/udev/rules.d/99-so101.rules]
# 第3回講義 p.67-70: 再起動や抜き差しで /dev/ttyACM0 や /dev/video0 が入れ替わるのを防ぐため
# シリアル番号で固定シンボリックリンクを作成します:
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{serial}=="<LEADER_SERIAL>", SYMLINK+="ttySO101_leader_1", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{serial}=="<FOLLOWER_SERIAL>", SYMLINK+="ttySO101_follower_1", MODE="0666"
------------------------------------------------------------
UDEV_EOF
