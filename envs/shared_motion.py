import numpy as np
import transforms3d as t3d

from ._base_task import Base_Task
from .shared_table import TABLE_OBJECTS, build_shared_table
from .utils import Action, ArmTag, create_actor


class SharedTask(Base_Task):
    def setup_demo(self, **kwags):
        self.scene_seed = kwags.get("seed", 0)
        super()._init_task_env_(**kwags)

    def load_actors(self):
        self.table_objects = build_shared_table(self, self.scene_seed)
        self.specs = {spec["name"]: spec for spec in TABLE_OBJECTS}


def lock_wrists(task):
    task.robot.left_rotate_lim = [0, 0]
    task.robot.right_rotate_lim = [0, 0]


def actor(task, name):
    return task.table_objects[name]["actor"]


def snapshot(task):
    task.rest = {
        name: np.array(info["actor"].get_pose().p, dtype=np.float64)
        for name, info in task.table_objects.items()
    }


def finish(task, object_name, arm, extra=None):
    info = {"{A}": object_name, "{a}": str(arm)}
    if extra:
        info.update(extra)
    task.info["info"] = info
    return task.info


def grippers_open(task):
    return task.robot.is_left_gripper_open() and task.robot.is_right_gripper_open()


def arm_closed(task, arm):
    if arm == "left":
        return task.robot.is_left_gripper_close()
    return task.robot.is_right_gripper_close()


def arm_open(task, arm):
    if arm == "left":
        return task.robot.is_left_gripper_open()
    return task.robot.is_right_gripper_open()


def quat_pointing(direction):
    x_axis = np.asarray(direction, dtype=np.float64)
    x_axis = x_axis / np.linalg.norm(x_axis)
    up = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(x_axis, up))) > 0.95:
        up = np.array([0.0, 1.0, 0.0])
    y_axis = np.cross(up, x_axis)
    y_axis = y_axis / np.linalg.norm(y_axis)
    z_axis = np.cross(x_axis, y_axis)
    rotation = np.stack([x_axis, y_axis, z_axis], axis=1)
    return t3d.quaternions.mat2quat(rotation)


def tcp_pose(tcp, direction):
    """Fingertip at tcp, gripper +x pointing along direction."""
    quat = quat_pointing(direction)
    rotation = t3d.quaternions.quat2mat(quat)
    position = np.asarray(tcp, dtype=np.float64) - 0.12 * rotation[:, 0]
    return position.tolist() + list(quat)


def ensure_place_point(obj):
    """Give a mesh a bottom point whose z axis points down, matching the boxes."""
    mats = obj.config.get("functional_matrix") or []
    if len(mats) > 0:
        return 0
    obj.config["functional_matrix"] = [[
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]]
    obj.config.setdefault("scale", [1.0, 1.0, 1.0])
    return 0


def pick_and_place(
    task,
    obj_name,
    arm,
    contact,
    target_name,
    target_fp=1,
    obj_fp=0,
    lift=0.08,
    pre_grasp=0.09,
    pre_dis=0.08,
    dis=0.01,
    constrain="align",
    retreat=0.0,
    pose_at_center=False,
    pre_dis_axis="grasp",
    contacts=None,
    center_bias=(0.0, 0.0),
):
    lock_wrists(task)
    snapshot(task)
    obj = actor(task, obj_name)
    target = actor(task, target_name)
    if contacts:
        contact = first_reachable_contact(task, obj, arm, contacts, pre_grasp)
    arm_tag = ArmTag(arm)
    task.move(
        task.grasp_actor(
            obj,
            arm_tag=arm_tag,
            pre_grasp_dis=pre_grasp,
            contact_point_id=contact,
        )
    )
    task.move(task.move_by_displacement(arm_tag=arm_tag, z=lift))
    task.high_z = float(obj.get_pose().p[2])
    if obj_fp is None:
        obj_fp = ensure_place_point(obj)
    if pose_at_center:
        center = np.array(target.get_pose().p, dtype=np.float64)
        # z axis points down so it matches the box and mesh bottom points.
        target_pose = [
            float(center[0] + center_bias[0]),
            float(center[1] + center_bias[1]),
            float(center[2]) + 0.006,
            0, 1, 0, 0,
        ]
    else:
        target_pose = target.get_functional_point(target_fp)
    kwargs = dict(
        arm_tag=arm_tag,
        target_pose=target_pose,
        pre_dis=pre_dis,
        dis=dis,
        constrain=constrain,
        functional_point_id=obj_fp,
        pre_dis_axis=pre_dis_axis,
    )
    task.move(task.place_actor(obj, **kwargs))
    if retreat:
        task.move(task.move_by_displacement(arm_tag=arm_tag, z=retreat))
        task.delay(8, save_freq=-1)
    obj_now = np.array(obj.get_pose().p, dtype=np.float64)
    target_now = np.array(target.get_pose().p, dtype=np.float64)
    print(
        f"place {obj_name}->{target_name} plan={task.plan_success} "
        f"obj={np.round(obj_now, 3).tolist()} target={np.round(target_now, 3).tolist()} "
        f"open={grippers_open(task)}",
        flush=True,
    )


