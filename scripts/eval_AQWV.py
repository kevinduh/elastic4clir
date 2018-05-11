#!/usr/bin/env python

import sys
import os
import re
import subprocess
import collections
from bs4 import BeautifulSoup
import json
import importlib
from configparser import SafeConfigParser
from collections import OrderedDict, defaultdict
from elasticsearch import Elasticsearch
import math

#Hardcoding the path to official implementation of material scoring. 
MATERIAL_EVAL_PATH = '/export/corpora5/MATERIAL/tools/MATERIAL_tools-0.5.2/'

#Hardcoding the conversion of domain names needed for the official NIST script
domain_id2name = {
    'GOV':'Government-And-Politics',
    'LIF':'Lifestyle',
    'BUS':'Business-And-Commerce',
    'LAW':'Law-And-Order',
    'HEA':'Physical-And-Mental-Health',
    'MIL':'Military'
}

#Checks all possible max_hits and finds the best AQWV overall
def best_score_overall(ref_out, search_out, beta, max_hits, N_total, out_path):
    #Upper bound max_hits to num docs  indexed
    max_hits = min(max_hits, N_total)
    
    print ("Running AQWV between max_hits of", str(0), "to", str(max_hits))
    #This is the worst possible score
    best_AQWV = -beta
    best_hits = 0
    
    #(Debug) For drawing a graph
    hits = []
    AQWV_scores = []
    
    for cur_hits in range(0, max_hits+1):
        scores = {}
        total_score = 0.0
        total_count = 0
        
        # IMP : For queries not present in both search_out and ref_out, AQWV is not computed
        for qry in search_out:
            if qry not in ref_out:
                continue 
            else:
                ref_docs = ref_out[qry]
                search_docs = set( list( search_out[qry].keys() )[0:cur_hits+1] )
                
                N_miss = len(ref_docs - search_docs) 
                N_FA = len(search_docs - ref_docs)
                N_relevant = len(ref_docs)
                
                P_miss = N_miss * 1.0/N_relevant
                P_FA = N_FA * 1.0/(N_total - N_relevant)
    
                scores[qry] = 1.0 - (P_miss + beta * P_FA)
                
                total_score += scores[qry]
                total_count +=1
    
        cur_AQWV = total_score/total_count
        
        
        AQWV_scores.append(cur_AQWV)
        hits.append(cur_hits)
        
        if cur_AQWV > best_AQWV:
            best_AQWV = cur_AQWV
            best_hits = cur_hits
        
    return best_AQWV, best_hits

#Checks all possible max_hits and finds the best AQWV PER QUERY
def best_score_per_qry(ref_out, search_out, beta, max_hits, N_total, out_path):
    
    #Upper bound max_hits to num docs  indexed
    max_hits = min(max_hits, N_total)
    scores = {}
    total_score = 0.0
    total_count = 0

    oracle_fid = open(os.path.join(out_path, "oracle_qwv.txt"), 'w')
    oracle_fid.write("# query optimal_max_hit oracle AQWV / (ES scores)\n")
    # IMP : For queries not present in both search_out and ref_out, AQWV is not computed
    for qry in search_out:
        if qry not in ref_out:
            continue 
        else:
            best_AQWV = -beta
            for cur_hits in range(0, max_hits+1):
                
                ref_docs = ref_out[qry]
                search_docs = set( list( search_out[qry].keys() )[0:cur_hits+1] )
                
                N_miss = len(ref_docs - search_docs) 
                N_FA = len(search_docs - ref_docs)
                N_relevant = len(ref_docs)
                
                P_miss = N_miss * 1.0/N_relevant
                P_FA = N_FA * 1.0/(N_total - N_relevant)
    
                scores[qry] = 1.0 - (P_miss + beta * P_FA)
                if scores[qry] > best_AQWV:
                    best_AQWV = scores[qry]
                    optimal_max_hits = cur_hits
                
            total_score += best_AQWV
            total_count +=1
            oracle_fid.write("%s \t %d/%d \t %.2f \t %.2f\n\t"%(qry, optimal_max_hits, len(search_docs), best_AQWV, scores[qry]))
            for s in search_out[qry].values():
                oracle_fid.write("%.3f "%s)
            oracle_fid.write("\n")
            
    cur_AQWV = total_score/total_count
    oracle_fid.write("# Oracle QWV for max_hits=%d: %.4f\n" %(max_hits, cur_AQWV))
    oracle_fid.close()
    return cur_AQWV


