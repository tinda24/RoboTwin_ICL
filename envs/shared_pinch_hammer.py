from .shared_motion import (
    SharedTask,
    arm_closed,
    finish,
    lock_wrists,
    make_movable,
    release_held_pose,
)


class shared_pinch_hammer(SharedTask):
    """Pick up the hammer and strike the playing cards. The hammer stays held."""

    def load_actors(self):
        super().load_actors()
        self.hammer = make_movable(self, "hammer", mass=0.001, hold_pose=True)

    def play_once(self):
        from .utils import ArmTag

        lock_wrists(self)
        arm = ArmTag("right")
        cards = self.table_objects["cards"]["actor"]
        self.hammer_rest = self.hammer.get_pose().p.copy()
        self.move(
            self.grasp_actor(
                self.hammer,
                arm_tag=arm,
                pre_grasp_dis=0.12,
                grasp_dis=0.01,
                contact_point_id=0,
            )
        )
        self.move(self.move_by_displacement(arm_tag=arm, z=0.07, move_axis="arm"))
        release_held_pose(self.hammer)
        card = cards.get_pose().p
        head_now = self.hammer.get_functional_point(0, "list")
        # Keep the head's current orientation and translate it onto the cards.
        target = [
            float(card[0]),
            float(card[1]),
            float(card[2]) + 0.02,
            *head_now[3:],
        ]
        self.move(
            self.place_actor(
                self.hammer,
                arm_tag=arm,
                target_pose=target,
                functional_point_id=0,
                pre_dis=0.06,
                dis=0.0,
                is_open=False,
                constrain="free",
            )
        )
        return finish(self, "hammer", "right", {"{B}": "playing cards"})

    def check_success(self):
        head = self.hammer.get_functional_point(0, "pose").p
        cards = self.table_objects["cards"]["actor"].get_pose().p
        near = abs(float(head[0] - cards[0])) < 0.03 and abs(float(head[1] - cards[1])) < 0.03
        struck = self.check_actors_contact("hammer", "cards") or near
        lifted = float(self.hammer.get_pose().p[2]) > float(self.hammer_rest[2]) + 0.02
        return arm_closed(self, "right") and struck and lifted
