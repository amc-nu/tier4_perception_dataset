from perception_dataset.t4_dataset.trailer_merge import bev_gap, merge_trailers


def box(x, y, size=(2.0, 6.0, 3.0), z=1.5):
    return {"translation": [x, y, z], "rotation": [1, 0, 0, 0], "size": list(size)}


def test_gap_overlap_and_distance():
    assert bev_gap(box(0, 0), box(5, 0)) == 0.0  # overlap
    assert abs(bev_gap(box(0, 0), box(7, 0)) - 1.0) < 1e-9  # 6m long boxes, centers 7m apart


def test_merge_within_gap_and_standalone():
    truck, trailer, far = box(0, 0), box(7, 0, (2.0, 8.0, 4.0), z=2.0), box(100, 0, (2.0, 8.0, 4.0))
    out = merge_trailers([truck, trailer, far], [False, True, True], [True, False, False], 1.0)
    assert len(out) == 2
    merged = out[0]
    assert abs(merged["translation"][0] - 4.0) < 1e-9 and abs(merged["size"][1] - 14.0) < 1e-9
    assert abs(merged["size"][2] - 4.0) < 1e-9
    assert out[1] is far
    out = merge_trailers([truck, box(7.5, 0)], [False, True], [True, False], 1.0)
    assert len(out) == 2  # gap 1.5 > 1.0
