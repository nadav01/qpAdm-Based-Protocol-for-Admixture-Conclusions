#!/bin/bash

#######################################################
#                SETTINGS AND VARIABLES               #
#######################################################

dataset=/home/salmanay/pheonicians/datasets/Haralds_V49.2_additions_7_9_2021/anc_only.v49.2
ind_file=/home/salmanay/pheonicians/datasets/Haralds_V49.2_additions_7_9_2021/ind_files/anc_only.v49.2_updated_matched_names_with_id.ind
outDir=v2
local_dataset=$outDir/data
# python-stype lists for source and refernece
references="['ElMiron', 'Greece_N', 'Levant_N', 'Natufian', 'Kostenki14', 'MA1', 'Ust_Ishim', 'Vestonice16', 'Villabruna']"
sources="['Anatolia_N', 'Armenia_ChL', 'Steppe_MLBA', 'Tunisia_N', 'Megiddo_MLBA_original']"
#bash-style list for all targets
targets_all="\
Phoenician_Birge_183 \
Phoenician_Birgi_176 \
Phoenician_Birgi_184_1 \
Phoenician_Birgi_9 \
Phoenician_Birgi_14 \
Phoenician_SelMan_T_7 \
Phoenician_Birgi_T_14 \
Phoenician_Birgi_5 \
Phoenician_Tribunale_T_138 \
Phoenician_SelMan_T_8 \
Phoenician_SelMan_T_12 \
Phoenician_Tribunale_T_128 \
Phoenician_Mozia_1 \
Phoenician_NecMon_162 \
Phoenician_Lilibeo_13 \
Phoenician_Birgi_16 \
Phoenician_Lilibeo_12 \
Phoenician_NecMon_63 \
Phoenician_NecMon_142 \
Phoenician_Birgi_3 \
Phoenician_CasTuk_T_15_a \
Phoenician_Tribunale_T_113 \
Italy_Sicily_Punic_I22095 \
Italy_Sicily_Punic_I22236 \
Italy_Sicily_Punic_I22232 \
Italy_Sicily_Punic_I4798 \
Italy_Sicily_Punic_I4799 \
Italy_Sicily_Punic_I4800 \
Italy_Sicily_Punic_I7454 \
Italy_Sicily_Punic_oEuropean_I7762 \
Italy_Sicily_Punic_oEuropean_I8577 \
	"
targetsPerJob=2


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
done