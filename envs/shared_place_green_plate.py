from .shared_motion import SharedTask, carry_and_drop, finish, in_plate


class shared_place_green_plate(SharedTask):
    def play_once(self):
        carry_and_drop(self, "green_cube", "left", 0, "plate", bias=(-0.07, -0.05))
        return finish(self, "green cube", "left")

    def check_success(self):
        return in_plate(self, "green_cube")
