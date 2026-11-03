from .shared_motion import SharedTask, finish, on_surface, pick_and_place


class shared_place_can_pad(SharedTask):
    """Left arm puts the can on the blue pad. The plate is out of reach."""

    def play_once(self):
        pick_and_place(
            self, "can", "left", 8, "blue_pad",
            contacts=(8, 2, 0, 4, 12),
            obj_fp=None, lift=0.12, pre_grasp=0.09,
            pre_dis=0.08, dis=0.01, constrain="free",
        )
        return finish(self, "can", "left")

    def check_success(self):
        return on_surface(self, "can", "blue_pad", xy=0.045, z_tol=0.05)
