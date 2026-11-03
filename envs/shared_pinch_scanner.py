import numpy as np
import transforms3d as t3d

from .shared_motion import SharedTask, arm_closed, finish, lock_wrists, make_movable


class shared_pinch_scanner(SharedTask):
    """Pick up the scanner and hold it over the yellow pad."""

    def load_actors(self):
        super().load_actors()
        self.scanner = make_movable(self, "scanner", mass=0.05)

    def play_once(self):
        from .utils import ArmTag

        lock_wrists(self)
        arm = ArmTag("left")
        pad = self.table_objects["yellow_pad"]["actor"]
        self.scanner_rest = self.scanner.get_pose().p.copy()
        self.move(
            self.grasp_actor(
                self.scanner,
                arm_tag=arm,
                pre_grasp_dis=0.09,
                contact_point_id=0,
            )
        )
        self.move(self.move_by_displacement(arm_tag=arm, z=0.1))
        self.move(
            self.place_actor(
                self.scanner,
                arm_tag=arm,
                target_pose=pad.get_functional_point(1),
                functional_point_id=0,
                pre_dis=0.08,
                dis=0.05,
                is_open=False,
                constrain="free",
            )
        )
        return finish(self, "scanner", "left", {"{B}": "yellow pad"})

    def check_success(self):
        pad = self.table_objects["yellow_pad"]["actor"].get_pose().p
        scanner_fp = np.array(self.scanner.get_functional_point(0), dtype=np.float64)
        aim = t3d.quaternions.quat2mat(scanner_fp[-4:]) @ np.array([0.0, 0.0, -1.0])
        offset = scanner_fp[:3] - pad
        distance = float(np.dot(aim, offset))
        projected = pad + distance * aim
        aimed = np.all(np.abs(projected - scanner_fp[:3]) < 0.04) and 0.0 < distance < 0.09
        above = np.linalg.norm(scanner_fp[:2] - pad[:2]) < 0.04 and scanner_fp[2] > pad[2] + 0.02
        moved = np.linalg.norm(self.scanner.get_pose().p[:2] - self.scanner_rest[:2]) > 0.05
        return arm_closed(self, "left") and moved and (aimed or above)
