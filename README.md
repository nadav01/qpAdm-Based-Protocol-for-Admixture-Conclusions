# qpAdm-Based-Protocol-for-Admixture-Conclusions

In order to use the protocol, please follow the instructions below.
In order to run qpAdm with specific target, sources and references populations, you need to edit the file configuration.sh with your target, sources and references populations, relevant file paths and chosen output directory and then upload it to the BioIDC server.

Connect to the BioIDC server, and run the command
```chmod +x ./configuration.sh```
and after it the command ```configuration.sh```
in order to run the script.  
A new directory (with your chosen output directory name) is created within the server, and after a couple of minutes (3-4 minutes in average) the run should finish. Within the output directory you can see .out files.  
You can find an example of configuration.sh file in the example_data directory (configuration-example.sh)  
Run the command  ```./process.sh ./v2/job-1.out ./v2/job-2.out ./v2/job-3.out ./v2/job-4.out … /v2/job-n.out > output.tsv```
(Complete the command with respect to all of the .out you have).

You can combine and automate the two steps above if you edit run-configuration.sh and run it (instead of configuration.sh) 


Now, the output of the qpAdm run is the output.tsv file.  
The protocol expects .tsv files (outputs of qpAdm runs like described above) in that manner:  
A file named MAIN_RUN.tsv which includes the full set of sources, as sources.  
A file named VALIDATION_[source_name].tsv for every source population, which in this run the population source_name is in the reference set (replace the [source_name] in the filename with the specific source population’s name).

Place the file protocol.py in the same directory where the .tsv files are located and run it using a command of this form:  
```python protocol.py MAIN_RUN.tsv,VALIDATION_source1.tsv,...,VALIDATION_sourceN.tsv Target1,...,TargetK source1,...,sourceN reference1,...,referenceJ t1 t2```

In the above example, we have K target populations, N source populations and J reference populations. t1 is the tail probability threshold for a feasible model being marked as valid, and t2 is the p-value threshold used for marking a model as compact (if for every population that does not participate in the model its p-value > t2 and for every population that does participate in the model, its p-value < t2).  
Please note that the lists of filenames, target populations, source populations and reference populations are all comma separated without spaces.

A running command for example would be:  
```python protocol.py MAIN_RUN.tsv,VALIDATION_Anatolia_N.tsv,VALIDATION_Armenia_ChL.tsv,VALIDATION_Megiddo_MLBA_original.tsv,VALIDATION_Steppe_MLBA.tsv Birgi_183,Birgi_176,Birgi_184_1,Birgi_9,Birgi_14,SelMan_T_7,Birgi_T_14,Birgi_5 Anatolia_N,Armenia_ChL,Steppe_MLBA,Megiddo_MLBA_original ElMiron,Mota,Ust_Ishim,Kostenki14,GoyetQ116-1,Vestonice16,MA1,Villabruna 0.05 0.05```

You can find the protocol outputs in the same directory that the protocol.py that you ran is located.

After running the commands above and obtaining a protocol summary file, you can use the contribution_space.py script in order to create the contribution vectors using PCA and project the on a 3D space, using a command in the form:  
```python contribution_space.py [PROTOCOL_SUMMARY_CSV] [LIST_OF_SOURCES]```
The [PROTOCOL_SUMMARY_CSV] is the path to the protocol summary csv file (the protocol outputs a file named Protocol_Summary.csv). The [LIST_OF_SOURCES] is the list of source populations in this summary file, comma separated.  
A command for example:  
```python contribution_space.py Protocol_Summary.csv anatolia_n,armenia_chl,steppe_mlba,tunisia_n,meggido_mlba_original```

You can find the outputs in the same directory that the contribution_space.py that you ran is located.
