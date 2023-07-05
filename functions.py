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
	level = ["D", "P", "C", "O", "F", "G", "S"] 	# Based on kraken levels
	read_index = 2 	# column of reads attributed only to this level (not any subsequent ones)
	sum_read_index = 1	# column of sum of reads of all child levels, including itself
	tree = ["-"] * 7 # same length as "level"
	index_list = [0] * 7
	summary = []
	classified = ["U", "R", "R1", "R2"]	# U=unclasified, R=classified, R1=cellular/other organisms, R2=other sequences (used as STOP)
	previous = 0
	for line in data:
		line = line.split("\t")
		line[3] = line[3].replace("K", "D1") # Viruses & Eukaryota have kingdoms level beneath the domain level

		# Append classfied/unclassified to summary table
		if line[3] in classified:
			if line[3] != "R2":
				summary.append([int(line[sum_read_index]), line[3], line[-1]])
			else:
				break	# To exclude the rare non-cellular organisms

		# Very rarely other taxonomic level occur, their reads are added to the R1 level
		elif line[3][0] not in level:
			if int(line[read_index]) > 0:
				summary[-1][0] += int(line[read_index])
			print("Not in Level" ,line[3], line[read_index])

		else:
			# Native level dirstibution is used to make the phylogeny tree
			if len(line[3]) == 1:
				# Delete all tax names that are higher than the new one
				if level.index(line[3]) < previous:
					for delete in range(level.index(line[3])+1,len(tree)):
						tree[delete] = "-"
						index_list[delete] = 0

				# Add new tax name to tree & table
				# Update the previous & index counter
				tree[level.index(line[3])] = line[-1].strip()
				previous = level.index(line[3])
				table.append([int(line[read_index])] + tree)
				index_list[level.index(line[3])] = len(table) - 1

			# Add reads of all sub-level to the parent level using the index counter
			else:
				if int(line[read_index]) > 0:
					add_index = index_list[level.index(line[3][0])]
					table[add_index][0] += int(line[read_index])

	# Convert both tables to pandas dataframes
	header = [name] + ["Domain", "Phylum", "Class", "Order", "Family", "Genus", "Species"]
	df_data = pd.DataFrame(table,columns=header)
	df_data = df_data[(df_data[name] > 0)]	# delete rows with 0 reads
	df_summary = pd.DataFrame(summary, columns=[name] + ["Label", "Name"])
	return(df_data, df_summary)


## Merge dataframes of all samples together, one at a time
def merge_dataframes(dataframe, append, name, split_on):
	sample_list, level_list, index = get_samples(list(dataframe), split_on=split_on)
	dataframe = pd.merge(dataframe, append, on=level_list,  how="outer")
	dataframe = dataframe[sample_list + [name] + level_list]
	return(dataframe)

## Calculate percentages for reads and add 1/sample
def add_percentages(dataframe, sample_list, index):
	percentage_list = []
	for sample in sample_list:
		sum = dataframe[sample].sum()
		dataframe.insert(loc=index, column="%-" + sample, value=dataframe[sample] / sum * 100)
		percentage_list.append("%-" + sample)
		index += 1
	return(dataframe, percentage_list)

##------------------------------------------------------
## TAXONOMY
##------------------------------------------------------

## Count Taxonomy and save 3 files for each tax level (reads, reads_cutoff, species)
def count_taxonomy(input_file, output_folder, cutoff, float_format, create_excel):
	# Read in _read.txt files, get column groups
	# Convert reads to int and add a percentage column for each
	reads_df = pd.read_csv(input_file, sep="\t", index_col=False)
	sample_list, level_list, index = get_samples(list(reads_df))
	reads_df[sample_list] = reads_df[sample_list].astype("Int64")
	reads_df, percentage_list = add_percentages(reads_df, sample_list, index)

	# Cycle through each tax level and group/condense by that level
	for level in range(len(level_list)):
		output_file = os.path.join(output_folder, os.path.split(input_file)[1].rsplit(".",1)[0] + "_" + level_list[level])
		reads = reads_df.groupby(level_list[:level+1], as_index=False)[sample_list + percentage_list].sum()
		species = reads_df[(reads_df[level_list[-1]] != "-")]	# delete all rows that aren't species
		species = species.groupby(level_list[:level+1], as_index=False)[sample_list].count()

		# For all levels > "Domain" filter out all rows where none of the samples have reads > the _cutoff
		# Sum the filtered out rows as "Other" and add them to the original dataframe
		if level > 0:
			df = reads[(reads[sample_list] < cutoff).all(axis=1)]
			df = df.groupby(level_list[:level], as_index=False)[sample_list + percentage_list].sum()
			df.insert(loc=level-1, column=level_list[level], value=["Other"]*len(df))
			reads_filtered = pd.concat([reads[(reads[sample_list] >= cutoff).any(axis=1)], df])

			# Save new filered dataframes as csv or append them to an excel (if wanted)
			reads_filtered.to_csv(output_file + "_reads_cutoff" + str(cutoff) + ".txt", sep="\t", index=False, float_format=float_format)
			if create_excel:
				create_excel_file(reads_filtered, level_list[level], level-1, input_file.rsplit(".",1)[0] + "_cutoff" + str(cutoff) + ".xlsx")

		# Save reads and specious counts as csv or append them to an excel (if wanted)
		reads.to_csv(output_file + "_reads.txt", sep="\t", index=False, float_format=float_format)
		species.to_csv(output_file + "_species.txt", sep="\t", index=False, float_format=float_format)
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