def get_reference(ref_file):
    ref_out = defaultdict(set)
    with open(ref_file, 'r') as f_ref:
        f_ref.readline()
        for cur_line in f_ref:
            q_id, doc_id = cur_line.split()
            ref_out[q_id].add(doc_id)
    return ref_out
            
#Implements the AQWV metric
def compute_AQWV(ref_file, out_file, N_total, max_hits):

    #Populate the reference outputs
    ref_out = get_reference(ref_file)

    #Populate the search_output
    search_out = {}
    with open(out_file, 'r') as f_out:
        for cur_line in f_out:
            toks = cur_line.strip().split()
            assert len(toks) == 6
            
            q_id = toks[0]; doc_id = toks[2]; sim = float(toks[4]);
            if q_id not in search_out:
                search_out[q_id] = OrderedDict()
            if doc_id != 'NO_HIT':
                search_out[q_id][doc_id] = sim
        
        #For each query , sort the documents acc. to  similarity
        for q in search_out:
            search_out[q] = OrderedDict(sorted(search_out[q].items(), key = lambda x:x[1], reverse = True))
        
   
    #Define AQWV parameters
    C = 0.0333
    V = 1.0
    P_relevant = 1.0/600
    #Beta can be computed from the above quanties. But for CLIR, it is set to 20.0 
    #IMP : Need to see the use of theta 
    beta = 20.0
    theta = 0.0
    
    #score, hits = best_score_overall(ref_out, search_out, beta, max_hits, N_total, os.path.split(out_file)[0])
    score = best_score_per_qry(ref_out, search_out, beta, max_hits, N_total, os.path.split(out_file)[0])
    print("Oracle QWV:          \t %.4f" %score)

    #Computing AQWV for given max-hits
    scores = {}
    total_score = 0.0
    total_count = 0
    
    for qry in search_out:
        if qry not in ref_out:
            # For queries not present in the reference, AQWV is not computed.
            # This corresponds to all-filt AQWV in the official script
            continue 
        else:
            ref_docs = ref_out[qry]
            search_docs = ( search_out[qry].keys() )
            
            N_miss = len(ref_docs - search_docs) 
            N_FA = len(search_docs - ref_docs)
            N_relevant = len(ref_docs)
            
            P_miss = N_miss * 1.0/N_relevant
            P_FA = N_FA * 1.0/(N_total - N_relevant)

            scores[qry] = 1.0 - (P_miss + beta * P_FA)
            
            total_score += scores[qry]
            total_count +=1
            #print("%s N_miss:%d N_FA:%d N_relevant:%d P_miss:%f P_FA:%f QWV:%f" %(qry,N_miss,N_FA,N_relevant,P_miss,P_FA,scores[qry]))
            
    cur_AQWV = total_score/total_count
    print("AQWV for max_hits=%d: \t %.4f" %(max_hits, cur_AQWV))
    print("#queries evaluated:   \t %d" %total_count)

    
def parse_query(query_string):
    '''very basic query parser'''
    conjunction = query_string.split(',')
    q = ""
    for c in conjunction:
        c2 = c.replace('EXAMPLE_OF(','').replace(')','').replace('"','').replace('+','').replace('<','').replace('>','')
        c3 = c2.split('[')[0]
        q+= c3 + " "
    return q
    

