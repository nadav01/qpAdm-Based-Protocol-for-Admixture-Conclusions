#!/bin/bash

#######################################################
#                SETTINGS AND VARIABLES               #
#######################################################

# relevant file paths
dataset=
ind_file=
# a new directory will be created for the output
outDir=$3
local_dataset=$outDir/data
# python-stype lists for source and refernece ['p_1', 'p_2', ...]
references=$2
sources=$1
# bash-style list for all targets, seperated with \
targets_all="\
		"
targetsPerJob=2
process_string=""


#######################################################
#                  COPY DATA FILES                    #
#######################################################

# copy data files
mkdir -p $outDir
ln -s  $dataset.snp  $local_dataset.snp
ln -s  $dataset.geno $local_dataset.geno
ln -rs $ind_file     $local_dataset.ind

#######################################################
#             MAKE CHANGES TO IND FILE                #
#######################################################

# NO CHANGES HERE

#######################################################
#              CREATE DOCUMENTATION                   #
#######################################################
echo "     dataset = $dataset"    >> $outDir/README
echo "  references = $references" > $outDir/README
echo "     sources = $sources"    >> $outDir/README
echo " all_targets = $targets_all">> $outDir/README
echo                              >> $outDir/README
#######################################################
#                    SET UP JOBS                      #
#######################################################
target_start=1
num_targets=`echo $targets_all | tr -s " " "\n" | wc -l`
jobid=1
while [ $target_start -le $num_targets ]
do
	# figure out python-style list for subset of targets
	((target_end=target_start+targetsPerJob-1))
	targets='['`echo $targets_all | tr -s " " "\n" | head -n$target_end | tail -n+$target_start | \
	           sed -r "s/.*/'&',/" | tr "\n"  " " | sed -r 's/, *$//'`']'

	# create custom multi_test.py python script
	bash ./create_multi_test.sh \
		$outDir/multi_test_$jobid.py \
		$local_dataset               \
		"$targets"                   \
		"$references"                \
		"$sources"                   \
		False

        echo "- Running	job $jobid with targets = $targets" >> $outDir/README
	nohup python3 $outDir/multi_test_$jobid.py &> $outDir/job-$jobid.out &
	((target_start=target_end+1))
	((jobid++))
	process_string+=" ./"
	process_string+=$outDir/job-$jobid.out
done
process_string+=" > $3.tsv"

sleep 300 # wait for the jobs to finish
bash ./process.sh \
	$process_string