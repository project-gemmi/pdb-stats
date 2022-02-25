#!/usr/bin/env python3
from __future__ import print_function
import os
import sys
from collections import defaultdict
import gemmi

PLAIN_TEXT = False
CCD_PATH = 'components.cif.gz'
#MON_LIB_DIR = os.path.expanduser('~/checkout/monomers')
MON_LIB_DIR = os.path.expanduser('~/ccp4/ccp4-7.1/lib/data/monomers')
MON_LIB_LIST = MON_LIB_DIR + '/list/mon_lib_list.cif'


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
        ent = st.get_entity_of(chain.get_polymer())
        idx = 1
        if ent is not None and ent.entity_type == gemmi.EntityType.Polymer:
            idx = 0
        for res in chain:
            counters[res.name][idx] += 1
    stat = ' '.join('%s:%d:%d' % (k, v[0], v[1]) for k, v in counters.items())
    return (st.info['_entry.id'], st.cell.volume_per_image(),
            st.resolution or 8, stat)


def main():
    # stage 1: reading PDB data
    pdb_data = []
    for arg in sys.argv[1:]:
        for path in sorted_search(arg):
            try:
                item = get_file_stats(path)
            except RuntimeError as e:
                sys.stderr.write('Failed to read %s: %s\n' % (path, e))
                continue
            pdb_data.append(item)
            if PLAIN_TEXT:
                print('%s %5.0f %3.1g  %s' % item)

    # stage 2: gathering per-component statistics
    stats = defaultdict(lambda: {'cat': None, 'files': 0, 'poly': 0,
                                 'nonpoly': 0, 'pdb': (None, 0)})
    for item in pdb_data:
        pdb_id, volume, resolution, rest = item
        if volume < 10 or volume != volume:
            volume = 1e12
        score_mult = 1.0 / volume / resolution
        for item in rest.split():
            comp, poly, nonpoly = item.split(':')
            d = stats[comp]
            d['files'] += 1
            d['poly'] += int(poly)
            d['nonpoly'] += int(nonpoly)
            score = (int(poly) + int(nonpoly)) * score_mult
            if score > d['pdb'][1]:
                d['pdb'] = (pdb_id, score)

    # stage 2a: add category from components.cif; also, count metal atoms
    ccd_category = {}
    metal_count = {}
    ccd = gemmi.cif.read(CCD_PATH)
    for block in ccd:
        comp_id = block.find_value('_chem_comp.id')
        ccd_category[comp_id] = block.find_value('_chem_comp.type')
        symbols = block.find_values('_chem_comp_atom.type_symbol')
        metal_count[comp_id] = sum(gemmi.Element(s).is_metal for s in symbols)

    # stage 2b: add category from the Refmac monomer library
    monlist = gemmi.cif.read(MON_LIB_LIST)['comp_list']
    refmac_category = {cc[0]: cc[1]
                       for cc in monlist.find('_chem_comp.', ['id', 'group'])}

    # stage 3: output
    total_files = len(pdb_data)
    if not PLAIN_TEXT:
        print('{\n"file_count": %d,\n"data": [' % total_files, end='')
    sep = ''
    for key in sorted(stats.keys(), key=lambda k: -stats[k]['files']):
        cat = ccd_category.get(key, '?').strip('"\'').lower()
        cat = cat.replace('beta', '\u03B2')
        cat = cat.replace('gamma', '\u03B3')
        cat = cat.replace('delta', '\u03B4')
        if 'terminus' in cat:
            cat = cat.replace('NH3 amino terminus', 'N-terminus')
            cat = cat.replace('cooh carboxy terminus', 'C-terminus')
            cat = cat.replace('oh 3 prime terminus', "3'-terminus")
            cat = cat.replace('oh 5 prime terminus', "5'-terminus")
        rcat = refmac_category.get(key, 'n/a').lower().strip('"')
        d = stats[key]
        total = d['poly'] + d['nonpoly']
        poly_percent = 100.0 * d['poly'] / total
        example = d['pdb'][0]
        if PLAIN_TEXT:
            print('%3s %2d %7d %5d %7.3f %s' %
                  (key, metal_count[key], d['files'], total,
                   poly_percent, example))
        else:
            print('%s\n["%s",%d,"%s","%s",%d,%d,%.3f,"%s"]' %
                  (sep, key, metal_count[key], cat, rcat, d['files'], total,
                   poly_percent, example),
                  end='')
        sep = ','
    if not PLAIN_TEXT:
        print('\n]\n}')


if __name__ == '__main__':
    main()
