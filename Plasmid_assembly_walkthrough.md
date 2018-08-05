# AMR plasmid de-novo assembly 

## Basecalling using albacore

To basecall fastq files from fast5 files. `nohup` and `&` are optional when using server based albacore: 

```
nohup read_fast5_basecaller.py -i /path/to/plasmid/fast5/ -t 96 -s path/to/output/fastq/ -f FLO-MIN106 -k SQK-LSK108 -o fastq -r &
```

` -i = [INTPUT FILE LOCATION]` : location of fast5 pass folder  
` -t = [NUMBER]` : number of threads to run on this job. Check your comp (probably 6-8)  
` -s = [OUTPUT FILE LOCATION]` : where to save fastq files to  
` -f = [FLOW CELL TYPE]` : type of flow cell used, FLO-MIN106  
` -k = [KIT CODE]` : code of seqencing kit used, SQK_LSK_108  
` -o = [OUTPUT TYPE]` : output as fastq or fast5  
` -r = [RECURSIVE]` : looks for files in directories within directories  

Fastq files will be written to:  

`path/to/output/fastq/`  

(Optional) If you want to you can watch how many sequences are being writen by changing to the directory 
where your fastq files are being writen (workspace/pass) and typing this:
```
watch -n 10 'find . -name "*.fastq" -exec grep 'read' -c {} \; | paste -sd+ | bc'
```

`watch` = envoke 'watch' command : tells the computer to watch for something  
`- n 10` = every 10 seconds  
`find .` = look in every directory below where you are   
`-name "*.fastq"` = : target of find which will find every file with 'fastq' in its name  
`-exec` = execute the following command on find .  
`grep` = command to look for stuff within each file found by 'find . -name'  
`'read'` = the thing grep is looking for in the header of each sequence (1 per sequence)  
`-c` = count command : count the number of the occourance 'read' in all files  
`{} \; | paste -sd+ | bc'` = paste the output from grep to basic calculator to display a count on the screen  

### Concatinate fastq files into one:

Once albacore has finished concatinate all the fastq files into one and count them, this is not neccecery if using barcoding 
as porechop will concatinate files automatically.
```
cat *.fastq > /path/to/output/plasmid_cat.fastq
grep 'read' /path/to/output/plasmid_cat.fastq -c
```

## Adapter trimming using the program porechop

Once bases are called, adapter sequences and optional barcode sequences must be removed from the reads before assembly.
Porechop will do this adequately with default settings in this case. Stringent barcoding values can be used to isolate only full length 
end to end reads. See "Nanopak" for examples or for more information and settings call `porechop`.

```
porechop -i /path/to/output/plasmid_cat.fastq -o /path/to/Plasmid_cat_chop.fastq --discard_middle
```

`i` Input file path  
`-o` output file path
`--discard_middle` remove chimeric sequences

### Count reads

Count the number of basecalled reads that passed quality filters from porechop 

```
grep 'read' /path/to/Plasmid_cat_chop.fastq -c
```

## Resample reads

If required, you can resample reads using fastqSample command from the program canu.
To resample 15,000 reads with the same length distrobution but no less than 1000bp:

```
fastqSample -U -p 150000 -m 1000 -I /path/to/plasmid_cat_chop.fastq -O /path/to/Plasmid_cat_chop_15k.fastq
```
`-U` = unpaired reads  
`-p` = total number of random reads (add `-max` to get longest reads)  
`-m` = minimum read lenght  
`-I` [INPUT FILE]  
`-O` [OUTPUT FILE]  

## De-novo plasmid assembly using CANU

To assemble the plasmid without a referance sequence. Use the default settings of canu. 
Detailed help can be found by calling 'canu'. 
In this case we have an aproximate genome size from PFGE. From Canu manual it is usually better to overestimate the genome size.

```
canu -p plasmid_assembly -d Sev_plasmid_assembly genomeSize=150k -nanopore-raw /path/to/plasmid_cat_chop_15k.fastq

```

`canu` = Envoke canu command  
`-p` = output directory name  
`-d` = temporary output directory name  
`genomeSize` = very aproximate genome size, better to overestimate  
`-nanopore-raw` = type of read (uncorrected raw)  

Check assembly in bandage. Then use the .gfa file to find the overlap at the two ends and trim the fasta file at that point.
Alternitivly search the start or end of the assembly to find the overlap trim point. This is importent for nanopolish to have
better end alignments. 

Save trimmed plasmid sequence to `/path/to/output/plasmid_trimmed_15k.fastq` with the header in the fastq file set
to `>plasmid_ID`.

## Polish the assembly with Nanopolish.

Nanopolish is used to increase the consensus sequence accuracy. You can reduce the time it takes to index the reads by only indexing the fast5 files randomly subsampled using `fastqSample`. 

To match the subsampled fastq file reads back to the fast5 files, construct a new directory to copy the fast5 files to and call `fast5seek`.
See fast5seek github page for more information on two stage process when using local machines. 

```
mkdir /path/to/plasmid_sample_fast5/
fast5seek -i /path/to/all/plasmid_fast5/fast5 -r /path/to/output/plasmid_trimmed_15k.fastq | xargs cp -t /path/tp/plasmid_sample_fast5/

```
`-i` : input fast5 dir
`r` : subsampled fastq reads file 
`| xargs cp -t` : pipe output to xargs and copy matching fast5 files

Nanopolish needs access to signal data in fast5 files that corrispond to fastq reads in the assembly.
Index `plasmid_cat_chop_15k.fastq` reads with their corrisponding fast5 files that contain raw squiggle data. 

Call `nanopolish index`.

```
nanopolish index -d /path/to/plasmid_sample_fast5/ /path/to/plasmid_cat_chop_15k.fastq
```

Align `plasmid_cat_chop_15k.fastq` with the draft assembly from canu using `minimap2` and index them using `samtools`.

```
minimap2 -ax map-ont -t 96 /path/to/plasmid_trimmed_15k.fastq /path/to/plasmid_cat_chop_15k.fastq | samtools sort -o /path/to/output/reads_sorted.bam -T reads.tmp
samtools index reads.sorted.bam
```

Check the `reads_sorted.bam` file has reads in it.

```
samtools view /path/to/reads_sorted.bam | head
```

Polish the assembly from canu call `nanopolish_makerange.py` for assemblys > 1mb and `variants` <100 kb

```
nanopolish variants --consensus plasmid_polished.fasta  -w "plasmid_name:0-n" -r /path/to/plasmid_trimmed_15k.fastq -b /path/to/reads_sorted.bam -g /path/to/plasmid_trimmed_15k.fastq
```
`variants --consensus` : construct new polished consensus sequence.
`-w "plasmid_name:0-n` plasmid name and range in fasta header to polish, replace n with the length of the plasmid sequence.
`
