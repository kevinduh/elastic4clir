#!/usr/bin/env python

from elasticsearch import Elasticsearch
import itertools
import codecs
import gzip
import os
import datetime
import configparser
import sys
from eval_AQWV import get_reference
from collections import defaultdict

configFile = str(sys.argv[1])

config = configparser.ConfigParser()
config.read(configFile)

#Supports multiple data-directories
datadirs = [x.strip() for x in config['Indexer']['datadir'].split(',')]
docIndex = config['Indexer']['index'].strip()
docType = 'doc'
newField = 'qrel'
analyzer = 'whitespace'
reference_file = config['Evaluation']['reference_file']
verbose = int(config['Indexer']['verbose'].strip())

def index_document(es, doc_id, doc_text):
    '''Index a document into ElasticSearch with id=doc_id and text=doc_text'''
    status = ''
    if not es.exists(index = docIndex, doc_type = docType, id = doc_id):
        es.index(index = docIndex, doc_type = docType, id = doc_id, body = {newField : doc_text})
        status='CREATING'
    else:
        es.update(index = docIndex, doc_type = docType, id = doc_id, body = {docType : {newField : doc_text}})
        status = 'UPDATING'

    return status




########################
# Get query relevance from relevance file
ref_out = get_reference(reference_file)
doc2qrel = defaultdict(str)
for qry in ref_out:
    for doc_id in ref_out[qry]:
        doc2qrel[doc_id] += "%s "%qry


########################
# Setup ElasticSearch
es = Elasticsearch()
if not es.indices.exists(index = docIndex):
    es.indices.create(index = docIndex)

mapping = '''{
  "properties": {
    \"%s\": {
      "type": "text",
      "analyzer": \"%s\"
    }
  }
}'''%(newField, analyzer)

es.indices.put_mapping(index = docIndex, doc_type = docType, body = mapping)

########################
# Loop over files in datadirs and start indexing
totalcount = num_updates = num_created = 0
for datadir in datadirs:
    for filename in os.listdir(datadir):
        if filename.startswith('MATERIAL'):
            doc_id=filename.split('.')[0]
            qrel = doc2qrel[doc_id]
            status = index_document(es, doc_id, qrel)
            if status == 'CREATING':
                num_created += 1
            elif status == 'UPDATING':
                num_updates += 1
            totalcount += 1
            if verbose >= 1:
                print("%s ==> current file Number : %s ; %d "%(status, doc_id, totalcount))


print("Total %d docs created and %d docs updated in index %s" %(num_created, num_updates, docIndex))
if verbose >= 1:
    print("Current ElasticSearch mapping:")
    print(es.indices.get_mapping(index = docIndex, doc_type = docType))
                


