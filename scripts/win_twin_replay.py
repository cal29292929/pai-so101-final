"""Digital-twin replay: SO-101 MuJoCo render beside the real wrist camera.

Usage:
  python scripts/win_twin_replay.py [--dataset DIR] [--episode N] [--out PATH] [--seconds S]
  python scripts/win_twin_replay.py --still   # sanity-check stills only

Mapping (LeRobot degrees -> so101_new_calib.xml qpos): the new_calib model has joint zero at the
middle of each range, same as LeRobot's calibrated degrees. Arm joints: qpos = SIGN[j]*deg2rad(state).
Gripper 0..100 -> joint range [-0.1745, 1.7453] linearly. SIGN is documented below.
"""
import argparse, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd, cv2, mujoco

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "sim" / "so101" / "scene.xml"
DEFAULT_DS = Path.home() / ".cache/huggingface/lerobot/local/so101_catfood_transfer_20261101_050202"
OUT_DIR = Path("E:/pai_video/twin")
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
SIGN = np.array([1, 1, 1, 1, 1], dtype=float)  # per-joint sign flips (see README / report)
W, H, FPS = 640, 480, 30


def load_episode(ds: Path, ep: int):
    meta = pd.concat([pd.read_parquet(f) for f in sorted((ds / "meta/episodes").glob("chunk-*/file-*.parquet"))])
    m = meta[meta.episode_index == ep].iloc[0]
    df = pd.concat([pd.read_parquet(f) for f in sorted((ds / "data").glob("chunk-*/file-*.parquet"))])
    df = df[df.episode_index == ep].sort_values("frame_index") if "frame_index" in df else df[df.episode_index == ep]
    state = np.stack(df["observation.state"].to_numpy()).astype(np.float64)
    k = "videos/observation.images.wrist/"
    vid = ds / f"videos/observation.images.wrist/chunk-{int(m[k+'chunk_index']):03d}/file-{int(m[k+'file_index']):03d}.mp4"
    return state, vid, float(m[k + "from_timestamp"])


def make_model():
    model = mujoco.MjModel.from_xml_path(str(SCENE))
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(model.njnt)]
    print("MuJoCo joints (qpos order):", names)
    return model, names


def state_to_qpos(model, state):
    q = np.zeros(model.nq)
    q[:5] = SIGN * np.deg2rad(state[:5])
    lo, hi = model.jnt_range[5]
    q[5] = lo + (np.clip(state[5], 0, 100) / 100.0) * (hi - lo)
    return q


def camera():
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = [0.15, 0.0, 0.10]
    cam.distance, cam.azimuth, cam.elevation = 0.7, 120, -20
    return cam


def label(img, text):
    cv2.rectangle(img, (0, 0), (img.shape[1], 34), (0, 0, 0), -1)
    cv2.putText(img, text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, default=DEFAULT_DS)
    ap.add_argument("--episode", type=int, default=2)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--still", action="store_true")
    a = ap.parse_args()

    model, _ = make_model()
    data = mujoco.MjData(model)
    state, vid, t0 = load_episode(a.dataset, a.episode)
    n = min(len(state), int(a.seconds * FPS))
    print(f"episode {a.episode}: {len(state)} frames, using {n}; video {vid} @ {t0}s")
    cam = camera()
    r = mujoco.Renderer(model, H, W)

    def render(i):
        data.qpos[:] = state_to_qpos(model, state[i])
        mujoco.mj_forward(model, data)
        r.update_scene(data, cam)
        return r.render().copy()

    if a.still:
        idx = np.linspace(0, n - 1, 9).astype(int)
        tiles = [label(cv2.cvtColor(render(i), cv2.COLOR_RGB2BGR), f"sim f{i}") for i in idx]
        sheet = np.vstack([np.hstack(tiles[k:k + 3]) for k in (0, 3, 6)])
        cv2.imwrite(str(OUT_DIR / "still_sheet.jpg"), cv2.resize(sheet, None, fx=0.5, fy=0.5))
        return

    out = a.out or OUT_DIR / f"twin_ep{a.episode}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(t0), "-i", str(vid), "-frames:v", str(n),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{2*W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
                            "-threads", "1", str(out)], stdin=subprocess.PIPE)
    sheet_idx = set(np.linspace(0, n - 1, 9).astype(int))
    sheet_tiles = {}
    for i in range(n):
        raw = dec.stdout.read(W * H * 3)
        real = np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy() if len(raw) == W * H * 3 else np.zeros((H, W, 3), np.uint8)
        frame = np.hstack([label(render(i), "Digital Twin (MuJoCo)"), label(real, "Real wrist camera")])
        enc.stdin.write(frame.tobytes())
        if i in sheet_idx:
            sheet_tiles[i] = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), (640, 240))
    enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()
    tiles = [sheet_tiles[i] for i in sorted(sheet_tiles)]
    sheet = np.vstack([np.hstack(tiles[k:k + 3]) for k in (0, 3, 6)])
    cv2.imwrite(str(out.with_name(out.stem + "_sheet.jpg")), sheet)
    print("wrote", out)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    main()
