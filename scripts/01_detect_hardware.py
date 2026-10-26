#!/usr/bin/env python3
"""
01_detect_hardware.py
SO-101 (Feetech STS3215) USBシリアルポートおよび UVC カメラ（リストカメラ・俯瞰カメラ）を自動検出し、
configs/so101_task_config.yaml のハードウェア設定を更新・診断するスクリプト。
"""
from __future__ import annotations

import argparse
import glob
import json
import platform
import sys
from pathlib import Path
from typing import Any

import yaml


def scan_serial_ports() -> list[dict[str, Any]]:
    """OSに応じたSO-101用USBシリアルデバイスを列挙する。"""
    patterns = [
        "/dev/ttyACM*",
        "/dev/ttyUSB*",
        "/dev/cu.usbmodem*",
        "/dev/cu.usbserial*",
    ]
    found: list[str] = []
    for pat in patterns:
        found.extend(sorted(glob.glob(pat)))

    results: list[dict[str, Any]] = []
    try:
        from serial.tools import list_ports  # type: ignore

        port_map = {p.device: p for p in list_ports.comports()}
    except Exception:
        port_map = {}

    for dev in sorted(set(found)):
        info = port_map.get(dev)
        results.append(
            {
                "device": dev,
                "description": getattr(info, "description", "USB Serial (STS3215 / CH340 / CP210x)"),
                "vid_pid": f"{getattr(info, 'vid', 0) or 0:04x}:{getattr(info, 'pid', 0) or 0:04x}"
                if info
                else "unknown",
                "serial_number": getattr(info, "serial_number", None),
            }
        )
    return results


def scan_cameras(max_index: int = 6) -> list[dict[str, Any]]:
    """OpenCVを用いて接続済みのUVCカメラ（リストカメラ等）を検出する。"""
    cameras: list[dict[str, Any]] = []
    try:
        import cv2
    except ImportError:
        return cameras

    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap is not None and cap.isOpened():
            ok, frame = cap.read()
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
            cap.release()
            if ok and frame is not None:
                cameras.append(
                    {
                        "index": idx,
                        "resolution": f"{width}x{height}",
                        "fps": round(fps, 1),
                    }
                )
        else:
            if cap is not None:
                cap.release()
    return cameras


def update_config_file(
    config_path: Path,
    ports: list[dict[str, Any]],
    cameras: list[dict[str, Any]],
) -> dict[str, Any]:
    """検出されたポートとカメラを設定ファイルに反映する（未検出時はデフォルト値を維持）。"""
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    arms = cfg.setdefault("hardware", {}).setdefault("arms", {})
    if len(ports) >= 1:
        arms["follower_1"]["port"] = ports[0]["device"]
    if len(ports) >= 2:
        arms["leader_1"]["port"] = ports[1]["device"]
    if len(ports) >= 4:
        cfg["hardware"]["mode"] = "bimanual"
        arms["follower_2"]["enabled"] = True
        arms["follower_2"]["port"] = ports[2]["device"]
        arms["leader_2"]["enabled"] = True
        arms["leader_2"]["port"] = ports[3]["device"]

    cams_cfg = cfg["hardware"].setdefault("cameras", {})
    if len(cameras) >= 1:
        cams_cfg["wrist_cam"]["index_or_path"] = cameras[0]["index"]
    if len(cameras) >= 2:
        cams_cfg["top_cam"]["enabled"] = True
        cams_cfg["top_cam"]["index_or_path"] = cameras[1]["index"]

    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)

    return cfg


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect SO-101 serial ports and UVC wrist camera.")
    parser.add_argument(
        "--write-config",
        type=Path,
        default=Path("configs/so101_task_config.yaml"),
        help="Path to YAML config file to inspect/update.",
    )
    parser.add_argument("--json", action="store_true", help="Print detection summary as JSON.")
    args = parser.parse_args()

    ports = scan_serial_ports()
    cameras = scan_cameras()

    summary = {
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "detected_serial_ports": ports,
        "detected_cameras": cameras,
        "recommended_topology": (
            "bimanual_4_arms"
            if len(ports) >= 4
            else ("single_unit_leader_follower" if len(ports) >= 2 else "simulation_or_single_arm")
        ),
    }

    if args.write_config.exists():
        update_config_file(args.write_config, ports, cameras)
        summary["updated_config"] = str(args.write_config)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("=" * 68)
        print(" SO-101 Hardware & Wrist Camera Diagnostic")
        print("=" * 68)
        print(f"OS / Python       : {summary['os']} / Python {summary['python']}")
        print(f"Serial Ports Found: {len(ports)}")
        for i, p in enumerate(ports):
            role_hint = ["follower_1", "leader_1", "follower_2", "leader_2"][i] if i < 4 else f"extra_{i}"
            print(f"  - [{role_hint}] {p['device']} ({p['description']}, VID:PID={p['vid_pid']})")
        if not ports:
            print("  (No USB serial ports detected right now; default ports in YAML preserved for dry-run)")

        print(f"UVC Cameras Found : {len(cameras)}")
        for i, c in enumerate(cameras):
            cam_role = "wrist_cam (Eye-in-Hand)" if i == 0 else f"top_cam_{i}"
            print(f"  - [{cam_role}] index={c['index']} ({c['resolution']} @ {c['fps']}fps)")
        if not cameras:
            print("  (No UVC cameras detected right now; synthetic wrist-camera feed available in --dry-run)")
        print(f"Config Updated    : {args.write_config}")
        print("=" * 68)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
