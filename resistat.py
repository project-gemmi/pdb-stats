#!/usr/bin/env python3
from __future__ import print_function
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
import gemmi

PLAIN_TEXT = False
CCD_PATH = 'components.cif.gz'
#MON_LIB_DIR = os.path.expanduser('~/checkout/monomers')
MON_LIB_DIR = os.path.expanduser('~/ccp4/ccp4-8.0/lib/data/monomers')
MON_LIB_LIST = MON_LIB_DIR + '/list/mon_lib_list.cif'


def sorted_search(top_dir):
    extensions = ['.cif', '.cif.gz']
    for root, dirs, files in os.walk(top_dir):
        dirs.sort()
        for name in sorted(files):
            if any(name.endswith(ext) for ext in extensions):
                yield os.path.join(root, name)

@dataclass(slots=True)
class ResidueCounter:
    example: str = ''
    example_score: float = 0
    ccd_category: str = ''
    ml_group: str = 'n/a'
    metal_count: int = 0
    files: int = 0
    total: int = 0
    counts: dict = field(default_factory=lambda: defaultdict(int))

    def nice_category(self):
        cat = self.ccd_category.strip('"\'').lower()
        cat = cat.replace('beta', '\u03B2')
        cat = cat.replace('gamma', '\u03B3')
        cat = cat.replace('delta', '\u03B4')
        cat = cat.replace('linking', 'lin.')
        if 'terminus' in cat:
            cat = cat.replace('NH3 amino terminus', 'N-terminus')
            cat = cat.replace('cooh carboxy terminus', 'C-terminus')
            cat = cat.replace('oh 3 prime terminus', "3'-terminus")
            cat = cat.replace('oh 5 prime terminus', "5'-terminus")
        return cat

def calculate_score_mult(st):
    volume = st.cell.volume_per_image()
    resolution = st.resolution or 8
    if volume < 10 or volume != volume:
        volume = 1e12
    return 1.0 / volume / resolution

def entity_key(ent):
    if ent.entity_type == gemmi.EntityType.Polymer:
        if ent.polymer_type == gemmi.PolymerType.PeptideL:
            key = 'lpept'
        elif ent.polymer_type == gemmi.PolymerType.PeptideD:
            key = 'dpept'
        elif ent.polymer_type == gemmi.PolymerType.Dna:
            key = 'dna'
        elif ent.polymer_type == gemmi.PolymerType.Rna:
            key = 'rna'
        elif ent.polymer_type == gemmi.PolymerType.DnaRnaHybrid:
            key = 'dnarna'
        elif ent.polymer_type == gemmi.PolymerType.Other:
            key = 'other'
        elif ent.polymer_type == gemmi.PolymerType.Pna:
            key = 'other'  # we don't count pept. nucl. acid separately
        else:
            assert 0, ent.polymer_type
    elif ent.entity_type == gemmi.EntityType.Branched:
        key = 'branched'
    elif ent.entity_type == gemmi.EntityType.NonPolymer:
        key = 'nonpoly'
    elif ent.entity_type == gemmi.EntityType.Water:
        key = 'water'
    else:
        assert 0, ent.entity_type
    return key

def add_file_stats(path, counters):
    try:
        st = gemmi.read_structure(path)
    except RuntimeError as e:
        sys.stderr.write('Failed to read %s: %s\n' % (path, e))
        return
    totals = defaultdict(int)
    score_mult = calculate_score_mult(st)
    for chain in st[0]:
        for res in chain:
            totals[res.name] += 1
            counter = counters[res.name]
            ent = st.get_entity(res.entity_id)
            key = entity_key(ent)
            counter.counts[key] += 1
    for resname, res_count in totals.items():
        counter = counters[resname]
        counter.total += res_count
        counter.files += 1
        score = score_mult * res_count
        if score > counter.example_score:
            counter.example = st.name
            counter.example_score = score


def main():
    counters = defaultdict(ResidueCounter)
    total_files = 0
    # stage 1: reading PDB data
    for arg in sys.argv[1:]:
        for path in sorted_search(arg):
            total_files += 1
            add_file_stats(path, counters)

    # stage 2a: add category from components.cif, count metal atoms
    ccd = gemmi.cif.read(CCD_PATH)
    for block in ccd:
        comp_id = block.find_value('_chem_comp.id')
        counter = counters[comp_id]
        counter.ccd_category = block.find_value('_chem_comp.type')
        symbols = block.find_values('_chem_comp_atom.type_symbol')
        counter.metal_count = sum(gemmi.Element(s).is_metal for s in symbols)

    # stage 2b: add group (category) from the Refmac monomer library
    monlist = gemmi.cif.read(MON_LIB_LIST)['comp_list']
    for cc in monlist.find('_chem_comp.', ['id', 'group']):
        counter = counters[cc[0]]
        counter.ml_group = cc[1]

    # stage 3: output
    print('{\n"file_count": %d,\n"data": [' % total_files, end='')
    sep = ''
    for key in sorted(counters.keys(), key=lambda k: -counters[k].files):
        counter = counters[key]
        ccd_cat = counter.nice_category()
        ml_cat = counter.ml_group.lower().strip('"')
        d = counter.counts
        total = sum(d.values())
        assert total == counter.total
        if total == 0:
            continue
        print(sep)
        print(f'''\
["{key}",{counter.metal_count},"{ccd_cat}","{ml_cat}",\
{counter.files},{total},{d['nonpoly']},{d['branched']},\
{d['lpept']},{d['dpept']},{d['dna']},{d['rna']},{d['dnarna']},{d['other']},\
"{counter.example}"]''', end='')
        sep = ','
    print('\n]\n}')


if __name__ == '__main__':
    main()
