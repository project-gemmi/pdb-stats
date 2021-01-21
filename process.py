#!/usr/bin/env python3
# Copyright 2017 Global Phasing Ltd.
# Licence: Mozilla Public License 2.0

import datetime
import itertools
import csv
import json
import gemmi
import sys

INPUT = 'grep.out'
FROM_YEAR = 2008

def read_data():
    with open(INPUT) as f_in:
        reader = csv.reader(f_in, delimiter=';', escapechar='\\',
                            quoting=csv.QUOTE_NONE)
        for _, v in itertools.groupby(reader, key=lambda x: x[0]):
            items = list(v)
            for item in items:
                assert len(item) == 21, item
            yield items

def read_and_filter_data():
    groups = {}
    for items in read_data():
        method = items[0][8]
        year = int(items[0][4][:4])
        if (method == 'X-RAY DIFFRACTION' and year >= FROM_YEAR and
                items[0][9] != 'NUCLEAR REACTOR'):
            group = items[0][18]
            if group:
                if group in groups:
                    groups[group][0] += 1
                    continue
                groups[group] = [1, items[0][4]]
            yield items
    #for gid, (count, date) in sorted(groups.items()):
    #    print(gid, date, count)

def parse_date(txt):
    if not txt:
        return None
    try:
        return datetime.date(*[int(x) for x in txt.split('-')])
    except (ValueError, TypeError):
        return None

SYNCHROTRONS = {
    'APS':                     'a APS (US, IL)',
    'ESRF':                    'e ESRF (FR)',
    'Diamond':                 'd Diamond (UK)',
    'DIAMOND':                 'd Diamond (UK)',
    'DIAMOND LIGHT SOURCE':    'd Diamond (UK)',
    'SLS':                     's SLS (CH)',
    'ALS':                     'A ALS (US, CA)',
    'SSRL':                    'S SSRL (US, CA)',
    'NSLS':                    'n NSLS (US, NY)',
    'SSRF':                    'h Shanghai SRF (CN)',
    'Photon Factory':          'p Photon Factory (JP)',
    'SPring-8':                '8 SPring-8 (JP)',
    'BESSY':                   'b BESSY (DE)',
    'Australian Synchrotron':  'u Australian S. (AU)',
    'AUSTRALIAN SYNCHROTRON':  'u Australian S. (AU)',
    'SOLEIL':                  'f SOLEIL (FR)',
    'PAL/PLS':                 'k PAL/PLS (KR)',
    'CLSI':                    'c CLSI (CA)',
    'NSRRC':                   't NSRRC (TW)',
    'CHESS':                   'C CHESS (US, NY)',
    'MAX_II':                  'm MAX (SE)',
    'EMBL/DESY, Hamburg':      'D DESY (DE)',
    'EMBL/DESY, HAMBURG':      'D DESY (DE)',
    'LNLS':                    'L LNLS (BR)',
    'LNLS SIRUS':              'L LNLS (BR)',
    'PETRA III EMBL c/o DESY': 'D DESY (DE)',
    'PETRA II STORAGE RING':   'D DESY (DE)',
    'ALBA':                    'Z ALBA (ES)',
    'ELETTRA':                 'E Elettra (IT)',
    'BSRF':                    'B Beijing SRF (CN)',
    'SRS':                     'U SRS (UK)',
    'PETRA III, EMBL c/o DESY':'D DESY (DE)',
    'PETRA III, EMBL C/O DESY':'D DESY (DE)',
    'PETRA III, DESY':         'D DESY (DE)',
    'MAX II':                  'm MAX (SE)',
    'MAX IV':                  'm MAX (SE)',
    'RRCAT INDUS-2':           'I Indus (IN)',
    'KURCHATOV SNC':           'K KSRS (RU, Moscow)',
    'MPG/DESY, HAMBURG':       'D DESY (DE)',
    'SACLA':                   '8 SPring-8 (JP)',
    'CAMD':                    'z CAMD (US, LA)',
    'NFPSS':                   'h Shanghai SRF (CN)',
    'LURE':                    'f SOLEIL (FR)',
    'AichiSR':                 'i AichiSR (JP)',
    'SAGA-LS':                 'g SAGA-LS (JP)',
    'NSLS-II':                 'n NSLS (US, NY)',
    'RRCAT':                   'I Indus (IN)',
    'SLRI':                    'T Siam Photon P. (TH)',
    'PETRA III':               'D DESY (DE)',
    'PETRA II, DESY':          'D DESY (DE)',
    'DESY':                    'D DESY (DE)',  # this one is for coldates.py

    # these are actually XFEL
    'LCLS':                    'F SLAC (US, CA)',
    'SLAC':                    'F SLAC (US, CA)',
    'SLAC LCLS':               'F SLAC (US, CA)',

    # ?
    'SYNCHROTRON':             '?',
}

DETECTORS = {
    'CCD': 1,
    'PIXEL': 2,
    'CMOS': 2, # the same?
    'IMAGE PLATE': 3,
}

SOLUTIONS = ['KNOWN', 'MR', 'SAD', 'MAD', 'MIR/SIR', 'SIRAS', 'MIRAS', '-']

