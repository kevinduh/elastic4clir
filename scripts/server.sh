#!/bin/bash
#
# Convenience script for managing ElasticSearch server

if [ $# -ne 1 ]; then
    echo "Usage: server.sh command={start,stop,clean,status}"
    echo "  start: start the ElasticSearch server"
    echo "  stop:  stop the ElasticSearch server"
    echo "  clean: clean/delete ElasticSearch indices"
    echo "  status: show status of ElasticSearch server"
    exit
fi

version=5.6.3
endpoint="http://localhost:9200"

if [ $1 == 'start' ]; then
   echo "Starting ElasticSearch server"
   ./elasticsearch-${version}/bin/elasticsearch -d
   echo "PID: " `jps | grep Elasticsearch`

elif [ $1 == 'stop' ]; then
    es_pid=`jps | grep Elasticsearch | cut -f 1 -d ' '`
    echo "Stopping ElasticSearch server with PID:" $es_pid
    if [ -n "$es_pid" ]; then
       kill $es_pid
    fi

elif [ $1 == 'clean' ]; then
    echo "Cleaning ElasticSearch index"
    curl -XDELETE "${endpoint}/*"

elif [ $1 == 'status' ]; then
    echo "Current ElasticSearch server status:"
    curl "${endpoint}/_cat/indices?v"
    
else
    echo "Command unknown."
    echo "Usage: server.sh command={start,stop,clean,status}"
fi
