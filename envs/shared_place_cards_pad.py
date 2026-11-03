from .shared_motion import SharedTask, finish, on_surface, pick_and_place


class shared_place_cards_pad(SharedTask):
    def play_once(self):
        pick_and_place(
            self, "cards", "right", 0, "yellow_pad",
            obj_fp=None, lift=0.1, pre_dis=0.08, dis=0.01, constrain="free",
        )
        return finish(self, "playing cards", "right")

    def check_success(self):
        return on_surface(self, "cards", "yellow_pad", xy=0.04, z_tol=0.03)
