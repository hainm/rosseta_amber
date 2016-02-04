#!/bin/sh
#SBATCH -J amberrosseta
#SBATCH -o log/amberrosseta.%J.stdout
#SBATCH -e log/amberrosseta.%J.stderr
#SBATCH -p long
#SBATCH -N 4
#SBATCH -t 96:00:00

# require: mpi4py (conda install mpi4py)

cd /project1/dacase-001/haichit/rosseta_amber/

mpirun -n 1 python run_min.py -p prmtop -c *.rst7 -i min.in