def carry_and_drop(task, obj_name, arm, contact, target_name, contacts=None, bias=(-0.04, -0.04)):
    """Grasp, carry above a container, and drop. Used when place_actor cannot reach."""
    lock_wrists(task)
    snapshot(task)
    obj = actor(task, obj_name)
    target = actor(task, target_name)
    if contacts:
        contact = first_reachable_contact(task, obj, arm, contacts, 0.09)
    arm_tag = ArmTag(arm)
    task.move(
        task.grasp_actor(
            obj,
            arm_tag=arm_tag,
            pre_grasp_dis=0.09,
            contact_point_id=contact,
        )
    )
    task.move(task.move_by_displacement(arm_tag=arm_tag, z=0.18))
    task.high_z = float(obj.get_pose().p[2])
    center = np.array(target.get_pose().p, dtype=np.float64)
    goal_xy = np.array([center[0] + bias[0], center[1] + bias[1]])
    now = np.array(obj.get_pose().p, dtype=np.float64)
    mid_xy = now[:2] + 0.45 * (goal_xy - now[:2])
    task.move(
        task.move_by_displacement(
            arm_tag=arm_tag,
            x=float(mid_xy[0] - now[0]),
            y=float(mid_xy[1] - now[1]),
        )
    )
    # Lower before the second half. The left arm reaches farther when it is not fully raised.
    task.move(task.move_by_displacement(arm_tag=arm_tag, z=-0.08))
    now = np.array(obj.get_pose().p, dtype=np.float64)
    task.move(
        task.move_by_displacement(
            arm_tag=arm_tag,
            x=float(goal_xy[0] - now[0]),
            y=float(goal_xy[1] - now[1]),
        )
    )
    task.move(task.move_by_displacement(arm_tag=arm_tag, z=-0.06))
    task.move(task.open_gripper(arm_tag))
    task.move(task.move_by_displacement(arm_tag=arm_tag, z=0.08))
    task.delay(8, save_freq=-1)
    print(
        f"drop {obj_name} plan={task.plan_success} "
        f"obj={np.round(obj.get_pose().p, 3).tolist()} "
        f"target={np.round(center, 3).tolist()}",
        flush=True,
    )


def on_surface(task, obj_name, target_name, xy=0.03, z_tol=0.03):
    obj = actor(task, obj_name).get_pose().p
    target = actor(task, target_name).get_pose().p
    rest_z = task.rest[obj_name][2]
    return (
        np.all(np.abs(obj[:2] - target[:2]) < xy)
        and abs(float(obj[2]) - rest_z) < z_tol
        and grippers_open(task)
    )


def stacked(task, upper, lower):
    up = actor(task, upper).get_pose().p
    lo = actor(task, lower).get_pose().p
    return (
        np.linalg.norm(up[:2] - lo[:2]) < 0.025
        and abs(float(up[2] - lo[2]) - 0.04) < 0.02
        and grippers_open(task)
    )


def in_plate(task, obj_name, radius=0.10):
    obj = actor(task, obj_name).get_pose().p
    plate = actor(task, "plate").get_pose().p
    high_z = getattr(task, "high_z", 0.0)
    return (
        np.linalg.norm(obj[:2] - plate[:2]) < radius
        and float(obj[2]) < float(plate[2]) + 0.05
        and float(obj[2]) > float(plate[2]) - 0.02
        and high_z > float(plate[2]) + 0.06
        and grippers_open(task)
    )


