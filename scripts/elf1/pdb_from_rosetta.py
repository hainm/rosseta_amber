#!/usr/bin/env python

# python pdbgen_from_rosetta.py 1a32,1enh

import os
import sys

PATH_TO_DECOYDISC = os.environ.get('PATH_TO_DECOYDISC', "/project1/dacase-001/haichit/rosseta_amber/DecoyDiscrimination/")
ROSETTA_BIN = os.environ.get('ROSETTA_BIN', PATH_TO_DECOYDISC + "/extract_pdbs.static.linuxgccrelease")
ROSETTA_DB = os.environ.get('ROSETTA_DB', PATH_TO_DECOYDISC + "/Rosetta_Database/")
AMBER_HOME = os.environ.get("AMBERHOME")

decoy_set = "decoys.set2.init"
input_pdbs = sys.argv[1].split(',')
file_ending = 'retag.nocartbump.out'

options = dict(ROSETTA_BIN=ROSETTA_BIN,
               ROSETTA_DB=ROSETTA_DB,
               PATH_TO_DECOYDISC=PATH_TO_DECOYDISC,
               decoy_set=decoy_set,
               file_ending=file_ending)

cwd = os.getcwd()

for input_pdb in input_pdbs:
    try:
        options['input_pdb'] = input_pdb
        os.mkdir(input_pdb)
        os.chdir(input_pdb)
        os.system("{ROSETTA_BIN} -database {ROSETTA_DB} -in:file:silent {PATH_TO_DECOYDISC}/{decoy_set}/{input_pdb}.{file_ending}".format(**options))
        os.chdir(cwd)
    except OSError:
        print("folder exists, skip {}".format(input_pdb))
