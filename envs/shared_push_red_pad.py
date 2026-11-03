from .shared_motion import SharedTask, finish, push, pushed


class shared_push_red_pad(SharedTask):
    def play_once(self):
        push(self, "red_cube", "left", [0.0, 1.0, 0.0], 0.07, 0.02)
        return finish(self, "red cube", "left")

    def check_success(self):
        return pushed(self, "red_cube", [0.0, 1.0, 0.0], 0.03, z_tol=0.02)
