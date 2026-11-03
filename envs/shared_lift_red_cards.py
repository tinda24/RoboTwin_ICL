from .shared_motion import SharedTask, both_lifted, dual_lift, finish


class shared_lift_red_cards(SharedTask):
    def play_once(self):
        dual_lift(self, "red_cube", 0, "cards", 0, lift=0.08)
        return finish(self, "red cube", "left", {"{B}": "playing cards", "{b}": "right"})

    def check_success(self):
        return both_lifted(self, "red_cube", "cards")
