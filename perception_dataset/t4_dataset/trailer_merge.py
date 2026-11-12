"""Merge trailer boxes into the nearest parent vehicle box (BEV edge-to-edge gap)."""
from typing import Any, Dict, List, Sequence

import numpy as np
from scipy.spatial.transform import Rotation


def _yaw(q_wxyz: Sequence[float]) -> float:
    w, x, y, z = q_wxyz
    return float(Rotation.from_quat([x, y, z, w]).as_euler("zyx")[0])


def bev_corners(ann: Dict[str, Any]) -> np.ndarray:
    """4x2 BEV corners. T4 size is [width, length, height]; local x = length, y = width."""
    width, length, _ = ann["size"]
    yaw = _yaw(ann["rotation"])
    c, s = np.cos(yaw), np.sin(yaw)
    local = np.array([[1, 1], [-1, 1], [-1, -1], [1, -1]]) * [length / 2, width / 2]
    return local @ np.array([[c, s], [-s, c]]) + np.asarray(ann["translation"][:2])


def _point_segment_dist(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0.0, 1.0)
    return float(np.linalg.norm(p - (a + t * ab)))


def _overlap(p: np.ndarray, q: np.ndarray) -> bool:
    """Separating axis test for two convex polygons."""
    for poly in (p, q):
        for i in range(len(poly)):
            edge = poly[(i + 1) % len(poly)] - poly[i]
            axis = np.array([-edge[1], edge[0]])
            pp, qq = p @ axis, q @ axis
            if pp.max() < qq.min() or qq.max() < pp.min():
                return False
    return True


def bev_gap(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    """Edge-to-edge distance of the BEV footprints, 0 if they overlap or touch."""
    p, q = bev_corners(a), bev_corners(b)
    if _overlap(p, q):
        return 0.0
    return min(
        _point_segment_dist(v, poly[i], poly[(i + 1) % len(poly)])
        for poly_v, poly in ((p, q), (q, p))
        for v in poly_v
        for i in range(len(poly))
    )


def _merge_into(parent: Dict[str, Any], trailers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Oriented box (parent yaw) around parent and trailers, z-extent is the union."""
    yaw = _yaw(parent["rotation"])
    c, s = np.cos(yaw), np.sin(yaw)
    to_local = np.array([[c, s], [-s, c]])
    origin = np.asarray(parent["translation"][:2])
    boxes = [parent, *trailers]
    pts = np.vstack([(bev_corners(b) - origin) @ to_local.T for b in boxes])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    center = origin + ((lo + hi) / 2) @ to_local
    z_lo = min(b["translation"][2] - b["size"][2] / 2 for b in boxes)
    z_hi = max(b["translation"][2] + b["size"][2] / 2 for b in boxes)
    merged = dict(parent)
    merged["translation"] = [float(center[0]), float(center[1]), (z_lo + z_hi) / 2]
    merged["size"] = [float(hi[1] - lo[1]), float(hi[0] - lo[0]), z_hi - z_lo]
    return merged


def merge_trailers(
    anns: List[Dict[str, Any]],
    is_trailer: List[bool],
    is_parent: List[bool],
    max_gap: float,
) -> List[Dict[str, Any]]:
    """Return anns with trailers within max_gap of a parent folded into the nearest parent.

    Trailers without a parent in range are kept as standalone boxes.
    """
    parents = [i for i, p in enumerate(is_parent) if p]
    assigned: Dict[int, List[int]] = {}
    absorbed = set()
    for i, trailer in enumerate(is_trailer):
        if not trailer:
            continue
        gaps = [(bev_gap(anns[i], anns[j]), j) for j in parents]
        gap, j = min(gaps, default=(np.inf, -1))
        if gap <= max_gap:
            assigned.setdefault(j, []).append(i)
            absorbed.add(i)
    out = []
    for i, ann in enumerate(anns):
        if i in absorbed:
            continue
        out.append(_merge_into(ann, [anns[t] for t in assigned[i]]) if i in assigned else ann)
    return out