def get_queries(query_file):
    if not os.path.isfile(query_file) or os.stat(query_file).st_size == 0:
        return None
    
    query_dict = {}
    with open(query_file, 'r') as f:
        f.readline()
        for idx,cur_line in enumerate(f):
            query_id, query_string, domain_id, = cur_line.rstrip().split('\t')[0:3]
            query_dict[query_id] = {}
            query_dict[query_id]['parsed'] = parse_query(query_string)
            query_dict[query_id]['original'] = query_string + ":" + domain_id2name[domain_id]
            
    return query_dict


#Normalize the similarity scores such that they are between 0 and 1
#Some times scores can be negative. So we add all scores by min and then normalize by sum
def normalize_scores(res):
    count = 0
    min_score = float("inf")
    tot_score = 0.0
    
    for each_doc in res['hits']['hits']:
        each_score = float(each_doc['_score'])
        count += 1
        tot_score += each_score
        if each_score < min_score:
            min_score = each_score

    tot_score += count * min_score
    for each_doc in res['hits']['hits']:
        each_doc['_score'] = (float(each_doc['_score']) + min_score)/tot_score



def create_DocumentList(output_path, dataset_name, es_index):
    #Generate list of documents (for NIST script)
    with open(os.path.join(output_path, dataset_name + '_CLIR_AllDocIDs.tsv'), 'w') as f_datasetDocIDs:
        f_datasetDocIDs.write(dataset_name + '\n')
        es = Elasticsearch()
        r = es.search(index = es_index, body = {'query': {'match_all': {}}}, filter_path=['hits.hits._id'], size = 10000)
        for d in r['hits']['hits']:
            f_datasetDocIDs.write(d['_id'] + '\n')

            
