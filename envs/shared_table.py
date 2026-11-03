import numpy as np
import sapien
import transforms3d as t3d

from .utils import create_actor, create_box, create_sapien_urdf_obj


# One shared table. Poses are jittered by an isolated RandomState(seed), so
# every task that calls build_shared_table with the same seed rebuilds the
# same layout. The button is the RMBench prismatic cap. The knob is a small
# revolute cylinder. The only open container is the plate.
#
# Slots leave one open-gripper lane per graspable object. An aloha-agilex
# finger pair reaches about ±8.4 cm along the pinch axis and ±3.6 cm across
# it. GRASP_PLAN locks that axis: boxes use contact 0 (fingers along world X)
# or 1 (world Y). Mesh ids follow the same axis after the asset quaternion.
# Plate and knob have no pinch contact, so they are not in GRASP_PLAN.
TABLE_OBJECTS = [
    {
        "name": "bell",
        "kind": "actor",
        "model": "050_bell",
        "model_id": 0,
        "x": 0.220,
        "y": -0.320,
        "z": 0.741,
        "qpos": [0.5, 0.5, 0.5, 0.5],
        "yaw_axis": 1,
        "static": True,
        "mass": None,
    },
    {
        "name": "button",
        "kind": "urdf",
        "model": "005_button",
        "model_id": 0,
        "x": -0.400,
        "y": -0.100,
        "z": 0.751,
        "qpos": [1, 0, 0, 0],
        "yaw_axis": 2,
        "static": True,
        "mass": None,
    },
    {
        "name": "knob",
        "kind": "urdf",
        "model": "119_knob",
        "model_id": 0,
        "x": 0.280,
        "y": -0.080,
        "z": 0.747,
        "qpos": [1, 0, 0, 0],
        "yaw_axis": 2,
        "static": True,
        "mass": None,
    },
    {
        "name": "hammer",
        "kind": "actor",
        "model": "020_hammer",
        "model_id": 0,
        "x": 0.340,
        "y": 0.000,
        "z": 0.80,
        "qpos": [0, 0, 0.995, 0.105],
        "yaw_axis": 2,
        "static": True,
        "mass": None,
    },
    {
        "name": "scanner",
        "kind": "actor",
        "model": "024_scanner",
        "model_id": 0,
        "x": -0.300,
        "y": -0.030,
        "z": 0.75,
        "qpos": [0, 0, 0.707, 0.707],
        "yaw_axis": 1,
        "static": True,
        "mass": None,
    },
    {
        "name": "plate",
        "kind": "actor",
        "model": "003_plate",
        "model_id": 0,
        "x": 0.120,
        "y": 0.000,
        "z": 0.741,
        "qpos": [0.5, 0.5, 0.5, 0.5],
        "yaw_axis": 1,
        "static": True,
        "mass": None,
    },
    {
        "name": "cup",
        "kind": "actor",
        "model": "021_cup",
        "model_id": 0,
        "x": 0.340,
        "y": -0.180,
        "z": 0.741,
        "qpos": [0.5, 0.5, 0.5, 0.5],
        "yaw_axis": 1,
        "static": False,
        "mass": 0.05,
    },
    {
        "name": "blue_pad",
        "kind": "box",
        "x": -0.160,
        "y": -0.040,
        "z": 0.741,
        "qpos": [1, 0, 0, 0],
        "yaw_axis": 2,
        "half_size": (0.04, 0.04, 0.0005),
        "color": (0, 0, 1),
        "static": True,
    },
    {
        "name": "yellow_pad",
        "kind": "box",
        "x": 0.000,
        "y": -0.175,
        "z": 0.741,
        "qpos": [1, 0, 0, 0],
        "yaw_axis": 2,
        "half_size": (0.04, 0.04, 0.0005),
        "color": (1, 1, 0),
        "static": True,
    },
    {
        "name": "purple_pad",
        "kind": "box",
        "x": 0.100,
        "y": -0.190,
        "z": 0.741,
        "qpos": [1, 0, 0, 0],
        "yaw_axis": 2,
        "half_size": (0.04, 0.04, 0.0005),
        "color": (0.55, 0.0, 0.75),
        "static": True,
    },
    {
        "name": "red_cube",
        "kind": "box",
        "x": -0.160,
        "y": -0.185,
        "z": 0.762,
        "qpos": [1, 0, 0, 0],
        "yaw_axis": 2,
        "half_size": (0.02, 0.02, 0.02),
        "color": (1, 0, 0),
        "static": False,
    },
    {
        "name": "green_cube",
        "kind": "box",
        "x": -0.300,
        "y": -0.190,
        "z": 0.762,
        "qpos": [1, 0, 0, 0],
        "yaw_axis": 2,
        "half_size": (0.02, 0.02, 0.02),
        "color": (0, 1, 0),
        "static": False,
    },
    {
        "name": "blue_cube",
        "kind": "box",
        "x": -0.040,
        "y": 0.000,
        "z": 0.762,
        "qpos": [1, 0, 0, 0],
        "yaw_axis": 2,
        "half_size": (0.02, 0.02, 0.02),
        "color": (0, 0, 1),
        "static": False,
    },
    {
        "name": "cards",
        "kind": "actor",
        "model": "081_playingcards",
        "model_id": 0,
        "x": 0.200,
        "y": -0.190,
        "z": 0.741,
        "qpos": [0, 0, 0.707, 0.707],
        "yaw_axis": 1,
        "static": False,
        "mass": 0.02,
    },
    {
        "name": "roller",
        "kind": "actor",
        "model": "102_roller",
        "model_id": 0,
        "x": -0.330,
        "y": -0.250,
        "z": 0.741,
        "qpos": [0.5, 0.5, 0.5, 0.5],
        "yaw_axis": 1,
        "static": False,
        "mass": 0.05,
    },
    {
        "name": "can",
        "kind": "actor",
        "model": "071_can",
        "model_id": 0,
        "x": -0.060,
        "y": -0.070,
        "z": 0.741,
        "qpos": [0.5, 0.5, 0.5, 0.5],
        "yaw_axis": 1,
        "static": False,
        "mass": 0.05,
    },
]

