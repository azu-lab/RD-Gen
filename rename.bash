#!/bin/bash

for ((i=0; i<50; i++));
do
    n=$(( $i + 450 ))
    mv ./DAGs/dag_${i}.dot /mnt/c/Users/atsushi/Documents/Study/Code/LET_env/LET-P_sim/DAGs/dag_${n}.dot
done
