#!/usr/bin/env python3
"""Check the tracked v9 export without requiring Fusion or modifying meshes."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct

BASE = Path(__file__).resolve().parents[1] / 'cad' / 'v9'


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


def main():
    manifest = json.loads((BASE / 'manifest-sha256.json').read_text())
    for name, expected in manifest.items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == expected, f'Changed export: {name}'
    report = json.loads((BASE / 'validation.json').read_text())
    assert report['installed_print_count'] == 3 and not report['health_warnings'] and not report['interference']
    paths = sorted((BASE / 'stl').glob('*.stl'))
    assert len(paths) == 5
    for path in paths:
        check_mesh(path)
    print('v9 manifest and five connected, closed, consistently wound meshes passed.')


if __name__ == '__main__':
    main()
