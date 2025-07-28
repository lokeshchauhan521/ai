#!/usr/bin/env bash
chmod 777 /usr/src/app/logs -R
ln -sf /dev/stdout /usr/src/app/logs/app.log
#source env/bin/activate
export FLASK_APP=app.py
bash /srv/profile-prod.sh 
/usr/local/bin/supervisord