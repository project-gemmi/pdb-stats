
These statistics serve as an example how to use `gemmi-grep`
 (one of the utilities provided by the [project gemmi][1])
 to quickly extract data from mmCIF files.

The data is extracted from a local copy of the PDB archive in mmCIF format
(we rsync it once a week).

We use `gemmi-grep` in the `extract.sh` script to extract all the needed
metadata (and some more).
Reading all the archive (34GB of compressed files) takes 20-30min.
The output is redirected to a file (`grep.out`) that is later used
to prepare JSON files used in our web pages.

### Filter-able statistics

`./process.py >data.json` makes a concise JSON file that includes only:

* entries deposited since 2008 (aribitrary cut-off),
* obtained using X-ray crystallography,
* in case of group depositions (PDB has now only a dozen of such groups)
  we take one entry from each group.

The web app itself is contained in a single file (index.html).
It depends on three external libraries: dc.js, d3.js and crossfilter.

Here is an interactive demo (each plot can be used as a filter):

https://project-gemmi.github.io/pdb-stats/

### Synchrotron work patterns

`./coldates.py >calendar.json` writes the data used in calendar.html:

https://project-gemmi.github.io/pdb-stats/calendar.html

### Residue statistics

    $ curl -O ftp://ftp.wwpdb.org/pub/pdb/data/monomers/components.cif.gz
    $ ./resistat.py $PDB_DIR/structures/divided/mmCIF > residues.json
    $ # update file_count and date in residues.html (take file_count from json)

https://project-gemmi.github.io/pdb-stats/residues.html

### Tag statistics

File entries.idx is used to sort entries from the most recent ones,
so that the example PDB ID in tooltip is the newest entry with given tag.

    $ curl -O https://files.wwpdb.org/pub/pdb/derived_data/index/entries.idx
    $ gemmi tags --full components.cif.gz > ccd-tags.tsv
    $ gemmi tags --full --entries-idx=entries.idx $PDB_DIR/structures/divided/mmCIF > mmcif-tags.tsv
    $ gemmi tags --full --entries-idx=entries.idx --sf $PDB_DIR/structures/divided/structure_factors > sf-tags.tsv
    $ sed -i s"/ on 20..-..-../ on $(date -Idate)/" tags.html

To get more recent PDB entries in tooltips use --entries-idx=/.../entries.idx
(together with --sf for sf-tags.tsv).

https://project-gemmi.github.io/pdb-stats/tags.html

Similarly, for COD:

    $ gemmi tags --full path/to/cod/cif/ > cod-cif-tags.tsv
    $ gemmi tags --full --glob='*.hkl' path/to/cod/hkl/ > cod-hkl-tags.tsv
    $ sed -i s"/ on 20..-..-../ on $(date -Idate)/" cod-tags.html

https://project-gemmi.github.io/pdb-stats/cod-tags.html

[1]: https://project-gemmi.github.io/