def _dynamic_component(actor):
    import sapien

    for component in actor.actor.get_components():
        if isinstance(component, sapien.physx.PhysxRigidDynamicComponent):
            return component
    return None


def make_movable(task, name, mass=0.05, hold_pose=False):
    """Replace a static shared-table actor with a dynamic copy at the same pose.

    hold_pose turns gravity off so the designed grasp orientation survives the
    stability settle. Call release_held_pose after the grasp.
    """
    info = task.table_objects[name]
    old = info["actor"]
    pose = old.get_pose()
    spec = task.specs[name]
    entity = old.actor
    if hasattr(entity, "remove_from_scene"):
        entity.remove_from_scene()
    else:
        task.scene.remove_entity(entity)
    new = create_actor(
        scene=task,
        pose=pose,
        modelname=spec["model"],
        model_id=spec["model_id"],
        convex=True,
        is_static=False,
    )
    new.set_name(name)
    new.set_mass(mass)
    if hold_pose:
        component = _dynamic_component(new)
        if component is not None:
            component.disable_gravity = True
    task.add_prohibit_area(new, padding=0.03)
    info["actor"] = new
    task.specs[name]["static"] = False
    return new


def release_held_pose(actor):
    component = _dynamic_component(actor)
    if component is not None:
        component.disable_gravity = False


def pinch(task, obj_name, arm, contact, pre_grasp=0.08):
    lock_wrists(task)
    snapshot(task)
    arm_tag = ArmTag(arm)
    task.move(
        task.grasp_actor(
            actor(task, obj_name),
            arm_tag=arm_tag,
            pre_grasp_dis=pre_grasp,
            contact_point_id=contact,
        )
    )


def pinched(task, obj_name, arm):
    if not arm_closed(task, arm):
        return False
    if len(task.get_gripper_actor_contact_position(obj_name)) == 0:
        return False
    now = actor(task, obj_name).get_pose().p
    return np.linalg.norm(now[:2] - task.rest[obj_name][:2]) < 0.015


def first_reachable_contact(task, obj, arm, contacts, pre_grasp=0.09):
    arm_tag = ArmTag(arm)
    plan = task.robot.left_plan_path if arm == "left" else task.robot.right_plan_path
    for cid in contacts:
        chosen = task.choose_grasp_pose(
            obj,
            arm_tag=arm_tag,
            pre_dis=pre_grasp,
            target_dis=0,
            contact_point_id=cid,
        )
        if not chosen or chosen[0] is None:
            continue
        pre = chosen[0]
        if not isinstance(pre, list) or pre[0] == -1:
            continue
        if plan(pre).get("status") == "Success":
            print(f"grasp {obj.get_name()} contact {cid}", flush=True)
            return cid
    print(f"grasp {obj.get_name()} no reachable contact in {contacts}", flush=True)
    return contacts[0]


def lift_one(task, obj_name, arm, contact, lift=0.08, pre_grasp=0.09, contacts=None):
    lock_wrists(task)
    snapshot(task)
    obj = actor(task, obj_name)
    if contacts:
        contact = first_reachable_contact(task, obj, arm, contacts, pre_grasp)
    arm_tag = ArmTag(arm)
    task.move(
        task.grasp_actor(
            obj,
            arm_tag=arm_tag,
            pre_grasp_dis=pre_grasp,
            contact_point_id=contact,
        )
    )
    task.move(task.move_by_displacement(arm_tag=arm_tag, z=lift))


def lifted(task, obj_name, arm, dz=0.03):
    now = actor(task, obj_name).get_pose().p
    return arm_closed(task, arm) and float(now[2]) > task.rest[obj_name][2] + dz


def dual_lift(task, left_name, left_contact, right_name, right_contact, lift=0.08):
    lock_wrists(task)
    snapshot(task)
    left = ArmTag("left")
    right = ArmTag("right")
    task.move(
        task.grasp_actor(
            actor(task, left_name),
            arm_tag=left,
            pre_grasp_dis=0.09,
            contact_point_id=left_contact,
        ),
        task.grasp_actor(
            actor(task, right_name),
            arm_tag=right,
            pre_grasp_dis=0.09,
            contact_point_id=right_contact,
        ),
    )
    task.move(
        task.move_by_displacement(arm_tag=left, z=lift),
        task.move_by_displacement(arm_tag=right, z=lift),
    )


