# DataExtractor for KRAKEN2 files
created 2023 by gaenssle
written in python 3.8

for questions, write to algaenssle@gmx.com

Kraken2 reports https://github.com/DerrickWood/kraken2) list all taxonomic classification found in a sample.

This program here
- extracts the data stored in kraken.report files (e.g. for creating tables)
- sums the reads and counts the occurence of species in each Domain, Phylum, Class, Order, Family, Genus and Species
- it creates files with and without a cutoff (e.g. 20,000 reads)

Run the script:
- The program is started over the terminal by typing:
python3 Main.py [File/Folder]
where [File] is the input file or folder you want to use

Accepted input files:
- kraken.report (to extract them to a spreadsheet .txt file)
- a folder (to extract all .report files in it and combined them)
- kraken_reads.txt (extracted files, to count taxonomy)
The program will automatically determine which file type it is and for .report files it will ask if you want to conduct the counting of the taxonomy as well
