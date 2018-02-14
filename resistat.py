#!/usr/bin/env python3
from __future__ import print_function
import os
import sys
from collections import defaultdict
import gemmi

PLAIN_TEXT = False


def sorted_search(top_dir):
    extensions = ['.cif', '.cif.gz', '.pdb', '.pdb.gz', '.ent', '.ent.gz']
    for root, dirs, files in os.walk(top_dir):
        dirs.sort()
        for name in sorted(files):
            if any(name.endswith(ext) for ext in extensions):
                yield os.path.join(root, name)


def get_file_stats(path):
    st = gemmi.read_structure(path)
    counters = defaultdict(lambda: [0, 0])
    for chain in st[0]:
        ent = st.find_entity(chain.entity_id)
        idx = 1
        if ent is not None and ent.entity_type == gemmi.EntityType.Polymer:
            idx = 0
        for res in chain:
            counters[res.name][idx] += 1
    stat = ' '.join('%s:%d:%d' % (k, v[0], v[1]) for k, v in counters.items())
    return (st.get_info('_entry.id'), st.cell.volume_per_image(),
            st.resolution or 5, stat)


def main():
    # stage 1: reading PDB data
    pdb_data = []
    for path in sorted_search(sys.argv[1]):
        item = get_file_stats(path)
        pdb_data.append(item)
        if PLAIN_TEXT:
            print('%s %5.0f %3.1g  %s' % item)

    # stage 2: gathering per-component statistics
    stats = defaultdict(lambda: {'cat': None, 'files': 0, 'poly': 0,
                                 'nonpoly': 0, 'pdb': (None, 0)})
    for item in pdb_data:
        pdb_id, volume, resolution, rest = item
        score_mult = float(resolution) / float(volume)
        for item in rest.split():
            comp, poly, nonpoly = item.split(':')
            d = stats[comp]
            d['files'] += 1
            d['poly'] += int(poly)
            d['nonpoly'] += int(nonpoly)
            score = (int(poly) + int(nonpoly)) * score_mult
            if score > d['pdb'][1]:
                d['pdb'] = (pdb_id, score)
    # TODO add category from components.cif

    # stage 3: output
    total_files = len(pdb_data)
    if not PLAIN_TEXT:
        print('{\n"data": [', end='')
    sep = ''
    for key in sorted(stats.keys(), key=lambda k: -stats[k]['files']):
        d = stats[key]
        file_percent = 100.0 * d['files'] / total_files
        total = d['poly'] + d['nonpoly']
        poly_percent = 100.0 * d['poly'] / total
        example = d['pdb'][0]
        if PLAIN_TEXT:
            print('%3s %7.3f %5d %7.3f %s' %
                  (key, file_percent, total, poly_percent, example))
        else:
            print('%s\n["%s",%.3f,%d,%.3f,"%s"]' %
                  (sep, key, file_percent, total, poly_percent, example),
                  end='')
        sep = ','
    if not PLAIN_TEXT:
        print('\n]\n}')


if __name__ == '__main__':
    main()
