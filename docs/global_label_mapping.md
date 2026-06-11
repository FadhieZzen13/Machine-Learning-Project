# Global Label Mapping Table

Required by assignment §5 ("Overlapping and Hierarchical Class Design"). This
table is the human-readable companion to `config/classes.yaml`. Update both
together.

## Global class set (meta-classifier output)

| Global ID | Class | Parent category | Default severity | Detected by |
|-----------|-------|-----------------|------------------|-------------|
| 0 | pothole | hole_in_ground | medium | M1, M2 |
| 1 | uncovered_manhole | hole_in_ground | high | M1, M3 |
| 2 | open_drain | hole_in_ground | high | M1 |
| 3 | cracked_pavement | surface_defect | low | M1 |
| 4 | obstacle_on_walkway | obstruction | medium | M1, M3 |
| 5 | dangling_wire | electrical | high | M2, M3 |
| 6 | broken_bench | structural | low | M2 |
| 7 | broken_shelter_panel | structural | medium | M2 |
| 8 | exposed_socket | electrical | high | M2 |
| 9 | fallen_branch | obstruction | medium | M3 |
| 10 | missing_barricade | boundary | medium | M3 |

## Overlap design (assignment rule: ≥ 2 overlapping classes per member)

| Member | Focus | 5 classes | Overlaps with |
|--------|-------|-----------|---------------|
| M1 | Ground & surface | pothole, uncovered_manhole, open_drain, cracked_pavement, obstacle_on_walkway | pothole→M2, uncovered_manhole→M3, obstacle_on_walkway→M3 (3 overlaps) |
| M2 | Shelter structure & electrical | pothole, dangling_wire, broken_bench, broken_shelter_panel, exposed_socket | pothole→M1, dangling_wire→M3 (2 overlaps) |
| M3 | Obstruction & boundary | uncovered_manhole, dangling_wire, obstacle_on_walkway, fallen_branch, missing_barricade | uncovered_manhole→M1, dangling_wire→M2, obstacle_on_walkway→M1 (3 overlaps) |

## Relationship handling (assignment §5 four types)

| Relationship | Example here | Handling |
|--------------|--------------|----------|
| Exact overlap | M1 & M2 both detect `pothole`; M2 & M3 both detect `dangling_wire` | Cross-model agreement (count + mean IoU) becomes a meta-classifier feature; see `feature_extraction.py` agreement features. |
| Synonym | `exposed_live_wire`, `hanging_wire` → `dangling_wire`; `broken_socket` → `exposed_socket` | Normalised in `label_harmonization.SYNONYMS`. Labels with different safety meaning are NOT merged. |
| Generalisation | `pothole`, `uncovered_manhole`, `open_drain` → parent `hole_in_ground` | Parent one-hot kept as a feature alongside the specific class; see `parents` in `classes.yaml`. |
| Contextual overlap | `obstacle_on_walkway` on the boarding/exit path = blocked egress | Zone/context feature + `apply_context()` rule before meta-classification. |

## Justification (campus maintenance relevance — for §2 of report)

The bus stop & waiting area concentrates **pedestrian flow + vehicle traffic +
fixed infrastructure (shelter, seating, lighting)**, so it naturally exposes
ground hazards (pothole/manhole/drain near the kerb), structural/electrical
hazards (shelter panels, benches, lighting wiring/sockets), and obstruction/
boundary hazards (debris on the boarding path, missing barricades). The shared
overlap classes (pothole, manhole, dangling wire, walkway obstacle) are exactly
the high-traffic, high-consequence hazards where a second model's agreement
should raise confidence — which is what the meta-classifier is designed to use.
