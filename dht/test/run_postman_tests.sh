npm list newman || npm install newman
source ../../.venv/bin/activate
telnet localhost.localdomain 5000 || python ../../runserver.py -p=5000 > /dev/null 2>&1 &
telnet localhost.localdomain 5001 || python ../../runserver.py -p=5001 > /dev/null 2>&1 &
telnet localhost.localdomain 5002 || python ../../runserver.py -p=5002 > /dev/null 2>&1 &
telnet localhost.localdomain 5003 || python ../../runserver.py -p=5003 > /dev/null 2>&1 &
newman run dht.postman_collection.json

