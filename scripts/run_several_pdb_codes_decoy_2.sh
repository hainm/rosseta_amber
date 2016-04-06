#!/bin/sh

# seq="1gou 1h4a"
seq=`cat ../decoys.set2.init/pdblist.txt`

decoyset=2

for code in $seq; do
    python ConvertToPDBandSubmitMinimizationJobs.py -n $code -d $decoyset -m `pwd`/min/min.in -p 30
    python ConvertToPDBandSubmitMinimizationJobs.py -n $code -d $decoyset -m `pwd`/min/min_norestraint.in -p 30
done
