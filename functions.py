#!/usr/bin/python
# Written in Python 3.7 in 2023 by A.L.O. Gaenssle
# KRAKEN DATA EXTRACTOR - FUNCTIONS

import os
import pandas as pd

##------------------------------------------------------
## GENERAL
##------------------------------------------------------

## Print header
def print_header():
	print("\n","-"*75,"\n","-"*75)
	print("\tTHE KRONA DATA EXTRACTOR\tby A.L.O. Gaenssle, 2023")
	print("", "-"*75,"\n")


## Ask user a yes/no question
def question_to_user(question):
	answer = input(f"\n{question}\n(y=yes, n=no)\n")
	while answer not in ("y", "n"):
		answer = input("\nPlease enter 'y' or 'n'!\n")
	if answer == "y":
		get = True
	else:
		get = False
	return(get)


## Create new folder
def create_folder(new_path):
	if not os.path.exists(new_path):
		os.makedirs(new_path)
		print("Created folder:", new_path)
	else:
		print("Files will be added to:", new_path)
	return(new_path)


## Get numer & name of all samples
## Return level & name of available taxonomy
def get_samples(header_list, split_on="Domain"):
	try:
		index = header_list.index(split_on)
		return(header_list[:index], header_list[index:], index)
	except:
		print("Error: Tag", split_on, "does not exist")
		return([], [], 0)

##------------------------------------------------------
## GET INPUT FILES
##------------------------------------------------------

## Determine file type and create file_list to import
def get_files(given_input):
	file_list = []
	while os.path.exists(given_input) == False:
		given_input = input("\nPlease enter an existing file or folder"
		"\n\nYour current directory is:\n%s\n" % os.path.split(os.path.abspath(__file__))[0])
	if os.path.isdir(given_input):
		folder = given_input
		file_type = "report"
		for file in os.listdir(folder):
			if file.endswith(".report"):
				file_list.append(file)
	elif os.path.isfile(given_input):
		folder = os.path.split(given_input)[0]
		file_type = given_input.rsplit(".",1)[1]
		file_list.append(os.path.split(given_input)[1])
	return(sorted(file_list), folder, file_type)


##------------------------------------------------------
## REPORT -> IMPORT & COMBINE
##------------------------------------------------------

## Import each report separately and save it as _Reads.txt
def get_report(input_file, folder, name):
	# import file
	with open(os.path.join(folder, input_file), 'r') as file:
		print("\nImport File:", input_file)
		data = file.read().splitlines()

	# Convert input into table
	table = []
	level = ["D", "P", "C", "O", "F", "G", "S", "S1"] 	# Based on kraken levels
	tree = [""] * 8 # same length as "level"
	summary = []
	classified = ["U", "R", "R1"]	# U=unclasified, R=classified, R1=cellular/other organisms
	previous = 0
	for line in data:
		line = line.split("\t")
		if line[3] in level:

			# Delete all tax names that are higher than the new one
			if level.index(line[3]) < previous:
				for delete in range(level.index(line[3])+1,len(tree)):
					tree[delete] = ""

			# Add new tax name to tree & table, update the previous counter
			tree[level.index(line[3])] = line[-1].strip()
			previous = level.index(line[3])
			table.append([line[1]] + tree)

		# Append classfied/unclassified to different table
		elif line[3] in classified:
			summary.append([line[1], line[3], line[-1]])

	# Convert both tables to pandas dataframes
	header = [name] + ["Domain", "Phylum", "Class", "Order", "Family", "Genus", "Species", "Subspecies"]
	df_data = pd.DataFrame(table,columns=header)
	df_summary = pd.DataFrame(summary, columns=[name] + ["Label", "Name"])
	return(df_data, df_summary)


## Merge dataframes of all samples together, one at a time
def merge_dataframes(dataframe, append, name, split_on):
	sample_list, level_list, index = get_samples(list(dataframe), split_on=split_on)
	dataframe = pd.merge(dataframe, append, on=level_list,  how="outer")
	dataframe = dataframe[sample_list + [name] + level_list]
	return(dataframe)


##------------------------------------------------------
## TAXONOMY
##------------------------------------------------------

## Count Taxonomy and save 3 files for each tax level (reads, reads_cutoff, species)
def count_taxonomy(input_file, output_folder, cutoff, create_excel):
	# read in _read files, get column groups and convert reads to int
	reads_df = pd.read_csv(input_file, sep="\t", index_col=False)
	sample_list, level_list, index = get_samples(list(reads_df))
	reads_df[sample_list] = reads_df[sample_list].astype("Int64")

	# Cycle through each tax level and group/condense by that level
	for level in range(len(level_list)):
		output_file = os.path.join(output_folder, os.path.split(input_file)[1].rsplit(".",1)[0] + "_" + level_list[level])
		reads = reads_df.groupby(level_list[:level+1], as_index=False)[sample_list].sum()
		species = reads_df.groupby(level_list[:level+1], as_index=False)[sample_list].count()

		# For all levels > "Domain" filter out all rows where none of the samples have reads > the _cutoff
		# Sum the filtered out rows as "Other" and add them to the original dataframe
		if level > 0:
			df = reads[(reads[sample_list] < cutoff).all(axis=1)]
			df = df.groupby(level_list[:level], as_index=False)[sample_list].sum()
			df.insert(loc=level-1, column=level_list[level], value=["Other"]*len(df))
			reads_filtered = pd.concat([reads[(reads[sample_list] >= cutoff).any(axis=1)], df])

			# Save new filered dataframes as csv or append them to an excel (if wanted)
			reads_filtered.to_csv(output_file + "_reads_cutoff" + str(cutoff) + ".txt", sep="\t", index=False)
			if create_excel:
				create_excel_file(reads_filtered, level_list[level], level-1, input_file.rsplit(".",1)[0] + "_cutoff" + str(cutoff) + ".xlsx")

		# Save reads and specious counts as csv or append them to an excel (if wanted)
		reads.to_csv(output_file + "_reads.txt", sep="\t", index=False)
		species.to_csv(output_file + "_species.txt", sep="\t")
		if create_excel:
			create_excel_file(reads, level_list[level], level, input_file.rsplit(".",1)[0] + ".xlsx")
			create_excel_file(species, level_list[level], level, input_file.rsplit(".",1)[0] + "_species.xlsx")
		print("Counted", level_list[level], "from", input_file)


## Create/Append excel file with one dataframe/sheet
def create_excel_file(data, name, index, output_file, mode="a"):
	if index == 0:
		mode = "w"
		print("Create excel file:", output_file)
	with pd.ExcelWriter(output_file, mode=mode, engine="openpyxl") as writer:
		data.to_excel(writer, sheet_name=name, index=False)
