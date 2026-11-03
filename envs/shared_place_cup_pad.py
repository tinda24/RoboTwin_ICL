from .shared_motion import SharedTask, finish, on_surface, pick_and_place


class shared_place_cup_pad(SharedTask):
    def play_once(self):
        pick_and_place(
            self, "cup", "right", 0, "purple_pad",
            obj_fp=0, lift=0.1, pre_dis=0.08, dis=0.01,
        )
        return finish(self, "cup", "right")

    def check_success(self):
        return on_surface(self, "cup", "purple_pad", xy=0.04, z_tol=0.04)
