#!/usr/bin/env python3
from __future__ import print_function
import os
import sys
from collections import defaultdict
import gemmi

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
    return '%s %g %s' % (st.get_info('_entry.id'), st.cell.volume, stat)

def main():
    for path in sorted_search(sys.argv[1]):
        print(get_file_stats(path))

main()
