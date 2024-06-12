#!/usr/bin/env python3.11
# @author Giorgia Del Missier

import argparse
import pandas as pd
from Bio import SeqIO

parser = argparse.ArgumentParser()
parser.add_argument('--alignment_results', required=True,
                    help='mmseqs2 alignment results (.m8 file)')
parser.add_argument('--assembly1', required=True,
                    help='assembly file of poorly annotated genome')
parser.add_argument('--merged_fasta', required=True,
                    help='merged fasta file produced as output')
parser.add_argument('--mapped_assemblies', required=True,
                    help='mapped identifiers between the two assemblies')
args = parser.parse_args()


def process_fasta(fasta):
    identifier, sequence = fasta.id, str(fasta.seq)

    if identifier in query_target_dict:
        new_identifier = f"{identifier} | {query_target_dict[identifier]}"
        return f">{new_identifier}\n{sequence}\n", f"{identifier}\t{query_target_dict[identifier]}\n"

    else:
        return f">{identifier}\n{sequence}\n", None


# open the alignment results and identify the best hits
falignment = pd.read_csv(args.alignment_results, header=None, sep="\t")
falignment.columns = "query,target,qlen,tlen,fident,alnlen,mismatch,qstart,qend,tstart,tend,evalue,bits".split(",")
falignment = falignment.drop_duplicates(subset=["query"], keep="first")
query_target_dict = dict(zip(falignment['query'], falignment['target']))

# open the assembly fasta file
fasta_sequences = SeqIO.parse(open(args.assembly1),'fasta')

# store processed data
merged_fasta_lines = []
mapped_assembly_lines = []

for fasta in fasta_sequences:
    new_fasta_line, mapped_assembly = process_fasta(fasta)
    merged_fasta_lines.append(new_fasta_line)
    if mapped_assembly != None:
        mapped_assembly_lines.append(mapped_assembly)

# save the results
with open(args.merged_fasta, 'w') as fmerged:
    fmerged.writelines(merged_fasta_lines)

with open(args.mapped_assemblies, 'w') as fassemblies:
    fassemblies.write("#Assembly 1\tAssembly 2\n")
    fassemblies.writelines(mapped_assembly_lines)

