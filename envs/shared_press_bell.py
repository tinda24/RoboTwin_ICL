import numpy as np
import transforms3d as t3d

from ._base_task import Base_Task
from ._GLOBAL_CONFIGS import GRASP_DIRECTION_DIC
from .shared_table import TABLE_OBJECTS, build_shared_table
from .utils import *


class shared_press_bell(Base_Task):
    """Touch the top of the shared-table bell with a closed gripper."""

    def setup_demo(self, **kwags):
        self.scene_seed = kwags.get("seed", 0)
        super()._init_task_env_(**kwags)

    def load_actors(self):
        self.table_objects = build_shared_table(self, self.scene_seed)
        self.specs = {spec["name"]: spec for spec in TABLE_OBJECTS}
        self.bell = self.table_objects["bell"]["actor"]
        self.arm_tag = ArmTag("right")
        self.rest = {}

    def _press_pose(self, quat, retreat):
        contact = np.array(self.bell.get_contact_point(0, "list")[:3], dtype=np.float64)
        rotation = t3d.quaternions.quat2mat(quat)
        position = contact + rotation @ np.array([-0.12 - retreat, 0.0, 0.0])
        return position.tolist() + list(quat)

    def _choose_press_pose(self, arm_tag):
        plan = self.robot.left_plan_path if arm_tag == "left" else self.robot.right_plan_path
        for name in ("top_down_little_left", "top_down", "top_down_little_right"):
            quat = GRASP_DIRECTION_DIC[name]
            hover = self._press_pose(quat, 0.05)
            if plan(hover)["status"] == "Success":
                return hover, self._press_pose(quat, 0.0)
        return None, None

    def play_once(self):
        arm_tag = self.arm_tag
        self.robot.left_rotate_lim = [0, 0]
        self.robot.right_rotate_lim = [0, 0]
        self.rest = {
            name: np.array(info["actor"].get_pose().p, dtype=np.float64)
            for name, info in self.table_objects.items()
        }
        self.move(self.close_gripper(arm_tag=arm_tag, pos=0.0))
        hover, press = self._choose_press_pose(arm_tag)
        if hover is None:
            raise RuntimeError("no reachable press pose")
        self.move((
            arm_tag,
            [
                Action(arm_tag, "move", target_pose=hover),
                Action(arm_tag, "move", target_pose=press, constraint_pose=[1, 1, 1, 0, 0, 0]),
            ],
        ))
        self.info["info"] = {"{A}": "bell", "{a}": str(arm_tag)}
        return self.info

    def check_success(self):
        closed = self.robot.is_right_gripper_close() if str(self.arm_tag) == "right" else self.robot.is_left_gripper_close()
        if not closed:
            return False
        top = np.array(self.bell.get_contact_point(0, "list")[:3], dtype=np.float64)
        hit = False
        for position in self.get_gripper_actor_contact_position("bell"):
            delta = np.array(position, dtype=np.float64) - top
            if abs(delta[0]) < 0.03 and abs(delta[1]) < 0.03 and abs(delta[2]) < 0.04:
                hit = True
                break
        if not hit:
            return False
        for name, info in self.table_objects.items():
            spec = self.specs[name]
            if spec.get("static") or spec["kind"] == "urdf":
                continue
            now = np.array(info["actor"].get_pose().p, dtype=np.float64)
            if np.linalg.norm(now[:2] - self.rest[name][:2]) > 0.015:
                return False
        return True
