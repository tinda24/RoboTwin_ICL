from ._base_task import Base_Task
from .shared_table import build_shared_table
from .utils import *


class shared_place_cube(Base_Task):

    def setup_demo(self, **kwags):
        self.scene_seed = kwags.get("seed", 0)
        super()._init_task_env_(**kwags)

    def load_actors(self):
        self.table_objects = build_shared_table(self, self.scene_seed)
        self.red_cube = self.table_objects["red_cube"]["actor"]
        self.blue_pad = self.table_objects["blue_pad"]["actor"]
        self.arm_tag = ArmTag("left")

    def play_once(self):
        arm_tag = self.arm_tag
        # Keep the fingers on the lane that is clear of the blue pad.
        self.robot.left_rotate_lim = [0, 0]
        self.robot.right_rotate_lim = [0, 0]
        self.cube_rest_z = float(self.red_cube.get_pose().p[2])
        self.move(
            self.grasp_actor(
                self.red_cube,
                arm_tag=arm_tag,
                pre_grasp_dis=0.09,
                contact_point_id=0,
            )
        )
        self.move(self.move_by_displacement(arm_tag=arm_tag, z=0.07))
        target_pose = self.blue_pad.get_functional_point(1)
        self.move(
            self.place_actor(
                self.red_cube,
                arm_tag=arm_tag,
                target_pose=target_pose,
                functional_point_id=0,
                pre_dis=0.08,
                dis=0.01,
                constrain="align",
            )
        )
        self.info["info"] = {
            "{A}": "red cube",
            "{a}": str(arm_tag),
        }
        return self.info

    def check_success(self):
        cube_pos = self.red_cube.get_pose().p
        target_pos = self.blue_pad.get_pose().p
        rest_z = getattr(self, "cube_rest_z", 0.762 + self.table_z_bias)
        return (
            np.all(np.abs(cube_pos[:2] - target_pos[:2]) < 0.03)
            and np.abs(cube_pos[2] - rest_z) < 0.025
            and self.robot.is_left_gripper_open()
            and self.robot.is_right_gripper_open()
        )
