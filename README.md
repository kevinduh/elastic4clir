# elastic4clir
An ElasticSearch package for Cross-Lingual Information Retrieval

The goal of *elastic4clir* is to provide a flexible framework for running cross-lingual information retrieval (CLIR) experiments. It implements various retrieval techniques and benchmarks while using ElasticSearch/Lucene as the backend index and search components.


## Installation

It's assumed that you have Anaconda installed. If not, download and setup your conda path like below. It's recommended that you add the conda path to your .bashrc (`export PATH=$HOME/miniconda2/bin:$PATH`). 

```bash
wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
bash Miniconda2-latest-Linux-x86_64.sh
export PATH=$HOME/miniconda2/bin:$PATH
```

Once you have Anaconda, clone this repo and run the install script, which sets up the conda environment with the necessary dependencies and downloads the ElasticSearch binaries:

```bash
./scripts/install.sh
```

## ElasticSearch Server

This version of elastic4clir is based on ElasticSearch version 5.6.3. To start the ElasticSearch server, run:

```bash
./scripts/server.sh start
```

To stop the ElasticSearch server (and delete the indices), run:

```bash
./scripts/server.sh stop
```

To check the status of the server/indices, run `./scripts/server.sh status`.


## Running Experiments

### Running Experiments using different translation results

In the document-translation approach to CLIR, we first translate all the foreign documents in the collection to English. This lets us to run the English queries as if it were monolingual IR. Of course, the IR result will depend on the quality of the translation. This *elastic4clir* package enables the evaluation of various translated results in terms of IR metrics like AQWV.

The process for running such an CLIR experiments is:
1. Start ElasticSearch server: `./scripts/server.sh start`
2. Prepare the translations of your test collection, then run the following script with three arguments:

```bash
./scripts/quickstir_evaluate.sh datadir1 datadir2 template.cfg
```

where `datadir1` and `datadir2` are the speech and text translations of the test collection in question, and template.cfg points to the configuration file in the `collection` subdirectory.

As an example, suppose we are interested in evaluating the results of human translations on the MATERIAL Swahili-English Analysis1 collection, then we would run the following:

```
./scripts/quickstir_evaluate.sh /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1A/ANALYSIS1/text/translation/ /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1A/ANALYSIS1/audio/translation/ collection/material/sw-en/analysis1/template.cfg
```

Note that this script is designed to make it easy to run MATERIAL ASR/MT end evaluation with CLIR, so there are always two data directories (one for speech, one for text; the order does not matter). If there is a template.cfg in one of the subdirectories of `collection`, that means it is possible to run `quickstir_evaluate.sh` and get an IR metric like the AQWV score. The script assumes that each of the data directories contains files with the same naming convention as the MATERIAL data packs (see e.g. `/export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1A/ANALYSIS1/text/translation/`). Importantly, each file name is prefixed with `MATERIAL_BASE-$language_$id` and consists of a document. If there are any tab-separated columns in these files, the last one is assumed to be the English translation. 

As a second example, suppose we are interested in evaluating the results of human translations on the MATERIAL Tagalog-English Analysis1 collection, then we would run the following:

```
./scripts/quickstir_evaluate.sh /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1B/ANALYSIS1/text/translation/ /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1B/ANALYSIS1/audio/translation/ collection/material/tl-en/analysis1/template.cfg
```

3. The above script will generate temporary output directories (`tmp.$random_number`). These can be safely deleted anytime. The `search_output.txt` file in the temporary output directory records the retrieved results of the IR run, in TREC-Eval format. The `nohit_queries.txt` file shows the queries (in the parsed form given to ElasticSearch) that do not return any document hits (i.e. OOVs). These can be used if further analysis of retrieved results is needed.

4. Multiple runs with different datadir can be made while the ElasticSearch server is up. Once done, stop the server with `./scripts/server.sh stop`.

A note on the AQWV results: the Swahili-English Analysis1 human reference translations should give the following AQWV results:

```
Total 0 docs created and 471 docs updated in index sw-en-analysis1
Total returned hits from all 300 queries: 1073
Oracle QWV:               0.3440
AQWV for max_hits=5:      0.2527
#queries evaluated:        150
...
QWV (Query Weighted Value) = 0.55572059
P_miss = 0.308880406667
P_falseAlarm = 0.00677005333333
speech,80,0.653750,0.004149,0.263266
text,125,0.618724,0.007624,0.228787
modifiedAQWV(to account for queries with no relevant documents),300,0.617761,0.006770,0.246838
```

The Actual Query Weighted Value, evaluated at maximum 5 hits per query, is 0.2527. This is the all-filt AQWV and should be the main metric for comparison. Other metrics are 0.5557 (all-unfilt), 0.263 (speech), 0.228 (text), 0.246 (modified). 

The Tagalog-English Analysis1 human reference results are:

```
Total 0 docs created and 462 docs updated in index tl-en-analysis1
Total returned hits from all 300 queries: 1227
Oracle QWV:               0.5688
AQWV for max_hits=5:      0.4478
#queries evaluated:        125
...
QWV (Query Weighted Value) = 0.677400153333
P_miss = 0.163785703333
P_falseAlarm = 0.00794098666667
speech,56,0.384141,0.006630,0.483256
text,93,0.424014,0.008247,0.411049
modifiedAQWV(to account for queries with no relevant documents),300,0.393086,0.007941,0.448095
```

### Running Experiments using different IR configurations

TODO: This is more advanced usage and will be documented later.


