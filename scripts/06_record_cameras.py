#!/usr/bin/env python3
"""Record SO-101 wrist camera + extra webcams to timestamped mp4 (one file per camera).

Windows (DirectShow via ffmpeg). Does NOT move the robot.
Usage:
  python scripts/06_record_cameras.py                      # default cameras
  python scripts/06_record_cameras.py --cam wrist="TSTC USB20 WEB CAMERA" --cam pc="Integrated Camera"
  python scripts/06_record_cameras.py --list               # list dshow devices
Stop with Ctrl+C. Output: outputs/recordings/<name>_YYYYmmdd_HHMMSS.mp4
"""
import argparse, datetime, pathlib, signal, subprocess, sys, time

DEFAULT = {"wrist": "TSTC USB20 WEB CAMERA", "pc": "Integrated Camera"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", action="append", default=[], help='name="DirectShow device name"')
    ap.add_argument("--out", default="outputs/recordings")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default=None, help="e.g. 640x480")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        subprocess.run(["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"])
        return
    cams = dict(c.split("=", 1) for c in a.cam) if a.cam else DEFAULT
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    procs = []
    for name, dev in cams.items():
        f = out / f"{name}_{ts}.mp4"
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "dshow",
               "-rtbufsize", "512M", "-framerate", str(a.fps)]
        if a.size:
            cmd += ["-video_size", a.size]
        cmd += ["-i", f"video={dev}", "-c:v", "libx264", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", str(f)]
        procs.append((name, f, subprocess.Popen(cmd, stdin=subprocess.PIPE)))
        print(f"[rec] {name}: {dev} -> {f}")
    print("Recording... Ctrl+C to stop.")
    try:
        while all(p.poll() is None for _, _, p in procs):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    for _, _, p in procs:
        if p.poll() is None:
            try:
                p.stdin.write(b"q"); p.stdin.flush()
            except Exception:
                p.send_signal(signal.SIGINT)
    for name, f, p in procs:
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
        print(f"[done] {name}: {f} rc={p.returncode}")

if __name__ == "__main__":
    sys.exit(main())
