#!/usr/bin/env bash
# @author Giorgia Del Missier

echo "Installing required packages..."
echo

pip install -r requirements.txt

## TASK 1

# To disambiguate the proteins based on sequence similarity I am using the MMseqs2 software suite (https://github.com/soedinglab/MMseqs2),
# which runs 10000 times faster than BLAST, achieving similar sensitivity.
# This makes MMseqs2 an effective tool to use with very large databases / large assemblies.

# Installation

echo "Installing MMseqs2..."
echo

# install via conda
#conda install -c conda-forge -c bioconda mmseqs2
# static build with AVX2 (fastest)
wget https://mmseqs.com/latest/mmseqs-linux-avx2.tar.gz; tar xvfz mmseqs-linux-avx2.tar.gz; export PATH=$(pwd)/mmseqs/bin/:$PATH
# static build with SSE4.1
#wget https://mmseqs.com/latest/mmseqs-linux-sse41.tar.gz; tar xvfz mmseqs-linux-sse41.tar.gz; export PATH=$(pwd)/mmseqs/bin/:$PATH


# Sequence alignment

echo "Performing sequence alignment..."
echo

# the easy-search workflow searches a FASTA file against another FASTA file
mmseqs easy-search --format-output "query,target,qlen,tlen,fident,alnlen,mismatch,qstart,qend,tstart,tend,evalue,bits" \
                   --threads 64 --max-seqs 1000 -s 9.5 --min-seq-id 0.95 -c 0.9 \
                   data/assembly_1.prot.fa data/assembly_2.prot.fa results/out.m8 tmp

# the --max-seqs option specifies the maximum number of results per query sequence allowed to pass the prefilter
# -s specificies the sensitivity
# the --min-seq-id option lists matches above a threshold sequence identity
# the -c option lists matches above a fraction of aligned (covered) residues


# another option could be to use the easy-rbh workflow, which performs a reciprocal best hit search between the two FASTA files,
# adding confidence to the pair of homologs identified between the two assemblies
# mmseqs easy-rbh --format-output "query,target,qlen,tlen,fident,alnlen,mismatch,qstart,qend,tstart,tend,evalue,bits" \
#                 --threads 64 --max-seqs 1000 -s 9.5 --min-seq-id 0.95 -c 0.9 \
#                 data/assembly_1.prot.fa data/assembly_2.prot.fa results/out_rbh.m8 tmp


# Merge FASTA files

echo "Merging fasta files..."
echo

python3 merge_fasta.py --alignment_results results/out.m8 --assembly1 data/assembly_1.prot.fa \
                       --merged_fasta results/merged.fasta --mapped_assemblies results/homologs.txt

# the output file merged.fasta will contain all proteins from the poorly annotated assembly 1; 
# when a homologue sequence has been identified in the reference assembly 2, both IDs from the two assemblies are reported


## TASK 2

# the function map2uniprot.py maps each identifier in the reference assembly to its corresponding UniProt ID (where possible),
# together with the corresponding gene name and EC number (when available)
# it then writes the results in the output file uniprot_mapped.txt, which also contains the corresponding homolog in the poorly annotated assembly

echo "Mapping proteins to UniProt IDs..."
echo

python3 map2uniprot.py --assembly2 data/assembly_2.prot.fa --homologs results/homologs.txt \
                       --uniprot_mapping results/uniprot_mapped.txt

# the script takes around 2 minutes to run for around 46000 proteins, making it suitable also for large scale datasets

# enzymes can be classified using the Enzyme Commission (EC) numbers; 
# hydrolases acting on ester bonds are identified by an EC number starting with 3.1;
# to identify proteins in the poorly annotated assembly 1 with EC number starting with 3.1, we can use grep on the output file produced in the previous file

echo

p=$(grep -E '3\.1\.\d+\.\d+' results/uniprot_mapped.txt | awk '{print $1}')
s=$(grep -E '3\.1\.\d+\.\d+' results/uniprot_mapped.txt | wc -l)

echo "Total number of proteins in the poorly annotated assembly 1 with EC number starting with 3.1: $s"
echo "Proteins in the poorly annotated assembly 1 with EC number starting with 3.1: $p"
