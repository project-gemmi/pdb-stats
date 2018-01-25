
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

* entries deposited since 2010 (aribitrary cut-off),
* obtained using X-ray crystallography,
* in case of group depositions (PDB has now only a dozen of such groups)
  we take one entry from each group.

The web app itself is contained in a single file (index.html).
It depends on three external libraries: dc.js, d3.js and crossfilter.

Here is an interactive demo (each plot can be used as a filter):

https://project-gemmi.github.io/pdb-stats/

### Synchrotron work patterns

`./calendar.py >calendar.json` writes the data used in calendar.html:

https://project-gemmi.github.io/pdb-stats/calendar.html

[1]: https://project-gemmi.github.io/
