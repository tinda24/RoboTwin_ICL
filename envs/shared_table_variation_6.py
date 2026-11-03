"""Shared-table layout variation 6.

Same 16 objects as ``shared_table``. Each object keeps its height, orientation,
and model. Only the horizontal slot is reassigned, and the assignment is fixed.
"""

from copy import deepcopy

from .shared_table import GRASP_PLAN as _BASE_GRASP
from .shared_table import TABLE_OBJECTS as _BASE_OBJECTS
from .shared_table import build_shared_table as _build_shared_table

# Object name -> the original occupant of the slot it now uses.
_SLOT = {
    "bell": "scanner",
    "button": "purple_pad",
    "knob": "blue_cube",
    "hammer": "button",
    "scanner": "red_cube",
    "plate": "plate",
    "cup": "yellow_pad",
    "blue_pad": "can",
    "yellow_pad": "cards",
    "purple_pad": "hammer",
    "red_cube": "green_cube",
    "green_cube": "knob",
    "blue_cube": "cup",
    "cards": "blue_pad",
    "roller": "bell",
    "can": "roller",
}


def _layout():
    slots = {spec["name"]: (spec["x"], spec["y"]) for spec in _BASE_OBJECTS}
    objects = []
    for spec in _BASE_OBJECTS:
        spec = deepcopy(spec)
        spec["x"], spec["y"] = slots[_SLOT[spec["name"]]]
        objects.append(spec)
    return objects


TABLE_OBJECTS = _layout()


def _grasp_plan():
    plan = {}
    for spec in TABLE_OBJECTS:
        name = spec["name"]
        if name not in _BASE_GRASP:
            continue
        arm = "left" if spec["x"] < 0.05 else "right"
        plan[name] = (arm, _BASE_GRASP[name][1])
    return plan


GRASP_PLAN = _grasp_plan()


def build_shared_table(task, seed):
    return _build_shared_table(task, seed, objects=TABLE_OBJECTS)
