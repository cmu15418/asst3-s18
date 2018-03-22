#!/bin/bash
# This script lets you submit jobs for execution on the latedays cluster
# You should submit it using qsub:
#   'qsub latedays.sh'

# Upon completion, the output generated on stdout will show up in the
# file latedays.sh.oNNNNN where NNNNN is the job number.  The output
# generated on stderr will show up in the file latedays.sh.eNNNNN.

# Limit execution time to 20 minutes
#PBS -lwalltime=0:20:00
# Allocate all available CPUs on a single node
#PBS -l nodes=1:ppn=24


# Configure to place threads on successive processors
OMP_PLACES=cores
OMP_PROC_BIND=close

# Go to the directory from which you submitted your job
cd $PBS_O_WORKDIR

# Execute the performance evaluation program and store summary in benchmark-NNNN.out
# where NNNN is a random 4-digit number
./benchmark.py -f benchmark-XXXX.out


