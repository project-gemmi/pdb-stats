#!/usr/bin/env python3

import sys
from process import read_data, parse_date, SYNCHROTRONS

# alternative names are also included, see process.py
OUTPUT_SYN = ['APS', 'Diamond', 'ESRF', 'SSRF', 'SLS',
              'ALS', 'SSRL', 'Australian Synchrotron', 'Photon Factory',
              'BESSY', 'SPring-8', 'PAL/PLS', 'CLSI', 'SOLEIL']
ALL_OUTPUT = OUTPUT_SYN + ['home']

OUTPUT_YEARS = [2013, 2014, 2015, 2016]

def days_in_year(year):
    if year % 4 == 0:
        return 366
    return 365

def print_data(data):
    print('{')
    after_dict = False
    for syn in ALL_OUTPUT:
        if after_dict:
            print(',')
        print(' "%s": {' % syn.translate(str.maketrans('','', ' /-')))
        after_list = False
        for year in OUTPUT_YEARS:
            counts = data[syn][year]
            if after_list:
                print(',')
            print('  "%d": [%s]' % (year, ','.join(map(str, counts))), end='')
            after_list = True
        print('\n }', end='')
        after_dict = True
    print('\n}')

def main():
    syn_symbols = {SYNCHROTRONS[s][0]: s for s in OUTPUT_SYN}
    data = {s: {y: [0]*days_in_year(y) for y in OUTPUT_YEARS}
            for s in ALL_OUTPUT}
    for items in read_data():
        syn = SYNCHROTRONS.get(items[0][11])
        name = None
        if items[0][8] == 'ELECTRON MICROSCOPY':
            # No stats for CryoEM. In most of entries _em_imaging.date is null.
            name = None
        elif syn:
            name = syn_symbols.get(syn[0])
        elif items[0][9] in ('SEALED TUBE', 'ROTATING ANODE'):
            name = 'home'
        if not name:
            continue
        coll = parse_date(items[0][19])
        if not coll or coll.year not in OUTPUT_YEARS:
            continue
        day = coll.timetuple().tm_yday
        data[name][coll.year][day-1] += 1
    # summary to stderr
    for syn in ALL_OUTPUT:
        totals = [sum(data[syn][year]) for year in OUTPUT_YEARS]
        print('%-10.10s %-17s total: %4d' % (syn, totals, sum(totals)),
              file=sys.stderr)
    # JSON to stdout
    print_data(data)

main()
