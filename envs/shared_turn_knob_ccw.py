from .shared_motion import SharedTask, finish, knob_turned, turn_knob


class shared_turn_knob_ccw(SharedTask):
    def play_once(self):
        turn_knob(self, clockwise=False)
        return finish(self, "knob", "right")

    def check_success(self):
        return knob_turned(self, clockwise=False)
