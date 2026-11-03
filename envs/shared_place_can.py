from ._base_task import Base_Task
from .shared_table import build_shared_table
from .utils import *


class shared_place_can(Base_Task):

    def setup_demo(self, **kwags):
        self.scene_seed = kwags.get("seed", 0)
        super()._init_task_env_(**kwags)

    def load_actors(self):
        self.table_objects = build_shared_table(self, self.scene_seed)
        self.can = self.table_objects["can"]["actor"]
        self.can_id = self.table_objects["can"]["model_id"]
        self.blue_pad = self.table_objects["blue_pad"]["actor"]
        self.arm_tag = ArmTag("left")

    def play_once(self):
        arm_tag = self.arm_tag
        self.can_rest_z = float(self.can.get_pose().p[2])
        self.move(self.grasp_actor(self.can, arm_tag=arm_tag, pre_grasp_dis=0.08, gripper_pos=0))
        self.move(self.move_by_displacement(arm_tag=arm_tag, z=0.05))
        target_pose = self.blue_pad.get_functional_point(1)
        self.move(
            self.place_actor(
                self.can,
                arm_tag=arm_tag,
                target_pose=target_pose,
                pre_dis=0.05,
                dis=0,
                pre_dis_axis="fp",
            )
        )
        self.info["info"] = {
            "{A}": f"071_can/base{self.can_id}",
            "{a}": str(arm_tag),
        }
        can_pos = self.can.get_pose().p
        pad_pos = self.blue_pad.get_pose().p
        print(
            f"plan_success={self.plan_success} can={np.round(can_pos, 3).tolist()} "
            f"pad={np.round(pad_pos, 3).tolist()}"
        )
        return self.info

    def check_success(self):
        can_pos = self.can.get_pose().p
        target_pos = self.blue_pad.get_pose().p
        rest_z = getattr(self, "can_rest_z", 0.741 + self.table_z_bias)
        return (
            np.all(np.abs(can_pos[:2] - target_pos[:2]) < 0.04)
            and np.abs(can_pos[2] - rest_z) < 0.03
            and self.robot.is_left_gripper_open()
            and self.robot.is_right_gripper_open()
        )
