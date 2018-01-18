#!/bin/sh

# This web page is part of an example how to use gemmi-grep.
# gemmi-grep is an part of the GEMMI library, funded by GPhL and CCP4.

PATH="$PATH":../gemmi/

gemmi-grep --delimiter=';' \
       _software.classification \
    -a _software.name \
    -a _pdbx_database_status.deposit_site \
    -a _pdbx_database_status.recvd_initial_deposition_date \
    -a _symmetry.space_group_name_H-M \
    -a _reflns.d_resolution_high \
    -a _reflns.pdbx_redundancy \
    -a _exptl.method \
    -a _diffrn_source.source \
    -a _diffrn_detector.detector \
    -a _diffrn_source.pdbx_synchrotron_site \
    -a _refine.pdbx_method_to_determine_struct \
    -a _refine.ls_number_reflns_all \
    -a _refine_hist.number_atoms_total \
    -a _refine_hist.number_atoms_solvent \
    -a _refine_hist.pdbx_number_atoms_protein \
    -a _refine_hist.pdbx_number_atoms_nucleic_acid \
    -a _pdbx_deposit_group.group_id \
    -a _diffrn_detector.pdbx_collection_date \
    -a _pdbx_audit_revision_history.revision_date \
    $PDB_DIR/structures/divided/mmCIF/  > grep.out

if [ "$1" = "--auto" ]; then
  ./process.py >data.json
  sed -i s"/\(Last update:\) ....-..-../\1 $(date -Idate)/" index.html
fi
