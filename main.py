#!/usr/bin/python
# Written in Python 3.7 in 2023 by A.L.O. Gaenssle
# KRONA DATA EXTRACTOR - MAIN SCRIPT

##------------------------------------------------------
## IMPORT MODULES
##------------------------------------------------------
import sys
import os
import pandas as pd

# Own modules
import functions


##------------------------------------------------------
## MAIN SCRIPT
##------------------------------------------------------
cutoff = 2000 # Cufoff all UTFs below this number of reads (default = 20000)

functions.print_header()


try:
	file_list, folder, file_type = functions.get_files(sys.argv[1])
except IndexError:
	file_list, folder, file_type = functions.get_files("")
get = True # Default for count taxonomy


## Input and extract kraken.report files, export into table(s)
if file_type == "report":
	for input_file in file_list:
		name = input_file.rsplit(".",1)[0]
		output_file = folder + input_file.rsplit(".",1)[0] + "_reads.txt"
		if file_list.index(input_file) == 0:
			dataframe, classified = functions.get_report(input_file, folder, name)
		else:
			append, append_classified = functions.get_report(input_file, folder, name)
			dataframe = functions.merge_dataframes(dataframe, append, name, split_on="Domain")
			classified = functions.merge_dataframes(classified, append_classified, name, split_on="Label")
	if len(file_list) > 1:
		output_file = folder + "KrakenReport_combined_reads.txt"
		file_list = ["KrakenReport_combined_reads.txt"]
		file_type = "combined"
	dataframe.to_csv(output_file, sep="\t", index=False)
	classified.to_csv(output_file.rsplit("_",1)[0] + "_classified.txt", sep="\t", index=False)
	print("Data saved as:", output_file)
	get = functions.get_taxonomy()


## Count Taxonomy
if file_type == "txt" or get:
	output_folder = functions.create_folder(folder +"Results/")
	for input_file in file_list:
		if file_type == "report":
			input_file = input_file.rsplit(".",1)[0] + "_reads.txt"
		print(input_file)
		functions.count_taxonomy(folder + input_file, output_folder, cutoff)

print("\n","-"*75,"\n End of program\n","-"*75,"\n","-"*75)
