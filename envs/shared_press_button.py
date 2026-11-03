import numpy as np
import transforms3d as t3d

from ._base_task import Base_Task
from ._GLOBAL_CONFIGS import GRASP_DIRECTION_DIC
from .shared_table import TABLE_OBJECTS, build_shared_table
from .utils import *


class shared_press_button(Base_Task):
    """Press the shared-table button with a closed gripper.

    The cap travels 6 mm. A weak spring holds it up until the gripper pushes
    it down, and the fingers stay closed so they do not sweep sideways.
    """

    def setup_demo(self, **kwags):
        self.scene_seed = kwags.get("seed", 0)
        super()._init_task_env_(**kwags)

    def load_actors(self):
        self.table_objects = build_shared_table(self, self.scene_seed)
        self.specs = {spec["name"]: spec for spec in TABLE_OBJECTS}
        self.button = self.table_objects["button"]["actor"]
        self.arm_tag = ArmTag("left")
        self._hold_button_up()
        self.rest = {}

    def _hold_button_up(self):
        for joint in self.button.actor.get_joints():
            if joint.get_name() != "button_joint":
                continue
            joint.set_drive_properties(damping=5.0, stiffness=400.0, force_limit=20.0)
            joint.set_drive_target(0.0)
        self.button.set_qpos(np.array([0.0], dtype=np.float64))

    def _button_q(self):
        return float(np.array(self.button.get_qpos()).reshape(-1)[0])

    def _press_pose(self, quat, retreat):
        # Fingertip frame. left_plan_path shifts this onto the end link.
        contact = np.array(self.button.get_contact_point(0, "list")[:3], dtype=np.float64)
        rotation = t3d.quaternions.quat2mat(quat)
        position = contact + rotation @ np.array([-0.12 - retreat, 0.0, 0.0])
        return position.tolist() + list(quat)

    def _choose_press_pose(self, arm_tag):
        plan = self.robot.left_plan_path if arm_tag == "left" else self.robot.right_plan_path
        for name in ("top_down_little_right", "top_down", "top_down_little_left"):
            quat = GRASP_DIRECTION_DIC[name]
            hover = self._press_pose(quat, 0.04)
            if plan(hover)["status"] == "Success":
                return hover, self._press_pose(quat, 0.008)
        return None, None

    def play_once(self):
        arm_tag = self.arm_tag
        self.robot.left_rotate_lim = [0, 0]
        self.robot.right_rotate_lim = [0, 0]
        self._hold_button_up()
        self.rest_q = self._button_q()
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
        self.info["info"] = {"{A}": "button", "{a}": str(arm_tag)}
        return self.info

    def check_success(self):
        if not self.robot.is_left_gripper_close():
            return False
        if self._button_q() > self.rest_q - 0.003:
            return False
        for name, info in self.table_objects.items():
            spec = self.specs[name]
            if spec.get("static") or spec["kind"] == "urdf":
                continue
            now = np.array(info["actor"].get_pose().p, dtype=np.float64)
            if np.linalg.norm(now[:2] - self.rest[name][:2]) > 0.015:
                return False
        return True
