
This is an example how to use `gemmi-grep` (one of the utilities
provided by the [project gemmi][1]) to quickly extract data from mmCIF files.

* We have a local copy of the PDB archive in mmCIF format
  (and we rsync it once a week).

* We use `gemmi-grep` (see `extract.sh`) to extract all the needed metadata
  (we actually extract more data then we'll need in the next steps).
  Reading all the archive (34GB of compressed files) takes 20-30min.
  The output is redirected to a file (`grep.out`) that can be later read
  and analysed in seconds.

* `./process.py >data.json` makes a concise JSON files that is used by our
  web app.  This dataset includes only:

    * entires deposited since 2010 (aribitrary cut-off),
    * obtained using X-ray crystallography,
    * in case of group depositions (PDB has now only a dozen of such groups)
      we take one entry from each group.

The web app itself is contained in a single file (index.html).
It depends on three external libraries: dc.js, d3.js and crossfilter.

Here is an interactive demo (each plot can be used as a filter):

https://project-gemmi.github.io/pdb-stats/


[1]: https://project-gemmi.github.io/
