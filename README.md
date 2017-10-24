
This project is an example how to use `gemmi-grep`.

In our final dataset we include PDB entries:

* deposited since 2010,
* only for the X-ray method
* and in case of group depositions (PDB has now only a dozen of such groups)
  we take one entry from each group.

# Updating

* update (rsync) local copy of the PDB archive in mmCIF format
* `./extract.sh` runs `gemmi-grep` to extract needed fields (and a few more)
  from all the mmCIF files. The output goes to a file `grep.out`.
  Reading all the files (34GB of compressed files) takes less than 30min.
* `./process.py >data.json` makes a concise dataset for our web app
