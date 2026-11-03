from .shared_motion import SharedTask, finish, in_plate, pick_and_place


class shared_place_cup_plate(SharedTask):
    def play_once(self):
        pick_and_place(
            self, "cup", "right", 0, "plate",
            target_fp=0, obj_fp=0, lift=0.12, pre_grasp=0.09,
            pre_dis=0.08, dis=0.02, constrain="free", retreat=0.08,
            pose_at_center=True,
        )
        return finish(self, "cup", "right")

    def check_success(self):
        return in_plate(self, "cup")
