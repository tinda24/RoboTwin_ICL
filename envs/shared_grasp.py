import os

import numpy as np

from ._base_task import Base_Task
from .shared_table import GRASP_PLAN, TABLE_OBJECTS, build_shared_table
from .utils import *


class shared_grasp(Base_Task):
    """Grasp one shared-table object and lift it when it is free to move.

    The object name comes from SHARED_GRASP_OBJECT. The contact id in
    GRASP_PLAN keeps the open fingers on the empty lane of that slot, and
    the wrist roll is locked so the fingers do not swing into a neighbor.
    """

    def setup_demo(self, **kwags):
        self.scene_seed = kwags.get("seed", 0)
        super()._init_task_env_(**kwags)

    def load_actors(self):
        name = os.environ.get("SHARED_GRASP_OBJECT", "")
        plan = GRASP_PLAN.get(name)
        if plan is None:
            raise RuntimeError(f"{name} has no pinch contact on the shared table")
        arm_name, contact_id = plan
        self.table_objects = build_shared_table(self, self.scene_seed)
        self.specs = {spec["name"]: spec for spec in TABLE_OBJECTS}
        self.target_name = name
        self.target = self.table_objects[name]["actor"]
        self.arm_tag = ArmTag(arm_name)
        self.grasp_contact = int(contact_id)
        spec = self.specs[name]
        self.target_static = bool(spec.get("static")) or spec["kind"] == "urdf"
        self.rest = {
            obj_name: np.array(info["actor"].get_pose().p, dtype=np.float64)
            for obj_name, info in self.table_objects.items()
        }

    def _lock_wrist(self):
        self.robot.left_rotate_lim = [0, 0]
        self.robot.right_rotate_lim = [0, 0]

    def _gripper_touching(self, actor_name):
        return len(self.get_gripper_actor_contact_position(actor_name)) > 0

    def play_once(self):
        self._lock_wrist()
        arm_tag = self.arm_tag
        for obj_name, info in self.table_objects.items():
            self.rest[obj_name] = np.array(info["actor"].get_pose().p, dtype=np.float64)
        self.move(
            self.grasp_actor(
                self.target,
                arm_tag=arm_tag,
                pre_grasp_dis=0.08,
                contact_point_id=self.grasp_contact,
            )
        )
        if not self.target_static:
            self.move(self.move_by_displacement(arm_tag=arm_tag, z=0.06))
        self.info["info"] = {
            "{A}": self.target_name.replace("_", " "),
            "{a}": str(arm_tag),
        }
        return self.info

    def check_success(self):
        closed = (
            self.robot.is_left_gripper_close()
            if str(self.arm_tag) == "left"
            else self.robot.is_right_gripper_close()
        )
        if not closed or not self._gripper_touching(self.target_name):
            return False
        for name, info in self.table_objects.items():
            if name == self.target_name:
                continue
            if self._gripper_touching(name):
                return False
            if self.specs[name].get("static") or self.specs[name]["kind"] == "urdf":
                continue
            now = np.array(info["actor"].get_pose().p, dtype=np.float64)
            if np.linalg.norm(now[:2] - self.rest[name][:2]) > 0.015:
                return False
        if not self.target_static:
            now = np.array(self.target.get_pose().p, dtype=np.float64)
            if now[2] < self.rest[self.target_name][2] + 0.03:
                return False
        return True
