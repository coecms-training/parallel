depend=on:1

BENCHMARK=benchmark_era5_t2_climatology.py

# Submit the jobs in sequence with -Wdepend so that the csv file writes don't have a race
for N in 4 8 16 32 48; do
jobid=$(qsub << EOF
#!/bin/bash
#PBS -N bench_$N
#PBS -l ncpus=$N
#PBS -l mem=$(( N * 4 ))gb
#PBS -l walltime=1:00:00
#PBS -l jobfs=100gb
#PBS -l wd
#PBS -l storage=gdata/hh5+gdata/w35+gdata/rt52
#PBS -W umask=0022
#PBS -W depend=$depend
#PBS -j oe

module use /g/data3/hh5/public/modules
module load conda/analysis3-21.04

set -eu

python $BENCHMARK
EOF
)
echo $N $jobid $depend
depend=beforeok:$jobid,on:1
done

qsub -l ncpus=1,mem=50mb,walltime=0:01:00 -W depend=beforeok:$jobid -j oe -N trigger << EOF
#!/bin/bash
true
EOF
