import numpy as np

from .shared_motion import SharedTask, finish, handed, lock_wrists, snapshot


class shared_handover_cards(SharedTask):
    """Right hand lifts the cards; the left hand takes them along the free faces."""

    def play_once(self):
        from .utils import ArmTag
        import transforms3d as t3d

        from .shared_motion import ensure_place_point, tcp_pose

        lock_wrists(self)
        snapshot(self)
        cards = self.table_objects["cards"]["actor"]
        give = ArmTag("right")
        recv = ArmTag("left")
        self.move(
            self.grasp_actor(
                cards,
                arm_tag=give,
                pre_grasp_dis=0.09,
                contact_point_id=0,
            )
        )
        self.move(self.move_by_displacement(give, z=0.12))
        # Far enough left for the left arm, still inside the right arm's reach.
        self.move(
            self.place_actor(
                cards,
                arm_tag=give,
                target_pose=[-0.02, -0.16, 0.88, 0, 1, 0, 0],
                functional_point_id=ensure_place_point(cards),
                pre_dis=0.05,
                dis=0.0,
                is_open=False,
                constrain="free",
            )
        )
        print(
            f"handover carried plan={self.plan_success} p={cards.get_pose().p}",
            flush=True,
        )

        center = np.array(cards.get_pose().p, dtype=np.float64)
        right_tcp = np.array(self.robot.get_right_tcp_pose(), dtype=np.float64)
        finger = t3d.quaternions.quat2mat(right_tcp[3:])[:, 1]
        finger[2] = 0.0
        if np.linalg.norm(finger) < 1e-4:
            finger = np.array([0.0, 1.0, 0.0])
        finger = finger / np.linalg.norm(finger)
        # Prefer the direction that puts the left arm further to -x.
        directions = sorted((finger, -finger), key=lambda d: -float(d[0]))
        direction = directions[0]
        pre_pt = center - direction * 0.08
        high = tcp_pose(pre_pt + np.array([0.0, 0.0, 0.16]), direction)
        pre = tcp_pose(pre_pt, direction)
        grasp = tcp_pose(center, direction)
        if self.need_plan and self.plan_success:
            for candidate in directions:
                high_try = tcp_pose(
                    center - candidate * 0.08 + np.array([0.0, 0.0, 0.16]),
                    candidate,
                )
                ok = self.robot.left_plan_path(high_try).get("status") == "Success"
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
            tcp = np.array(self.robot.get_left_tcp_pose(), dtype=np.float64)
            cards_p = np.array(cards.get_pose().p, dtype=np.float64)
            print(
                f"{tag} tcp={np.round(tcp[:3], 3).tolist()} cards={np.round(cards_p, 3).tolist()} "
                f"plan={self.plan_success}",
                flush=True,
            )

        self.move(self.move_to_pose(recv, high))
        _mark("high")
        self.move(self.move_to_pose(recv, pre))
        _mark("pre")
        # Re-center on the live pose before closing; the deck drifts when the left arm arrives.
        live = np.array(cards.get_pose().p, dtype=np.float64)
        self.move(self.move_to_pose(recv, tcp_pose(live, direction)))
        _mark("chase")
        self.move(self.close_gripper(recv, pos=0.0))
        print(
            f"recv closed plan={self.plan_success} "
            f"contact={len(self.get_gripper_actor_contact_position('cards'))}",
            flush=True,
        )
        # Lift while both hands still hold, then let the right hand leave.
        self.move(self.move_by_displacement(recv, z=0.06))
        print(
            f"recv lift plan={self.plan_success} "
            f"contact={len(self.get_gripper_actor_contact_position('cards'))} "
            f"z={float(cards.get_pose().p[2]):.3f}",
            flush=True,
        )
        self.move(self.open_gripper(give))
        print(f"give opened plan={self.plan_success}", flush=True)
        # Slide the right hand straight out along +x; lifting it knocks the deck free.
        self.move(self.move_by_displacement(give, x=0.18))
        print(
            f"give clear plan={self.plan_success} "
            f"contact={len(self.get_gripper_actor_contact_position('cards'))} "
            f"z={float(cards.get_pose().p[2]):.3f}",
            flush=True,
        )
        self.move(self.move_by_displacement(recv, z=0.08))
        print(f"handover taken plan={self.plan_success}", flush=True)
        return finish(self, "playing cards", "right", {"{b}": "left"})

    def check_success(self):
        return handed(self, "cards", "left", "right")
