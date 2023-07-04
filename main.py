#!/usr/bin/python
# Written in Python 3.7 in 2023 by A.L.O. Gaenssle
# KRONA DATA EXTRACTOR - MAIN SCRIPT

##------------------------------------------------------
## IMPORT MODULES
##------------------------------------------------------
import sys
import os

# Own modules
import functions


##------------------------------------------------------
## MAIN SCRIPT
##------------------------------------------------------
cutoff = 20000 # Cufoff all UTFs below this number of reads (default = 20000)

functions.print_header()

## Check & get file input
try:
	file_list, folder, file_type = functions.get_files(sys.argv[1])
except IndexError:
	file_list, folder, file_type = functions.get_files("")
get_tax = True # Default for count taxonomy
create_excel = False # Default to not export the count files to an excel


## Input and extract kraken.report files, export into table(s)
if file_type == "report":
	for input_file in file_list:
		name = input_file.rsplit(".",1)[0]
		output_file = os.path.join(folder, input_file.rsplit(".",1)[0] + "_reads.txt")
		if file_list.index(input_file) == 0:
			dataframe, classified = functions.get_report(input_file, folder, name)

		# If > 1 .report files, merge them with the previous dataframe
		else:
			append, append_classified = functions.get_report(input_file, folder, name)
			dataframe = functions.merge_dataframes(dataframe, append, name, split_on="Domain")
			classified = functions.merge_dataframes(classified, append_classified, name, split_on="Label")

	# If > .report files: export them with a new file name
	if len(file_list) > 1:
		output_file = os.path.join(folder, "KrakenReport_combined_reads.txt")
		file_list = ["KrakenReport_combined_reads.txt"]
		file_type = "combined"

	# Export created dataframes to .txt files
	dataframe.to_csv(output_file, sep="\t", index=False)
	classified.to_csv(output_file.rsplit("_",1)[0] + "_classified.txt", sep="\t", index=False)
	print("Data saved as:", output_file)
	get_tax = functions.question_to_user("Do you want to count the taxonomy?")


## Count Taxonomy and save files in a newly created folder called "Results"
if file_type == "txt" or get_tax:
	create_excel = functions.question_to_user("Do you want the count files exported to excel?\n(Will take longer)")
	output_folder = functions.create_folder(os.path.join(folder, "Results"))
	for input_file in file_list:

		# If the input was originally a single .report file, find the just created file
		if file_type == "report":
			input_file = input_file.rsplit(".",1)[0] + "_reads.txt"
		functions.count_taxonomy(os.path.join(folder, input_file), output_folder, cutoff, create_excel)

print("\n","-"*75,"\n End of program\n","-"*75,"\n","-"*75)
