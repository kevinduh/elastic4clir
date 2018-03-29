# elastic4clir
An ElasticSearch package for Cross-Lingual Information Retrieval

The goal of *elastic4clir* is to provide a flexible framework for running cross-lingual information retrieval (CLIR) experiments. It implements various retrieval techniques and benchmarks while using ElasticSearch/Lucene as the backend index and search components.


## Installation and Setup

It's assumed that you have Anaconda installed. If not, download and setup your conda path like below. It's recommended that you add the conda path to your .bashrc. 

```bash
wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
bash Miniconda2-latest-Linux-x86_64.sh
export PATH=$HOME/miniconda2/bin:$PATH
```

Once you have Anaconda, clone this repo and run the install script, which sets up the conda environment with the necessary dependencies and downloads the ElasticSearch binaries:

```bash
./scripts/install.sh
```

This version of elastic4clir is based on ElasticSearch version 5.6.3. To start the ElasticSearch server, run:

```bash
./scripts/server.sh start
```

To stop the ElasticSearch server, run:

```bash
./scripts/server.sh stop
```

Note that all indexed files persist in the ElasticSearch data directory and can be re-used across server restarts. To remove these indices, run:

```bash
./scripts/server.sh clean
```

## Running Experiments

# Running Experiments using different translation results

In the document-translation approach to CLIR, we first translate all the foreign documents in the collection to English. This lets us to run the English queries as if it were monolingual IR. Of course, the IR result will depend on the quality of the translation. This *elastic4clir* package enables the evaluation of various translated results in terms of IR metrics like AQWV.

The process for running such an CLIR experiments is:
1. Start ElasticSearch server: `./scripts/server.sh start`
2. Prepare the translations of your test collection, then run the following script with three arguments:

```bash
/scripts/quickstir_evaluate.sh datadir1 datadir2 template.cfg
```

where `datadir1` and `datadir2` are the speech and text translations of the test collection in question, and template.cfg is points to the configuration file in the `collection` subdirectory.

As an example, suppose we are interested in evaluating the results of human translations on the MATERIAL Swahili-English Analysis1 collection, then we would run the following:

```
/scripts/quickstir_evaluate.sh /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1A/ANALYSIS1/text/translation/ /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1A/ANALYSIS1/audio/translation/ collection/material/sw-en/analysis1/template.cfg
```

Note that this script is designed to make it easy to run MATERIAL ASR/MT end evaluation with CLIR, so there are always two data directories (one for speech, one for text; the order does not matter). If there is a template.cfg in one of the subdirectories of `collection`, that means it is possible to run `quickstir_evaluate.sh` and get an IR metric like the AQWV score.

As a second example, suppose we are interested in evaluating the results of human translations on the MATERIAL Tagalog-English Analysis1 collection, then we would run the following:

```
/scripts/quickstir_evaluate.sh /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1B/ANALYSIS1/text/translation/ /export/corpora5/MATERIAL/IARPA_MATERIAL_BASE-1B/ANALYSIS1/audio/translation/ collection/material/tl-en/analysis1/template.cfg
```

# Running Experiments using different IR configurations

TODO: This is more advanced usage and will be documented later.


