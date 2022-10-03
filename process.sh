###################################################################
# Expects to get a list of multi_test.py log files as arguments
# and creates a merged table with all results.
# 
# First lines in output are all the reference sets used in the analyses.
# Typically, this will be one line if all analyses used the same set.
#
# Then, there is the title line with column ids:
# target   - id of target sample
# feasible - feasible (TRUE/FALSE)
# list of source pops for ancestry proportions
# prob     - tail probability (P-val)
# nested-p - nested P-val for nested models
# valid	   - TRUE/FALSE. True if feasible and if prob>= 0.05
#
# After this all results are printed in a tab-separated table.
# Each line is a separate qpAdm model.
#
######################################################################

logfiles=$*
grep -h "References" $logfiles | uniq
grep -h "target" $logfiles | \
	tr " |" "\t" | tr -s "\t" | uniq | \
	sed -r 's/^[[:space:]]*//' | sed -r 's/[[:space:]]*$/\tvalid/' | cut -f1,3,6-
grep -h "|" $logfiles | grep -v "target" | \
	grep [[:alpha:]] | tr " |" "\t" | tr -s "\t" | \
	sed -r 's/^[[:space:]]*//' | sed -r 's/[[:space:]]*$//' |\
	cut -f1,3,6- | sed 's/^Phoenician_//' |\
	awk -v OFS="\t" \
	'{ \
	   i=NF-1; \
	   if($2=="True" && $i>=0.05) { valid="True"} else {valid="False"}; \
	   print $0,valid; \
	}' 
