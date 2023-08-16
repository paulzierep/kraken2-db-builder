# build custom kraken2 db

## Run

* Open Galaxy Jupyter notebook
* Clone this repo or upload as zip
* Create the conda env (see below)
* modify the vertebrate_mammalian.csv accession input file if needed
* run the script
    * the script can also just download the fasta, get the taxonomy or build the db individually
* upload to zenodo via zenodo_upload.sh (see below)
* split the tar file if zenode 50 GB limit

## Install

```
mamba create -n kraken2 python=3.10
conda activate kraken2
mamba install htop seqfu rsync ncdu ncbi-genome-download kraken2 pandas pv jq
```

# Zenodo upload

See: https://github.com/jhpoelen/zenodo-upload

token=$token
https://zenodo.org/deposit/8248780

```
./zenodo-upload/zenodo_upload.sh https://zenodo.org/deposit/8248780 meat_hosts_tests.tar.gz 
```

# Additional Notes

## Links

* source: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7069206/
* https://telatin.github.io/microbiome-bioinformatics/Build-a-kraken2-database/
* https://software.cqls.oregonstate.edu/updates/docs/kraken2/MANUAL.html

## Note

* gallus gallus cannot be downloaded via the ncbi script, therefore the curl approach

## Code

curl -OJX GET "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/GCF_000001405.40/download?include_annotation_type=GENOME_FASTA,GENOME_GFF,RNA_FASTA,CDS_FASTA,PROT_FASTA,SEQUENCE_REPORT&filename=GCF_000001405.40.zip" -H "Accept: application/zip"

```
curl -OJX GET "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/GCF_000002315.5/download?include_annotation_type=GENOME_FASTA&filename=GCF_000002315.5.zip" -H "Accept: application/zip"
unzip GCF_000002315.5.zip -d GCF_000002315.5
cd ./GCF_000002315.5/ncbi_dataset/data/GCF_000002315.5
seqfu cat --append "|kraken:taxid|9031" GCF_000002315.5_GRCg6a_genomic.fna > GCF_000002315.5_GRCg6a_genomic_taxid.fna # (only needed if no ncbi acession is available)
kraken2-build --add-to-library GCF_000002315.5_GRCg6a_genomic_taxid.fna -db gallus_gallus_kraken2.db --threads 30
kraken2-build --download-taxonomy --db gallus_gallus_kraken2.db --use-ftp
kraken2-build --build --db gallus_gallus_kraken2.db --threads 30 --fast-build
kraken2-build --clean  --db gallus_gallus_kraken2.db --thread 30 --fast-build
```

## NCBI download

* https://github.com/kblin/ncbi-genome-download

```
conda install -c bioconda ncbi-genome-download
```


## classify

```
kraken2 --db gallus_gallus_kraken2.db 'Galaxy1-[Barcode10].fastq.gz' --report --gzip-compressed --thread 30
kraken2 --db gallus_gallus_kraken2.db 'Galaxy1-[Barcode10].fastq.gz' --report report.csv --gzip-compressed --thread 30 > results.csv
```

## test ncbi connection

```
wget ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz
wget -q ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz
```

# zip with progress bar

```
tar cf - taxonomy -P | pv -s $(du -sb taxonomy | awk '{print $1}') | gzip > taxonomy.tar.gz
tar xvzf #unzip
```

# split tar file

```
split --bytes=200M taxonomy.tar.gz tax_chunks/taxonomy.tar.gz.
cat  tax_chunks/taxonomy.tar.gz.* > taxonomy.tar.gz
```

