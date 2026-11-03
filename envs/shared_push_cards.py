from .shared_motion import SharedTask, finish, push, pushed


class shared_push_cards(SharedTask):
    def play_once(self):
        push(self, "cards", "right", [0.0, -1.0, 0.0], 0.045, 0.048, z_offset=0.012)
        return finish(self, "playing cards", "right")

    def check_success(self):
        return pushed(self, "cards", [0.0, -1.0, 0.0], 0.025, z_tol=0.015)
