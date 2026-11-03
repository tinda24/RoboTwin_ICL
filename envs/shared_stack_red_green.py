from .shared_motion import SharedTask, finish, pick_and_place, stacked


class shared_stack_red_green(SharedTask):
    def play_once(self):
        pick_and_place(
            self, "red_cube", "left", 0, "green_cube",
            target_fp=1, obj_fp=0, lift=0.1, pre_dis=0.08, dis=0.005,
        )
        return finish(self, "red cube", "left", {"{B}": "green cube"})

    def check_success(self):
        return stacked(self, "red_cube", "green_cube")
