#!/bin/bash
#iservice httpd reload > /var/log/restartapache.out 2>&1
cd /var/www/test/csv2_ai_analysis/
rsync -avz . /var/www/csv2_ai_analysis/

