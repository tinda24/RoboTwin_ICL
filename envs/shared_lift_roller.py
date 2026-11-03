from .shared_motion import SharedTask, finish, lift_one, lifted


class shared_lift_roller(SharedTask):
    def play_once(self):
        lift_one(self, "roller", "left", 0, lift=0.08, contacts=(0, 1))
        return finish(self, "roller", "left")

    def check_success(self):
        return lifted(self, "roller", "left")
