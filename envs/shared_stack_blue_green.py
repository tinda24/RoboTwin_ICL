from .shared_motion import SharedTask, finish, pick_and_place, stacked


class shared_stack_blue_green(SharedTask):
    def play_once(self):
        pick_and_place(
            self, "blue_cube", "left", 1, "green_cube",
            target_fp=1, obj_fp=0, lift=0.12, pre_dis=0.08, dis=0.005,
        )
        return finish(self, "blue cube", "left", {"{B}": "green cube"})

    def check_success(self):
        return stacked(self, "blue_cube", "green_cube")
