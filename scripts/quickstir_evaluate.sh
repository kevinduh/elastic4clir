#!/bin/bash
#
# Indexes a MATERIAL collection and evaluates AQWV score against a standard test set

if [ $# -ne 3 ]; then
    echo "Usage: quickstir_evaluate.sh data_dir1 data_dir2 template.cfg"
    echo "    where data_dir{1,2} points to directories containing documents to index"
    echo "    e.g. /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1A/ANALYSIS1/{text,audio}/translation"
    echo "    and template.cfg points to config file of desired collection"
    echo "    e.g. collections/sw-en/analysis1/template.cfg"
    exit
fi

datadir1=$1
datadir2=$2
template=$3

source activate elastic4clir
scriptdir=$(cd `dirname $0` && pwd)
outputdir=tmp.$RANDOM


mkdir -p $outputdir
sed "s@__DIR1__@$datadir1@g" $template | \
    sed "s@__DIR2__@$datadir2@g" | \
    sed "s@__OUTPUTDIR__@$outputdir@g" > $outputdir/run.cfg

python $scriptdir/index.py $outputdir/run.cfg
python $scriptdir/eval_AQWV.py $outputdir/run.cfg