# (arm, contact_point_id). The id is the pinch whose fingers stay inside the
# empty lane of that slot. Plate and knob are omitted: their assets have no
# pinch contact.
GRASP_PLAN = {
    "bell": ("right", 0),
    "button": ("left", 0),
    "hammer": ("right", 0),
    "scanner": ("left", 0),
    "cup": ("right", 0),
    "blue_pad": ("left", 0),
    "yellow_pad": ("left", 0),
    "purple_pad": ("right", 0),
    "red_cube": ("left", 0),
    "green_cube": ("left", 0),
    "blue_cube": ("left", 1),
    "cards": ("right", 0),
    "roller": ("left", 0),
    "can": ("left", 2),
}


def _jittered_pose(rng, spec):
    yaw = float(rng.uniform(-np.deg2rad(5.0), np.deg2rad(5.0)))
    angles = [0.0, 0.0, 0.0]
    angles[spec["yaw_axis"]] = yaw
    quat = t3d.quaternions.qmult(
        np.asarray(spec["qpos"], dtype=np.float64),
        t3d.euler.euler2quat(angles[0], angles[1], angles[2]),
    )
    return sapien.Pose(
        [
            spec["x"] + float(rng.uniform(-0.01, 0.01)),
            spec["y"] + float(rng.uniform(-0.01, 0.01)),
            spec["z"],
        ],
        quat,
    )


def _aim_head_camera(task):
    # D435 vertical FOV is 37 degrees. The embodiment default sits low and
    # crops the left, right, and near edges. This pose is only applied to the
    # shared table, and looks at the middle of the tabletop.
    cameras = getattr(task, "cameras", None)
    if cameras is None:
        return
    camera = None
    for cam, name in zip(cameras.static_camera_list, cameras.static_camera_name):
        if name == "head_camera":
            camera = cam
            break
    if camera is None:
        return
    position = np.array([0.0, -0.42, 1.70])
    target = np.array([0.0, 0.02, 0.74])
    forward = target - position
    forward = forward / np.linalg.norm(forward)
    left = np.array([-1.0, 0.0, 0.0])
    up = np.cross(forward, left)
    up = up / np.linalg.norm(up)
    mat = np.eye(4)
    mat[:3, 0] = forward
    mat[:3, 1] = left
    mat[:3, 2] = up
    mat[:3, 3] = position
    camera.entity.set_pose(sapien.Pose(mat))


def build_shared_table(task, seed, objects=None):
    """Build the shared table. ``objects`` overrides TABLE_OBJECTS for a variation."""
    _aim_head_camera(task)
    rng = np.random.RandomState(int(seed))
    actors = {}
    for spec in (TABLE_OBJECTS if objects is None else objects):
        pose = _jittered_pose(rng, spec)
        if spec["kind"] == "box":
            actor = create_box(
                scene=task,
                pose=pose,
                half_size=spec["half_size"],
                color=spec["color"],
                name=spec["name"],
                is_static=spec["static"],
            )
            model = None
            model_id = None
        elif spec["kind"] == "urdf":
            actor = create_sapien_urdf_obj(
                scene=task,
                pose=pose,
                modelname=spec["model"],
                modelid=spec["model_id"],
                fix_root_link=True,
            )
            if actor is None:
                raise RuntimeError(f"failed to create {spec['model']} id={spec['model_id']}")
            model = spec["model"]
            model_id = spec["model_id"]
        else:
            actor = create_actor(
                scene=task,
                pose=pose,
                modelname=spec["model"],
                model_id=spec["model_id"],
                convex=True,
                is_static=spec["static"],
            )
            if actor is None:
                raise RuntimeError(f"failed to create {spec['model']} id={spec['model_id']}")
            if spec["mass"] is not None:
                actor.set_mass(spec["mass"])
            model = spec["model"]
            model_id = spec["model_id"]
        actor.set_name(spec["name"])
        task.add_prohibit_area(actor, padding=0.03)
        actors[spec["name"]] = {
            "actor": actor,
            "model": model,
            "model_id": model_id,
        }
    return actors
