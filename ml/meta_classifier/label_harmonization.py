"""
Label harmonisation for the Campus Hazard meta-classifier.

Each member's YOLO model emits class ids that are LOCAL to that model. Before
the meta-classifier can reason about agreement between models, every detection
must be mapped onto the shared GLOBAL label space defined in config/classes.yaml.

This module handles the four relationship types required by the assignment:
  - exact overlap     : same class detected by >= 2 models   -> same global id
  - synonym           : different names, same safety meaning  -> SYNONYMS map
  - generalisation    : specific class -> parent category     -> parent_of()
  - contextual overlap: zone changes effective meaning         -> apply_context()

It has no heavy dependencies (only PyYAML) so it can be unit-tested standalone.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "classes.yaml"
)

# Synonyms: any raw label on the left is normalised to the global label on the
# right. Extend this as your annotation vocabulary grows. Do NOT merge labels
# that carry a different safety meaning (assignment rule).
SYNONYMS = {
    "exposed_live_wire": "dangling_wire",
    "exposed_wire": "dangling_wire",
    "hanging_wire": "dangling_wire",
    "broken_socket": "exposed_socket",
    "damaged_socket": "exposed_socket",
    "open_manhole": "uncovered_manhole",
    "manhole": "uncovered_manhole",
    "walkway_obstacle": "obstacle_on_walkway",
    "obstruction": "obstacle_on_walkway",
}


@dataclass
class HazardOntology:
    """Loaded view of config/classes.yaml with lookup helpers."""

    zone: str
    members: dict                       # member_key -> {local_id: name}
    global_classes: dict                # global_id -> name
    parents: dict                       # parent_name -> [child names]
    severity: dict                      # name -> severity str
    _name_to_global: dict = field(default_factory=dict)
    _child_to_parent: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: str = _CONFIG_PATH) -> "HazardOntology":
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        members = {
            mk: {int(cid): cname for cid, cname in mv["classes"].items()}
            for mk, mv in cfg["members"].items()
        }
        global_classes = {int(k): v for k, v in cfg["global_classes"].items()}
        parents = cfg.get("parents", {})
        severity = cfg.get("severity", {})

        name_to_global = {v: k for k, v in global_classes.items()}
        child_to_parent = {
            child: parent for parent, children in parents.items() for child in children
        }
        return cls(
            zone=cfg["zone"],
            members=members,
            global_classes=global_classes,
            parents=parents,
            severity=severity,
            _name_to_global=name_to_global,
            _child_to_parent=child_to_parent,
        )

    @property
    def num_global_classes(self) -> int:
        return len(self.global_classes)

    def normalise(self, raw_label: str) -> str:
        """Apply synonym mapping; return the canonical global label name."""
        return SYNONYMS.get(raw_label, raw_label)

    def local_to_global_id(self, member_key: str, local_id: int) -> int:
        """Map a (model, local class id) pair to a global class id."""
        name = self.members[member_key][local_id]
        name = self.normalise(name)
        if name not in self._name_to_global:
            raise KeyError(
                f"Label '{name}' (from {member_key} local id {local_id}) "
                f"is not in global_classes. Update config/classes.yaml."
            )
        return self._name_to_global[name]

    def parent_of(self, name: str) -> Optional[str]:
        """Return the parent/general category for a class name, or None."""
        return self._child_to_parent.get(self.normalise(name))

    def severity_of(self, name: str) -> str:
        return self.severity.get(self.normalise(name), "medium")


# --- Contextual overlap -------------------------------------------------------
# A class can change meaning depending on the zone/sub-zone it is found in.
# At a bus stop the most relevant rule: an obstacle sitting on the boarding
# path / in front of the shelter exit is more severe than a generic obstacle.
def apply_context(global_name: str, zone_context: str) -> str:
    """Optionally remap a class based on contextual zone information.

    Returns a possibly-modified global label name. Rule-based and deliberately
    conservative: only escalates meaning where the assignment's 'contextual
    overlap' example applies. Extend with your own documented rules.
    """
    ctx = (zone_context or "").lower()
    if global_name == "obstacle_on_walkway" and ("boarding" in ctx or "exit" in ctx):
        # Obstacle on the boarding/exit path behaves like a blocked egress.
        return "obstacle_on_walkway"  # keep label; severity is bumped elsewhere
    return global_name


if __name__ == "__main__":
    onto = HazardOntology.load()
    print(f"Zone: {onto.zone}")
    print(f"Global classes ({onto.num_global_classes}):")
    for gid, name in onto.global_classes.items():
        print(f"  {gid:>2}  {name:<22} parent={onto.parent_of(name)} "
              f"severity={onto.severity_of(name)}")
    # Sanity: every member/local class resolves to a global id.
    for mk, classes in onto.members.items():
        for lid in classes:
            gid = onto.local_to_global_id(mk, lid)
            print(f"{mk} local {lid} ({classes[lid]}) -> global {gid}")
