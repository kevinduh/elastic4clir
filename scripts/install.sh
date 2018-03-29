#!/bin/bash
#
# Installs ElasticSearch and the dependencies

rootdir=$(cd `dirname $0/`/.. && pwd)
cd $rootdir

# 1. create conda environment
echo "1. Creating conda environment: elastic4clir"
conda env create -f conda-elastic4clir-env.yml

# 2. download ElasticSearch
version=5.6.3
echo "2. Downloading ElasticSearch"
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${version}.tar.gz
gunzip elasticsearch-${version}.tar
tar -xvf elasticsearch-${version}.tar
rm elasticsearch-${version}.tar
