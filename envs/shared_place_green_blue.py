from .shared_motion import SharedTask, finish, on_surface, pick_and_place


class shared_place_green_blue(SharedTask):
    """Left arm puts the green cube on the blue pad. The plate is out of reach."""

    def play_once(self):
        pick_and_place(
            self, "green_cube", "left", 0, "blue_pad",
            obj_fp=0, lift=0.1, pre_dis=0.08, dis=0.01,
        )
        return finish(self, "green cube", "left")

    def check_success(self):
        return on_surface(self, "green_cube", "blue_pad", xy=0.03, z_tol=0.03)
