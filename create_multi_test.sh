#!/bin/bash

# script for crating copy of multi_test.py with specific settings

outfile=$1      # complete path for multi_test.py output
dataset=$2      # path of data set (files witout extension)
targets=$3      # python-style list; need to wrap with " "
references=$4   # python-style list; need to wrap with " "
sources=$5      # python-style list; need to wrap with " "
move_src_to_ref=$6 # True or False - checking models with sources moved to the reference set

if [ "$move_src_to_ref" != "False" ]; then
   move_src_to_ref=True
fi

# get path for scripts dir
scriptDir=`echo $0 | sed -r 's|[^/]*$||'`

cat ${scriptDir}multi_test_template.py                                | \
	sed -r "s|REPLACE_WITH_DATASET_PATH|$dataset|"              | \
	sed -r "s/REPLACE_WITH_LIST_OF_TARGET_POPS/$targets/"       | \
	sed -r "s/REPLACE_WITH_LIST_OF_REFERENCE_POPS/$references/" | \
	sed -r "s/REPLACE_WITH_LIST_OF_SOURCE_POPS/$sources/"       | \
	sed -r "s/MOVE_SRC_TO_REF/$move_src_to_ref/"  >  $outfile