def structure_solution(s):
    if not s or s == 'OTHER':
        return '-'
    s = s.lower()
    if s.startswith('molecular') or s.startswith('mr') or s == 'phaser' \
            or s == 'molrep':
        return 'MR'
    if s.startswith('ab initio'):
        #return 'a AB INITIO'  # too few to show
        return '-'
    if s.startswith('sad') or s.startswith('s-sad') or s.startswith('ssad'):
        return 'SAD'
    if s == 'mad':
        return 'MAD'
    if s.startswith('siras'):
        return 'SIRAS'
    if s == 'miras':
        return 'MIRAS'
    if s == 'mir' or s == 'sir' or s == 'isomorphous replacement':
        return 'MIR/SIR'
    if s.startswith('fourier') or s.startswith('rigid') or \
            s.startswith('difference') or 'refinement' in s or ' apo ' in s:
        return 'KNOWN'
    return '-'

def concise_date(s):
    if s:
        assert s[0:4].isdigit() and s[4] == '-' and s[7] == '-'
        short_date = s[2:4] + s[5:7] + s[8:10]
        assert short_date.isdigit()
        return short_date
    else:
        return ' ' * 6

def encode_month(d):
    return 12 * (d.year - 1989) + d.month - 1
def encode_date(d):
    return 32 * encode_month(d) + d.day

def main():
    oldest_date = datetime.date(1989, 1, 1)
    data = []
    for entry in read_and_filter_data():
        pipes = {'xia2', 'AutoPROC'}
        data_softs = {p[2] for p in entry if p[1] in
                              ['data processing', 'data reduction']} - pipes
        scal_softs = {p[2] for p in entry if p[1] == 'data scaling'} - pipes
        refi_softs = {p[2] for p in entry if p[1] == 'refinement'}

        if not data_softs:
            data_soft = '-'
        elif data_softs <= {'XDS', 'autoXDS', 'XDS-package'}:
            data_soft = 'XDS'
        elif data_softs <= {'DENZO', 'HKL-2000', 'HKL-3000', 'HKL'}:
            data_soft = 'HKL'
        elif data_softs <= {'MOSFLM', 'iMOSFLM'}:
            data_soft = 'MOSFLM'
        elif data_softs <= {'d*TREK', 'CrystalClear'}:
            data_soft = 'd*TREK'
        elif data_softs <= {'DIALS'}:
            data_soft = 'DIALS'
        else:
            data_soft = 'Other'
            #print(data_softs)

        if not scal_softs:
            scal_soft = '-'
        elif scal_softs in [{'Aimless'}, {'CCP4', 'Aimless'}]:
            scal_soft = 'Aimless'
        elif scal_softs in [{'SCALA'}]:
            scal_soft = 'SCALA'
        elif scal_softs <= {'HKL-2000', 'SCALEPACK', 'HKL-3000', 'HKL', 'hkl'}:
            scal_soft = 'HKL'
        elif scal_softs <= {'XSCALE', 'XDS'}:
            scal_soft = 'XSCALE'
        elif scal_softs <= {'d*TREK', 'CrystalClear'}:
            scal_soft = 'd*TREK'
        else:
            scal_soft = 'Other'
            #print(scal_softs)

        if not refi_softs:
            refi = '-'
        elif refi_softs <= {'PHENIX', 'phenix.refine'}:
            refi = 'P'
        elif refi_softs <= {'REFMAC', 'REFMAC5', 'CCP4', 'Coot'}:
            refi = 'R'
        elif refi_softs <= {'BUSTER', 'TNT', 'BUSTER-TNT'}:
            refi = 'B'
        elif refi_softs <= {'CNX', 'CNS'}:
            refi = 'C'
        else:
            refi = '-'

        first = entry[0]

        source = first[9]
        synchrotron = first[11]

        source = first[9]
        if source == 'SYNCHROTRON':
            facility = SYNCHROTRONS[synchrotron] if synchrotron else '?'
        elif source in ('SEALED TUBE', 'ROTATING ANODE'):
            if synchrotron:  # then we assume it's actually a synchrotron
                facility = SYNCHROTRONS[synchrotron]
            else:
                facility = 'H'
        elif source == 'FREE ELECTRON LASER':
            facility = 'F'
        else:
            facility = '-'

        detector = DETECTORS.get(first[10], 0)

        hm = first[5]
        sg = gemmi.find_spacegroup_by_name(hm) if hm else None
        if not sg:
            print("Unknown H-M SG '%s' in %s" % (hm, first[0]), file=sys.stderr)
            continue

        res = round(float(first[6]), 1) if first[6] else 0

        coll_date = parse_date(first[19])
        depos_date = parse_date(first[4])
        assert depos_date
        if coll_date and coll_date < depos_date and coll_date > oldest_date:
            encoded_coll_date = encode_month(coll_date)
        else:
            encoded_coll_date = 0
        release_date = parse_date(first[-1])

        struct_sol = SOLUTIONS.index(structure_solution(first[12]))
        software = data_soft[0] + scal_soft[0] + refi

        data.append([
            first[0],                  # 0
            facility[0],               # 1
            detector,                  # 2
            software,                  # 3
            sg.number,                 # 4
            res,                       # 5
            struct_sol,                # 6
            encoded_coll_date,         # 7
            encode_date(depos_date),   # 8
            encode_date(release_date), # 9
        ])

    data.sort(key=lambda x: (x[-1], x[0]))
    first = True
    print('[')
    for d in data:
        if not first:
            print(',')
        first = False
        print(json.dumps(d, separators=(',', ':')), end='')
    print('\n]')


if __name__ == '__main__':
    main()
