from .shared_motion import SharedTask, finish, pick_and_place, stacked


class shared_stack_green_red(SharedTask):
    def play_once(self):
        pick_and_place(
            self, "green_cube", "left", 0, "red_cube",
            target_fp=1, obj_fp=0, lift=0.1, pre_dis=0.08, dis=0.005,
        )
        return finish(self, "green cube", "left", {"{B}": "red cube"})

    def check_success(self):
        return stacked(self, "green_cube", "red_cube")
