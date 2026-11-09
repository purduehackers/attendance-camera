#!/usr/bin/env python3
"""Check current and archived exports without Fusion or modifying meshes."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct

CAD = Path(__file__).resolve().parents[1] / 'cad'


def check_mesh(path):
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 80)[0]
    assert len(data) == 84 + 50 * count, f'{path.name}: invalid binary STL length'
    edges = defaultdict(list)
    volume = 0
    for index in range(count):
        face = struct.unpack_from('<12fH', data, 84 + 50 * index)
        a, b, c = vertices = [tuple(round(v, 5) for v in face[j:j+3]) for j in (3, 6, 9)]
        assert len(set(vertices)) == 3, f'{path.name}: degenerate face'
        for j in range(3):
            first, second = vertices[j], vertices[(j+1) % 3]
            edges[tuple(sorted((first, second)))].append((index, first < second))
        volume += (a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    adjacent = [[] for _ in range(count)]
    for uses in edges.values():
        assert len(uses) == 2 and uses[0][1] != uses[1][1], f'{path.name}: nonmanifold/inconsistent edge'
        first, second = uses[0][0], uses[1][0]
        adjacent[first].append(second)
        adjacent[second].append(first)
    unseen = set(range(count))
    queue = [unseen.pop()]
    while queue:
        for face in adjacent[queue.pop()]:
            if face in unseen:
                unseen.remove(face)
                queue.append(face)
    assert not unseen, f'{path.name}: disconnected mesh'
    assert volume > 0, f'{path.name}: nonpositive volume'


def check_revision(revision):
    base = CAD / revision
    manifest = json.loads((base / 'manifest-sha256.json').read_text())
    actual = {str(p.relative_to(base)) for p in base.rglob('*')
              if p.is_file() and p.name != 'manifest-sha256.json'}
    assert actual == set(manifest), f'{revision}: manifest file set differs'
    for name, expected in manifest.items():
        assert hashlib.sha256((base / name).read_bytes()).hexdigest() == expected, f'Changed export: {name}'
    report = json.loads((base / 'validation.json').read_text())
    expected_installed = 10 if revision == 'v11' else 3
    assert report['installed_print_count'] == expected_installed and not report['health_warnings'] and not report['interference']
    assert report['camera_direction'] == [0, 0, -1]
    if revision == 'v10':
        hardware = json.loads((base / 'hardware.json').read_text())
        assert report['heat_set_inserts'] == 0 and report['nuts'] == 0
        assert hardware['inserts'] == [] and hardware['nuts'] == []
        for name, diameter in [('Pi', 2.1), ('camera', 1.7)]:
            faces = report['pilot_cylinder_checks'][name]
            assert len(faces) == 4 and all(f['diameter_mm'] == diameter for f in faces)
    if revision == 'v11':
        hardware = json.loads((base / 'hardware.json').read_text())
        assert report['unique_print_count'] == 7 and not report['open_pose_interference']
        assert report['heat_set_inserts'] == 0 and report['nuts'] == 8
        assert report['coupon_files'] == [] and hardware['inserts'] == []
        assert sum(p['quantity'] for p in report['parts']) == 10
        assert report['fastener_stack_mm']['M3_screw_length'] == 10
        assert report['fastener_stack_mm']['M3_tip_recess_above_jaw_bottom'] > 0
        cable = json.loads((base / 'cable-clearance.json').read_text())
        assert not cable['interference'] and cable['route_is_external']
        assert cable['pi_lower_housing_clearance_mm'] >= 1
        assert cable['power_route_including_housings_mm'] < 480
        assert cable['model_builder_sha256'] == hashlib.sha256(
            (CAD/'scripts/build_clamped_v11.py').read_bytes()).hexdigest()
        for name, diameter in [('Pi', 2.1), ('camera', 1.7)]:
            faces = report['pilot_cylinder_checks'][name]
            assert len(faces) == 4 and all(f['diameter_mm'] == diameter for f in faces)
    paths = sorted((base / 'stl').glob('*.stl'))
    expected_meshes = 7 if revision == 'v11' else 5
    assert len(paths) == expected_meshes
    for path in paths:
        check_mesh(path)
    print(f'{revision} manifest and {expected_meshes} connected, closed, consistently wound meshes passed.')


def main():
    for revision in ['v9', 'v10', 'v11']:
        check_revision(revision)


if __name__ == '__main__':
    main()
