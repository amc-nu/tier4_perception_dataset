# T4 → Autoware class mapping and merge rules

## Processing order (per frame)

1. Merge trailers into neighbouring trucks (original T4 classes).
2. Step 1: T4 class → internal class (`null` = dropped).
3. Step 2: internal class → Autoware label.

## Trailer merge rules

- Applied per frame, on original T4 classes, before any class mapping.
- A trailer (`truck.trailer`, `semi_trailer`) is merged into a `truck` (incl. `truck.common`, `tractor_unit`) or `construction_vehicle` (`truck.construction`) when the BEV
  edge-to-edge gap between the two box footprints is `<= 1.0 m`, or the footprints overlap.
- If several candidates qualify, the nearest one is used.
- Merged box: minimum oriented BEV box around both boxes, yaw of the truck,
  z-extent as the union of both. The track instance and attributes of the truck are kept.
- All other classes (`fire_truck`, `forklift`, ...) are never merge partners and stay as is.
- A trailer with no partner within range stays a standalone box and maps to `truck`.

## Final mapping

Dataset categories (as in `category.json`) → table class → Autoware label.

| Dataset category | Table class | Step 1 | Autoware label |
|---|---|---|---|
| car, car.common | car | car | CAR |
| car.emergency | emergency_vehicle | car | CAR |
| police_car | police_car | car | CAR |
| ambulance | ambulance | car | CAR |
| car.special | other_vehicle | car | CAR |
| truck, truck.common | truck | truck | TRUCK |
| truck.emergency | fire_truck | truck | TRUCK |
| truck.construction, construction_vehicle | construction_vehicle | truck | TRUCK |
| tractor_unit | truck | truck | TRUCK |
| truck.trailer, semi_trailer | trailer | truck | TRUCK (after merge) |
| bus | bus | bus | BUS |
| motorcycle | motorcycle | motorcycle | MOTORCYCLE |
| bicycle | bicycle | bicycle | BICYCLE |
| pedestrian, pedestrian.common | pedestrian | pedestrian | PEDESTRIAN |
| pedestrian.stroller | stroller | pedestrian | PEDESTRIAN |
| pedestrian.personal_mobility, personal_mobility | personal_mobility | pedestrian | PEDESTRIAN |
| construction_worker, police_officer, wheelchair | pedestrian | pedestrian | PEDESTRIAN |
| animal | animal | animal | ANIMAL |
| barrier.movable | barrier | barrier | HAZARD |
| barrier.construction_sign | construction_sign | barrier | HAZARD |
| traffic_cone | traffic_cone | traffic_cone | HAZARD |
| debris.unclassified | debris | debris | HAZARD |
| debris.pushable_pullable | pushable_pullable | debris | HAZARD |
| train | train | null | dropped |
| every other category (ignored, ego_vehicle, driveable_flat, manmade.*, vegetation, curb.*, noise.*, traffic_sign, traffic_light, ...) | n/a | null | dropped |

Step 1 table classes not present in the datasets (`kart`, `bicycle_rack`, `other_stuff`, `open_door`,
`vehicle_protruding_object`) map as in the original YAML (`kart` → car, the rest dropped).

Notes:
- `Label::TRAILER` is never produced, because step 1 maps `trailer` to `truck`.
- `Label::UNKNOWN` is never produced, because unmapped and null classes are dropped before step 2.
