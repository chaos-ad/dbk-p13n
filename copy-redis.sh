#!/bin/bash

source_host=customer-recs.qxlul7.ng.0001.euw1.cache.amazonaws.com
source_port=6379
source_db=0
target_host=localhost
target_port=6379
target_db=0

redis-cli -h $source_host -p $source_port -n $source_db KEYS \* | \
	while read key; \
		do echo "Copying $key"; \
		redis-cli --raw -h $source_host -p $source_port -n $source_db DUMP "$key" \
			| head -c -1 \
			| redis-cli -x -h $target_host -p $target_port -n $target_db RESTORE "$key" 0;
	done
