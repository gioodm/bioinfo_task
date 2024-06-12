#!/usr/bin/env python3.11
# @author Giorgia Del Missier

import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--assembly2', required=True,
                    help='assembly file of reference genome')
parser.add_argument('--homologs', required=True,
                    help='file containing homologs pairs from the two assemblies')
parser.add_argument('--uniprot_mapping', required=True,
                    help='output file containing the mapping between the reference assembly, \
                          the UniProt IDs and the corresponding homolog in assembly 1')
args = parser.parse_args()


# create a mapping between the query identifier (EMBL coding sequence ID) and the gene name for assembly 2
query2gene = dict()
with open(args.assembly2, "r") as fassembly2:
    lines = fassembly2.readlines()
    for line in lines:
        if line.startswith(">"):
           l = line.strip(">").split(" ")
           query2gene[l[1]]=l[0]

# create a list of all the EMBL coding sequence IDs in assembly 2
cdynames = list()
with open(args.homologs, "r") as fhomologs:
    lines = fhomologs.readlines()
    for line in lines:
        if line.startswith("#"):
            continue
        line = line.strip().split("\t")
        cdynames.append(line[1])

# map each EMBL coding sequence ID in assembly 2 to its UniProt ID using the UniProt API
UNIPROT_API = "https://rest.uniprot.org/"

# use pagination to reduce retrieval time and number of requests to the API
chunksize = 1000
chunks = [cdynames[x:x+chunksize] for x in range(0, len(cdynames), chunksize)]

def get_UniProt(chunk):
    pnames = "%20OR%20".join(chunk)

    for trynum in range(199):
        try:
            # together with the UniProt ID and the corresponding gene name, info about the EC number is also returned when available
            response = requests.get(f"{UNIPROT_API}/uniprotkb/stream?fields=id%2Caccession%2Cgene_primary%2Cec&format=tsv&query=%28{pnames}%29",timeout=3)
            break
        except Exception as e:
            continue

    return response.text

all_results = []    
for chunk_index, chunk in enumerate(chunks):
    print(f"Running chunk {chunk_index}")
    all_results.append(get_UniProt(chunk))

# save the mapping to a dictionary
cdy2up = dict()
for result in all_results:
    for r in result.split('\n')[1:-1]:
        terms = r.split('\t')[1:]
        gene_name = terms[1]
        if gene_name in query2gene:
            cdy2up[query2gene[gene_name]] = terms

# write the mapping to an output file
with open(args.homologs, "r") as fhomologs, open(args.uniprot_mapping, "w") as fout:
    fout.write(f"#Query (assembly 1) \t Query (assembly 2)\t Gene name (assembly 2)\tUniProt ID (assembly 2)\tEC number (assembly 2)\n")

    all_lines = fhomologs.readlines()[1:]
    for line in all_lines:
        line = line.strip("\n").split("\t")
        if line[1] in cdy2up:
            query = line[0]
            cdy = line[1]
            uniprot =  cdy2up[cdy][0]
            gene_name = cdy2up[cdy][1]
            ec = cdy2up[cdy][2]
            fout.write(f"{query}\t{cdy}\t{gene_name}\t{uniprot}\t{ec}\n")
