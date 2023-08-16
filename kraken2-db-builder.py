# conda env kraken

import os
import shutil
import subprocess as sp
import sys

import pandas as pd

db_name = "vertebrate_mammalian_meat_hosts"

ncbi_id_file = "vertebrate_mammalian.csv"
#ncbi_id_file = "vertebrate_mammalian_test.csv"
workdir = "vertebrate_kraken2_db"

taxonomy_path = "./galaxy_inputs/taxonomy/taxonomy.tar.gz.gz"

workdir_fastas = os.path.join(workdir, "fastas")
temp_download_dir = os.path.join(workdir, "tmp_download")
kraken_db = os.path.join(workdir, "kraken2_db")

test_file = "spike3bbarcode10.fastqsanger"

os.makedirs(workdir_fastas, exist_ok = True)
os.makedirs(temp_download_dir, exist_ok = True)
os.makedirs(kraken_db, exist_ok = True)

download_data = False
get_taxonomy = True 
build_db = False

if download_data:

    # Download and store all genome data in workdir_fastas folder

    df = pd.read_csv(ncbi_id_file, sep="\t", index_col=0)

    for row_id, row in df.iterrows():
        
        if os.path.isfile(os.path.join(temp_download_dir, f"{row_id}.zip")): 
            print(f"{row_id}.zip already downloaded.")
        else:
            # this failes sometimes with an 443 error, probably needs an retry, with a wait for maybe 5 - 10 minutes...
            # curl_call = [f'curl --output-dir {temp_download_dir} -OJX GET "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/{row_id}/download?include_annotation_type=GENOME_FASTA&filename={row_id}.zip" -H "Accept: application/zip"']
            # subprocess curl had connection timeouts to NCBI, why IDK !

            for x in range(5):

                os.system(f'curl --output-dir {temp_download_dir} -OJX GET "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/{row_id}/download?include_annotation_type=GENOME_FASTA&filename={row_id}.zip" -H "Accept: application/zip"')
                if os.path.isfile(os.path.join(temp_download_dir, f"{row_id}.zip")): 
                    break
                else:
                    print("NCBI download failed, waiting 5 minutes and try again!")
                    time.sleep(320)

            # print(curl_call)
            # process = sp.Popen(curl_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
            # process.wait()

            unzip_call = [f"unzip {temp_download_dir}/{row_id}.zip -d {temp_download_dir}/{row_id}"]
            process = sp.Popen(unzip_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
            process.wait()

            fasta_folder_path = f"{temp_download_dir}/{row_id}/ncbi_dataset/data/{row_id}"

            for file in os.listdir(fasta_folder_path):
                if ".fna" in file:
                    f_path = os.path.join(fasta_folder_path, file)
                    o_path = os.path.join(workdir_fastas, file)
                    print(f"copy {f_path} to {o_path}")
                    shutil.copyfile(f_path, o_path)

            print(f"Download of {row_id} complete !")

    shutil.rmtree(temp_download_dir)

    # build kraken2 db
    # if not from ncbi taxid needs to be added using e.g.:
    # seqfu cat --append "|kraken:taxid|9031" GCF_000002315.5_GRCg6a_genomic.fna > GCF_000002315.5_GRCg6a_genomic_taxid.fna 

# if you have a copy of the taxonomy db it does not need to be downloaded all the time !
# if used as input in galaxy use:
# cp taxonomy.tar.gz.gz taxonomy.tar.gz
# tar -xf taxonomy.tar.gz

if get_taxonomy:

    if taxonomy_path:
        kraken_taxonomy_path = os.path.join(kraken_db, "taxonomy.tar.gz")
        # temp_taxonomy_path = os.path.join(workdir, "tmp_taxonomy")

        print("Copy taxonomy folder.")

        #copy db from symlink
        #kraken_call = [f'rsync -ah --progress {taxonomy_path} {kraken_taxonomy_path}']
        #process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
        #process.wait()

        #untar 
        kraken_call = [f'tar -xvf {kraken_taxonomy_path} -C {kraken_db}'] #folder is already called taxonomy
        process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
        process.wait()

        print("Done !")

    else:
        kraken_call = [f'kraken2-build --download-taxonomy --db {kraken_db} --use-ftp']
        process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
        process.wait()


if build_db:

    # add all fasta to library
    for file in os.listdir(workdir_fastas):
        file_path = os.path.join(workdir_fastas, file)
        kraken_call = [f'kraken2-build --add-to-library {file_path} -db {kraken_db} --threads 30']
        process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
        process.wait()

    kraken_call = [f'kraken2-build --build --db {kraken_db} --threads 30 --fast-build']
    process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
    process.wait()

    kraken_call = [f'kraken2-build --clean --db {kraken_db} --threads 30 --fast-build']
    process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
    process.wait()

    # test db by running kraken2

    kraken_call = [f'kraken2 --db {kraken_db} {test_file} --report report.csv --thread 30 --confidence 0.01 > results.csv']
    process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
    process.wait()

    # test db by inspecting
    kraken_call = [f'kraken2-inspect --db {kraken_db} > db_inspected.csv']
    process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
    process.wait()

    # compress db
    kraken_call = [f"tar -czvf {db_name}.tar.gz {kraken_db}"]
    process = sp.Popen(kraken_call, stderr=sys.stderr, stdout=sys.stdout, shell=True)
    process.wait()