def both_lifted(task, left_name, right_name, dz=0.03):
    left = actor(task, left_name).get_pose().p
    right = actor(task, right_name).get_pose().p
    return (
        arm_closed(task, "left")
        and arm_closed(task, "right")
        and float(left[2]) > task.rest[left_name][2] + dz
        and float(right[2]) > task.rest[right_name][2] + dz
    )


def push(task, obj_name, arm, direction, distance, half_extent, z_offset=0.0):
    """Slide an object along the table without lifting it.

    A top grasp keeps the fingers on the slot's open lane. The arm then
    moves horizontally and lets go, so the object stays at table height.
    """
    del half_extent, z_offset
    from .shared_table import GRASP_PLAN

    lock_wrists(task)
    snapshot(task)
    direction = np.asarray(direction, dtype=np.float64)
    direction = direction / np.linalg.norm(direction)
    contact = GRASP_PLAN[obj_name][1]
    arm_tag = ArmTag(arm)
    task.move(
        task.grasp_actor(
            actor(task, obj_name),
            arm_tag=arm_tag,
            pre_grasp_dis=0.08,
            contact_point_id=contact,
        )
    )
    task.move(task.move_by_displacement(arm_tag=arm_tag, z=-0.004))
    task.move(
        task.move_by_displacement(
            arm_tag,
            x=float(direction[0] * distance),
            y=float(direction[1] * distance),
        )
    )
    task.move(task.open_gripper(arm_tag))
    task.delay(3, save_freq=-1)
    now = np.array(actor(task, obj_name).get_pose().p, dtype=np.float64)
    delta = now - task.rest[obj_name]
    print(
        f"push {obj_name} plan={task.plan_success} delta={np.round(delta, 3).tolist()}",
        flush=True,
    )


def pushed(task, obj_name, direction, min_move, z_tol=0.02):
    direction = np.asarray(direction, dtype=np.float64)
    direction = direction / np.linalg.norm(direction)
    now = np.array(actor(task, obj_name).get_pose().p, dtype=np.float64)
    delta = now - task.rest[obj_name]
    along = float(np.dot(delta[:2], direction[:2]))
    lateral = float(np.linalg.norm(delta[:2] - along * direction[:2]))
    return along > min_move and lateral < 0.035 and abs(float(delta[2])) < z_tol


def _cap_center(knob):
    pose = knob.get_pose()
    rotation = t3d.quaternions.quat2mat(pose.q)
    return np.array(pose.p, dtype=np.float64) + rotation @ np.array([0.0, 0.0, 0.018]), rotation


def _prepare_knob(task, knob):
    for joint in knob.actor.get_joints():
        if joint.get_name() != "knob_joint":
            continue
        joint.set_drive_properties(damping=0.02, stiffness=0.0, force_limit=1.0)
        try:
            joint.set_friction(0.0)
        except Exception:
            pass
    try:
        material = task.scene.create_physical_material(2.0, 1.5, 0.0)
        for link in knob.actor.get_links():
            shapes = getattr(link, "collision_shapes", None)
            if shapes is None:
                shapes = link.get_collision_shapes()
            for shape in shapes:
                shape.physical_material = material
    except Exception as exc:
        print(f"knob material: {exc}", flush=True)


def _knob_pose(center, rotation, angle, radius, sign, tilt):
    local = np.array([sign * np.sin(angle), -np.cos(angle), 0.0])
    outward = rotation @ local
    toward = -outward + np.array([0.0, 0.0, -tilt])
    toward = toward / np.linalg.norm(toward)
    tcp = center + outward * radius
    return tcp_pose(tcp, toward)


