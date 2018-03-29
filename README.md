# elastic4clir
An ElasticSearch package for Cross-Lingual Information Retrieval

The goal of *elastic4clir* is to provide a flexible framework for running cross-lingual information retrieval (CLIR) experiments. It implements various retrieval techniques and benchmarks while using ElasticSearch/Lucene as the backend index and search components.


## Installation and Setup

It's assumed that you have Anaconda installed. If not, download and setup your conda path:

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