def compute_AQWV_official(base_out_folder, dataset_name, ref_file, queries):
    '''Compute AQWV using the official NIST scripts'''

    #Create a sub-directory for Reference
    out_folder = os.path.join(base_out_folder, 'Reference')
    if not os.path.exists(out_folder):
        os.mkdir(out_folder)
    
    #Create subdirectory for generatedinputfiles
    gen_out_folder = os.path.join(base_out_folder, 'GeneratedInputFiles')
    if not os.path.exists(gen_out_folder):
        os.mkdir(gen_out_folder)

    #Create a subdirectory for scoredQWV files
    score_out_folder = os.path.join(base_out_folder, 'QueryScores')
    if not os.path.exists(score_out_folder):
        os.mkdir(score_out_folder)
    
    path_to_doc_file = os.path.join(base_out_folder, dataset_name + '_CLIR_AllDocIDs.tsv')
    path_to_query_files = os.path.join(base_out_folder, 'SystemOutputFiles')
    path_to_ref_files = os.path.join(base_out_folder, 'Reference')
    material_validator = os.path.join(MATERIAL_EVAL_PATH, 'material_validator.py')
    material_scorer = os.path.join(MATERIAL_EVAL_PATH, 'material_scorer.py')

    # get reference as dictionary of query -> relevant doc_id
    ref_out = get_reference(ref_file)    

    if verbose >= 1:
        print ('Calling Material Validator to create <GeneratedInputFiles> and Scorer to create <QueryScores>')

    #Generate generatedinputfiles for each query in ref_out and in search out
    for qry in queries:
        ref_file = os.path.join(path_to_ref_files, dataset_name + '_CLIR_' + 'q-' + qry + '.tsv')
        with open(ref_file, 'w') as f_qry:
            f_qry.write(qry + '\t' + queries[qry]['original'] + '\n')
            if qry in ref_out:
                for rel_docs in ref_out[qry]:
                    f_qry.write(rel_docs + '\n')

        qry_file = os.path.join(path_to_query_files, 'q-' + qry + '.tsv')        
        gen_file = os.path.join(gen_out_folder, 'q-' + qry + '.ScoringReady.tsv')
        score_file = os.path.join(score_out_folder, 'q-' + qry + '.AQWVscores.tsv')
        val_command = material_validator + ' -s ' + qry_file + ' -d ' + path_to_doc_file + ' -r ' + ref_file + ' -g ' + gen_file
        #Add beta for customization
        score_command = material_scorer + ' -g ' + gen_file + ' -w ' + score_file            
        subprocess.call(val_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)     
        subprocess.call(score_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    #Generate final AQWV score
    if verbose >= 1:
        print ('Calculating Official AQWV score ..')

    fin_score_command = material_scorer + ' -m ' + score_out_folder + ' -w ' + os.path.join(base_out_folder, 'FinalAQWVscore.txt')
    subprocess.call(fin_score_command, shell=True)
    print ('Official AQWV score at ' + os.path.join(base_out_folder, 'FinalAQWVscore.txt') )
    subprocess.call(['cat',os.path.join(base_out_folder, 'FinalAQWVscore.txt')])


    #Generate fine-grained AQWV score report
    if verbose >= 1:
        print('Calculating fine-grained AQWV score report (this may take a while)...')

    material_filter = os.path.join(MATERIAL_EVAL_PATH, 'material_filter.py')
    scoring_output = os.path.join(base_out_folder, 'AQWVreports')
    tmp_out = scoring_output + '-tmp'
    language_code = dataset_name.split('-')[1] # this is hardcoded, e.g. 1A
    nist_file_mapping = MATERIAL_EVAL_PATH + '/data/filteringFiles/' + language_code + '_mapping_genre_docid.tsv' # this is hardcoded and dependent on NIST tool setup
    filter_command = material_filter + ' --sysout_dir ' + path_to_query_files + ' --dataset_docids ' + path_to_doc_file + ' --ref_dir ' + path_to_ref_files + ' --perf_period ' + dataset_name + ' --material_tools ' + MATERIAL_EVAL_PATH + ' --tmp_out ' + tmp_out + ' --scoring_output ' + scoring_output + ' --nist_file_mapping ' + nist_file_mapping
    fid_out = open(os.path.join(base_out_folder, 'AQWVreports.txt'), 'w')
    subprocess.call(filter_command, shell=True, stdout=fid_out, stderr=subprocess.DEVNULL)
    fid_out.close()
    subprocess.call(['tail','-3', os.path.join(base_out_folder, 'AQWVreports.txt')])


def eval_AQWV(query_file, reference_file, output_path, search, es_index, system_id, dataset_name, max_hits, run_official_AQWV, verbose):
    #Create output_path if it doesn't exist
    if not os.path.exists(output_path):
        os.mkdir(output_path)
        
    #File to store search output
    SEARCH_OUT = os.path.join(output_path, "search_output.txt")
    f_out = open(SEARCH_OUT,'w')
    
    #File to record queries with no hits
    NOHIT_OUT = os.path.join(output_path, "nohit_queries.txt")
    f_nohit = open(NOHIT_OUT,'w')

    if run_official_AQWV:
        #File to store <SystemOutputFiles> of every query
        SYSTEM_OUT_FILES = os.path.join(output_path, "SystemOutputFiles")
        if not os.path.exists(SYSTEM_OUT_FILES):
            os.mkdir(SYSTEM_OUT_FILES)


    #Count the number of documents
    es = Elasticsearch()
    r = es.search(index = es_index, body = {'size' : '0', 'query' : {}})
    N_total = int(r['hits']['total'])

    #Run query
    queries = get_queries(query_file)
    res_list = []
    returned_total = 0
    
    if queries is None or len(queries) == 0:
        print ("\nInvalid or Bad Query File. Exiting Evaluation module\n")
        sys.exit
    for q_num in queries:  
        q_string =  queries[q_num]['parsed']

        res = search(es_index, system_id, q_string, max_hits)
        if int(res['hits']['total']) == 0:
            f_out.write(str(q_num) + " " + "1 NO_HIT -1 1.0 STANDARD\n")
            f_nohit.write(str(q_num) + '\t' + queries[q_num]['parsed'] + '\n')
        else:
            #normalize_scores(res)
            for each_doc in res['hits']['hits']:
                f_out.write(str(q_num) + " " + "1" + " " + each_doc['_id'] + " " + "-1" + " " + str(each_doc['_score']) + " " + "STANDARD" + "\n")
                returned_total += 1
                
        if verbose >= 1:
            # write search results output to json
            res['hits']['query_parsed'] = queries[q_num]['parsed']
            res['hits']['query_original'] = queries[q_num]['original']
            res['hits']['query_id'] = str(q_num)
            res_list.append(res['hits'])
        
        if run_official_AQWV:
        #Create a query file for this qID
            with open(os.path.join(SYSTEM_OUT_FILES, 'q-' + str(q_num) + '.tsv'), 'w') as f:
                f.write(str(q_num) + '\t' + queries[q_num]['original'] + '\n')
                for each_doc in res['hits']['hits']:
                    f.write(each_doc['_id'] + '\t' + "{0:.3f}".format(each_doc['_score']) + '\n')


    print("Total returned hits from all %d queries: %d" %(len(queries), returned_total))
    f_nohit.write("# Total returned hits from all %d queries: %d\n" %(len(queries), returned_total))
    f_out.close()
    f_nohit.close()

    
    if verbose >= 1:
        JSON_OUT = os.path.join(output_path, "search_output.json")
        with open(JSON_OUT,'w', encoding='utf-8') as json_out:
            json.dump(res_list, json_out, indent=2)
            json_out.close()
    
    # special condition: if reference_file is the string 'NO_REFERENCE', don't run anything else.
    if reference_file != 'NO_REFERENCE':
        compute_AQWV(reference_file, SEARCH_OUT, N_total, max_hits)
    else:
        print("NO_REFERENCE is specified. Packaging results to be run on NIST server here...")
        tar_command = "cd %s; tar -czvf ../%s-%s.tgz *.tsv" % (SYSTEM_OUT_FILES, es_index, system_id)
        subprocess.call(tar_command, shell=True, stdout=subprocess.DEVNULL)       
        print("%s/%s-%s.tgz" %(output_path, es_index, system_id))
        
    if (run_official_AQWV and (reference_file != 'NO_REFERENCE')):
        #Create <answerkeyfile> , default setting task to CLIR
        create_DocumentList(output_path, dataset_name, es_index)
        compute_AQWV_official(output_path, dataset_name, reference_file, queries)
    
        


if __name__ == '__main__':
    USAGE = '\nUSAGE : python eval_AQWV.py <config-file> \n'
    
    if len(sys.argv) != 2:
        print (USAGE)
        sys.exit()
    
    parser = SafeConfigParser({'output_path' : os.getcwd()})
    parser.read(sys.argv[1])
    
    if not (parser.has_option('Evaluation', 'query_file') or
            parser.has_option('Evaluation', 'reference_file') or
            parser.has_option('Indexer', 'system_id') or
            parser.has_option("Indexer", 'index')):
        print ("Invalid/Incomplete Evaluation parameters in config file")
        sys.exit()

    query_file = parser.get('Evaluation', 'query_file')
    reference_file = parser.get('Evaluation', 'reference_file')
    output_path = parser.get('Evaluation', 'output_path')
    system_id = parser.get('Indexer', 'system_id')
    es_index = parser.get('Indexer', 'index')
    dataset_name = parser.get('Indexer', 'dataset_name')
    max_hits = int(parser.get('Evaluation', 'max_hits'))
    run_official_AQWV = parser.getboolean('Evaluation', 'run_official_AQWV')
    verbose = int(parser.get('Evaluation', 'verbose'))

    #Import elastic4clir custom search module
    mod = importlib.import_module('search')
    search_func = getattr(mod, 'search')   

    eval_AQWV(query_file, reference_file, output_path, search_func, es_index, system_id, dataset_name, max_hits, run_official_AQWV, verbose)
