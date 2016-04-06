#!/bin/sh

# seq="1ez3 1fzy"
# seq="1a32 1acf"
# seq="1agy 1bk2 1bkr 1bm8 1cc8 1cei"
# 
# seq="1ctf 1elw 1enh 1ew4 1fna 1hz6"
seq=`cat ../decoys.set1.init/pdblist.txt`

decoyset=1

for code in $seq; do
    echo $code
    python ConvertToPDBandSubmitMinimizationJobs.py -n $code -d $decoyset -m `pwd`/min/min.in -p 30
    python ConvertToPDBandSubmitMinimizationJobs.py -n $code -d $decoyset -m `pwd`/min/min_norestraint.in -p 30
done
