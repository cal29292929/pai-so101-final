# Move the follower slowly to the blue-bowl start pose (median of teleop episode starts),
# so lerobot-rollout captures it as the "initial position" used for every reset.
import sys
import time

import cv2
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

START = {
    "shoulder_pan.pos": 12.0,
    "shoulder_lift.pos": 25.0,
    "elbow_flex.pos": -50.0,
    "wrist_flex.pos": 97.0,
    "wrist_roll.pos": 77.0,
    "gripper.pos": 43.0,
}

port = sys.argv[1] if len(sys.argv) > 1 else "COM7"
snap = sys.argv[2] if len(sys.argv) > 2 else None
cam = int(sys.argv[3]) if len(sys.argv) > 3 else 1

# Keep torque on after disconnect, otherwise the arm sags under gravity before rollout starts
robot = SO101Follower(
    SO101FollowerConfig(port=port, id="so101_follower_unit1", disable_torque_on_disconnect=False)
)
robot.connect(calibrate=False)
cur = {k: v for k, v in robot.get_observation().items() if k in START}
steps = 60
for i in range(1, steps + 1):
    a = i / steps
    robot.send_action({k: cur[k] + (START[k] - cur[k]) * a for k in START})
    time.sleep(0.05)
time.sleep(1.0)
print({k: round(v, 1) for k, v in robot.get_observation().items() if k in START})
robot.disconnect()

if snap:
    c = cv2.VideoCapture(cam, cv2.CAP_DSHOW)
    for _ in range(10):
        ok, f = c.read()
    if ok:
        cv2.imwrite(snap, f)
