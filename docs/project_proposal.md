# Campus Hazard Detection: Project Proposal

**Course:** CSC4602
**Zone:** Bus Stop & Waiting Area
**Group:** 4 members (M1 to M4)

## 1. Problem and scope

Bus stops and their waiting areas collect physical safety hazards over time:
potholes, uncovered manholes, open drains, dangling wires, broken shelter panels,
exposed sockets, fallen branches, and objects blocking the walkway. Manual
inspection is slow and easy to skip. We propose a mobile system that an inspector
points at a bus stop, which then detects the hazards in view, classifies each one,
and suggests a maintenance action.

The system uses four YOLOv8 detectors, one trained by each member, combined by a
neural-network meta-classifier that produces a single hazard label per object. A
language model then writes a short recommended action for each detection. The
four-detector split lets every member train and own a model, which the
assignment requires (§16), and gives the meta-classifier cross-model agreement to
work with.

## 2. Zone definition

The target zone is the bus stop and its waiting area. For context features we
divide it into sub-zones that the app can report with each frame:

| Sub-zone | Meaning |
|---|---|
| bus_stop | the stop structure and its immediate surroundings |
| waiting_area | seating and standing area under or beside the shelter |
| boarding_path | the strip where passengers board and alight |
| road | the carriageway edge next to the stop |
| unknown | sub-zone not specified |

The sub-zone matters because the same object can be more or less dangerous
depending on where it sits. An obstacle on the boarding path blocks passenger
movement more directly than the same obstacle off to one side.

## 3. Hazard classes

Each member trains one model over five classes (local ids 0 to 4). The union of
the four class sets gives 11 global classes, which is what the meta-classifier
outputs.

| Global id | Class | Parent category | Default severity |
|----:|---|---|---|
| 0 | pothole | hole_in_ground | medium |
| 1 | uncovered_manhole | hole_in_ground | high |
| 2 | open_drain | hole_in_ground | high |
| 3 | cracked_pavement | surface_defect | low |
| 4 | obstacle_on_walkway | obstruction | medium |
| 5 | dangling_wire | electrical | high |
| 6 | broken_bench | structural | low |
| 7 | broken_shelter_panel | structural | medium |
| 8 | exposed_socket | electrical | high |
| 9 | fallen_branch | obstruction | medium |
| 10 | missing_barricade | boundary | medium |

Severity is set per class up front, so electrical and fall hazards stay high
regardless of model confidence. The parent categories group related classes and
feed a generalisation feature (see §5).

## 4. Member roles

Each member sources and annotates their own dataset, trains their model, and
records its evaluation numbers. Section ownership in the report follows the same
split.

| Member | Focus | Classes (local ids 0 to 4) |
|---|---|---|
| M1 | Ground and surface hazards around the stop | pothole, uncovered_manhole, open_drain, cracked_pavement, obstacle_on_walkway |
| M2 | Shelter structure and electrical hazards | pothole, dangling_wire, broken_bench, broken_shelter_panel, exposed_socket |
| M3 | Obstruction and boundary hazards | uncovered_manhole, dangling_wire, obstacle_on_walkway, fallen_branch, missing_barricade |
| M4 | Fixtures, drainage, and debris (second-pass coverage) | open_drain, broken_bench, broken_shelter_panel, exposed_socket, fallen_branch |

M3 also sets up the shared configuration, the backend pipeline, the
meta-classifier, and the mobile app scaffold, so the four models plug into a
common system.

## 5. Overlap strategy

The assignment asks each member to share at least two classes with others. We
designed the overlap so every shared class has at least two detectors looking at
it, which is the signal the meta-classifier learns from.

| Overlapping class | Detected by |
|---|---|
| pothole | M1, M2 |
| uncovered_manhole | M1, M3 |
| obstacle_on_walkway | M1, M3 |
| dangling_wire | M2, M3 |
| open_drain | M1, M4 |
| broken_bench | M2, M4 |
| broken_shelter_panel | M2, M4 |
| exposed_socket | M2, M4 |
| fallen_branch | M3, M4 |

M4 is a second-pass detector. It adds a second opinion to classes that would
otherwise have had only one model, so more classes carry an agreement signal.

The label layer handles the four relationship types the assignment lists:

- Exact overlap: two models detect the same class, which maps to the same global
  id (both pothole map to id 0).
- Synonym: different names with the same safety meaning map to one global label
  (for example, hanging_wire maps to dangling_wire).
- Generalisation: each class maps to a parent category (pothole, uncovered_manhole,
  and open_drain all map to hole_in_ground), which the meta-classifier uses as a
  feature.
- Contextual overlap: the sub-zone can change effective meaning, so an obstacle on
  the boarding path is treated as more severe than a generic obstacle.

## 6. Planned app architecture

We will run inference on a backend service rather than on the phone. A single
detector could be exported to run on-device, but fusing four models and calling a
language model is simpler to manage on a server, and it keeps the phone light. The
phone captures a frame, sends it to the backend, and draws the result.

```
Phone camera ── frame ──▶ Flask backend
                          │
                          ├─ YOLO M1
                          ├─ YOLO M2 ──▶ label harmonisation (local ids to global ids)
                          ├─ YOLO M3
                          └─ YOLO M4
                          │
                          ▼
                  IoU grouping of overlapping detections
                          │
                          ▼
                  feature vector per object group
                          │
                          ▼
                  neural-network meta-classifier ──▶ global class
                          │
                          ▼
                  severity lookup + language-model action
                          │
Phone overlay ◀── JSON ───┘
```

The stages:

1. Detection. Each YOLO model runs on the frame and returns boxes with local
   class ids and confidence.
2. Harmonisation. Local ids map to the 11 global classes through the shared
   configuration.
3. Grouping. Detections whose boxes overlap (IoU above a threshold) are grouped
   as one physical object, so agreement across models can be measured.
4. Feature vector. Each group becomes one fixed-length vector that records which
   models fired, their confidence and class, the merged box, an agreement score,
   the sub-zone, and the parent category.
5. Meta-classification. A small multilayer perceptron maps the vector to one
   global class with a confidence score.
6. Action. The class gets a severity from the configuration and a short
   recommended action from a language model, with an offline fallback so the app
   still works without a network or API key.
7. Display. The phone draws boxes coloured by severity and lists each hazard with
   its class, confidence, how many models agreed, and the recommended action.

The backend exposes three endpoints: a health check, a hazard inference endpoint
that takes a frame, and a recommendation endpoint that returns an action for a
given hazard. The mobile app is built in Flutter and runs on Android.

## 7. Deliverables

- A trained YOLO model per member, with evaluation numbers.
- The meta-classifier and the fusion pipeline.
- The backend service and the Flutter app.
- The technical report, screencast, and logbook.
