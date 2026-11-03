from .shared_motion import SharedTask, carry_and_drop, finish, in_plate


class shared_place_can_plate(SharedTask):
    def play_once(self):
        carry_and_drop(
            self, "can", "left", 2, "plate",
            contacts=(8, 2, 0, 4, 12), bias=(-0.07, -0.04),
        )
        return finish(self, "can", "left")

    def check_success(self):
        return in_plate(self, "can")
