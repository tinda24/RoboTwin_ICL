from .shared_motion import SharedTask, both_lifted, dual_lift, finish


class shared_lift_green_cup(SharedTask):
    def play_once(self):
        dual_lift(self, "green_cube", 0, "cup", 0, lift=0.08)
        return finish(self, "green cube", "left", {"{B}": "cup", "{b}": "right"})

    def check_success(self):
        return both_lifted(self, "green_cube", "cup")