def turn_knob(task, clockwise):
    lock_wrists(task)
    snapshot(task)
    knob = actor(task, "knob")
    _prepare_knob(task, knob)
    task.rest_q = float(np.array(knob.get_qpos()).reshape(-1)[0])
    center, _rotation = _cap_center(knob)
    # Closed gripper comes down on the front rim, then slides sideways.
    # Clockwise, seen from above, moves that point toward -x.
    sweep = -0.035 if clockwise else 0.035
    down = np.array([0.0, 0.0, -1.0])
    hover = tcp_pose(center + np.array([0.0, -0.02, 0.07]), down)
    press = tcp_pose(center + np.array([0.0, -0.012, 0.012]), down)
    end = tcp_pose(center + np.array([sweep, -0.012, 0.012]), down)
    arm_tag = ArmTag("right")
    task.move(task.close_gripper(arm_tag=arm_tag, pos=0.0))
    print(f"knob after close plan={task.plan_success}", flush=True)
    task.move((arm_tag, [Action(arm_tag, "move", target_pose=hover)]))
    print(f"knob after hover plan={task.plan_success}", flush=True)
    task.move((
        arm_tag,
        [
            Action(arm_tag, "move", target_pose=press, constraint_pose=[1, 1, 1, 0, 0, 0]),
            Action(arm_tag, "move", target_pose=end, constraint_pose=[1, 1, 1, 0, 0, 0]),
        ],
    ))
    q_now = float(np.array(knob.get_qpos()).reshape(-1)[0])
    print(
        f"knob plan={task.plan_success} q={q_now:.3f} rest={task.rest_q:.3f} "
        f"center={np.round(center, 3).tolist()}",
        flush=True,
    )


def knob_turned(task, clockwise, min_angle=0.25):
    knob = actor(task, "knob")
    q = float(np.array(knob.get_qpos()).reshape(-1)[0])
    delta = q - task.rest_q
    print(f"knob delta={delta:.3f} closed={arm_closed(task, 'right')}", flush=True)
    if clockwise and delta > -min_angle:
        return False
    if not clockwise and delta < min_angle:
        return False
    return arm_closed(task, "right")


def handover(task, obj_name, give_arm, give_contact, recv_arm):
    """Lift with one hand, carry to the middle, then let the other hand take it."""
    lock_wrists(task)
    snapshot(task)
    obj = actor(task, obj_name)
    give = ArmTag(give_arm)
    recv = ArmTag(recv_arm)
    exchange = np.array([0.0, -0.15, 0.98])
    task.move(
        task.grasp_actor(
            obj,
            arm_tag=give,
            pre_grasp_dis=0.09,
            contact_point_id=give_contact,
        )
    )
    task.move(task.move_by_displacement(arm_tag=give, z=0.2))
    center = np.array(obj.get_pose().p, dtype=np.float64)
    delta = exchange - center
    task.move(task.move_by_displacement(arm_tag=give, x=float(delta[0]), y=float(delta[1])))
    task.move(task.move_by_displacement(arm_tag=give, z=float(delta[2])))
    print(
        f"handover carried plan={task.plan_success} p={np.round(obj.get_pose().p, 3).tolist()}",
        flush=True,
    )
    direction = np.array([1.0, 0.0, 0.0] if recv_arm == "left" else [-1.0, 0.0, 0.0])
    center = np.array(obj.get_pose().p, dtype=np.float64)
    pinch_at = center + np.array([0.0, 0.0, -0.012])
    hover = tcp_pose(pinch_at - direction * 0.10, direction)
    pinch_pose = tcp_pose(pinch_at, direction)
    task.move(task.open_gripper(recv, pos=1.0))
    task.move((
        recv,
        [
            Action(recv, "move", target_pose=hover),
            Action(recv, "move", target_pose=pinch_pose, constraint_pose=[1, 1, 1, 0, 0, 0]),
            Action(recv, "close", target_gripper_pos=0.0),
        ],
    ))
    print(f"handover taken plan={task.plan_success}", flush=True)
    task.move(task.open_gripper(give))
    task.move(task.move_by_displacement(arm_tag=give, z=0.08))


def handed(task, obj_name, recv_arm, give_arm):
    now = actor(task, obj_name).get_pose().p
    contact = len(task.get_gripper_actor_contact_position(obj_name))
    ok = (
        arm_closed(task, recv_arm)
        and arm_open(task, give_arm)
        and float(now[2]) > task.rest[obj_name][2] + 0.05
        and contact > 0
    )
    print(
        f"handed z={float(now[2]):.3f} recv_closed={arm_closed(task, recv_arm)} "
        f"give_open={arm_open(task, give_arm)} contact={contact}",
        flush=True,
    )
    return ok
