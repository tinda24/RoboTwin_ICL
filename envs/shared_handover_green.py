import numpy as np

from .shared_motion import SharedTask, finish, handed, lock_wrists, snapshot


class shared_handover_green(SharedTask):
    """Left hand lifts the green cube; the right hand takes it from the opposite faces."""

    def play_once(self):
        from .utils import Action, ArmTag

        lock_wrists(self)
        snapshot(self)
        cube = self.table_objects["green_cube"]["actor"]
        give = ArmTag("left")
        recv = ArmTag("right")
        self.move(
            self.grasp_actor(
                cube,
                arm_tag=give,
                pre_grasp_dis=0.09,
                contact_point_id=0,
            )
        )
        self.move(self.move_by_displacement(give, z=0.12))
        # Far enough right for the right arm, still inside the left arm's reach.
        self.move(
            self.place_actor(
                cube,
                arm_tag=give,
                target_pose=[0.06, -0.16, 0.88, 0, 1, 0, 0],
                functional_point_id=0,
                pre_dis=0.05,
                dis=0.0,
                is_open=False,
                constrain="free",
            )
        )
        print(
            f"handover carried plan={self.plan_success} p={cube.get_pose().p}",
            flush=True,
        )
        import transforms3d as t3d

        from .shared_motion import tcp_pose

        center = np.array(cube.get_pose().p, dtype=np.float64)
        left_tcp = np.array(self.robot.get_left_tcp_pose(), dtype=np.float64)
        finger = t3d.quaternions.quat2mat(left_tcp[3:])[:, 1]
        finger[2] = 0.0
        if np.linalg.norm(finger) < 1e-4:
            finger = np.array([1.0, 0.0, 0.0])
        finger = finger / np.linalg.norm(finger)
        # Approach along the left fingers, so the right fingers close on the free faces.
        # Smaller direction_x puts the right arm further to +x.
        directions = sorted((finger, -finger), key=lambda d: float(d[0]))
        direction = directions[0]
        pre_pt = center - direction * 0.08
        high_pt = pre_pt + np.array([0.0, 0.0, 0.16])
        high = tcp_pose(high_pt, direction)
        pre = tcp_pose(pre_pt, direction)
        grasp = tcp_pose(center, direction)
        if self.need_plan and self.plan_success:
            for candidate in directions:
                high_try = tcp_pose(center - candidate * 0.08 + np.array([0.0, 0.0, 0.16]), candidate)
                ok = self.robot.right_plan_path(high_try).get("status") == "Success"
                print(
                    f"recv dir={np.round(candidate, 2).tolist()} high={ok}",
                    flush=True,
                )
                if ok:
                    direction = candidate
                    pre_pt = center - direction * 0.08
                    high = high_try
                    pre = tcp_pose(pre_pt, direction)
                    grasp = tcp_pose(center, direction)
                    break
        print(
            f"recv finger={np.round(finger, 2).tolist()} dir={np.round(direction, 2).tolist()}",
            flush=True,
        )
        self.move(self.open_gripper(recv, pos=1.0))

        def _mark(tag):
            tcp = np.array(self.robot.get_right_tcp_pose(), dtype=np.float64)
            cube_p = np.array(cube.get_pose().p, dtype=np.float64)
            print(
                f"{tag} tcp={np.round(tcp[:3], 3).tolist()} cube={np.round(cube_p, 3).tolist()} "
                f"plan={self.plan_success}",
                flush=True,
            )

        self.move(self.move_to_pose(recv, high))
        _mark("high")
        self.move(self.move_to_pose(recv, pre))
        _mark("pre")
        self.move(self.move_to_pose(recv, grasp))
        _mark("grasp")
        self.move(self.close_gripper(recv, pos=0.0))
        print(
            f"recv closed plan={self.plan_success} "
            f"contact={len(self.get_gripper_actor_contact_position('green_cube'))}",
            flush=True,
        )
        self.move(self.open_gripper(give))
        print(f"give opened plan={self.plan_success}", flush=True)
        self.move(self.move_by_displacement(give, x=-0.12, z=0.08))
        print(f"give clear plan={self.plan_success}", flush=True)
        self.move(self.move_by_displacement(recv, z=0.08))
        print(f"handover taken plan={self.plan_success}", flush=True)
        return finish(self, "green cube", "left", {"{b}": "right"})

    def check_success(self):
        return handed(self, "green_cube", "right", "left")
