#!/bin/bash
# NOT IN USE YET
mongodump -h mongo:27017 -d aggregated_historical -o backup
tar -zcvf aggregated_historical$(date +%Y%m%d).tar.gz backup
/bin/bash bin/uploader.sh
rm -rf backup
rm -rf aggregated_historical$(date +%Y%m%d).tar.gz
/bin/bash bin/slack.sh
