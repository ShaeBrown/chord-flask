npm list newman || npm install newman
source ../../.venv/bin/activate
curl -s 'localhost.localdomain:5000/ping' || python ../../runserver.py -p=5000 -r=6000 > /dev/null 2>&1 &
curl -s 'localhost.localdomain:5001/ping' || python ../../runserver.py -p=5001 -r=6001 > /dev/null 2>&1 &
curl -s 'localhost.localdomain:5002/ping' || python ../../runserver.py -p=5002 -r=6002 > /dev/null 2>&1 &
curl -s 'localhost.localdomain:5003/ping' || python ../../runserver.py -p=5003 -r=6003 > /dev/null 2>&1 &
curl -s 'localhost.localdomain:5007/ping' || python ../../runserver.py -p=5007 -r=6007 > /dev/null 2>&1 &
redis-cli -p 6000 ping || redis-server --port 6000
redis-cli -p 6001 ping || redis-server --port 6001
redis-cli -p 6002 ping || redis-server --port 6002
redis-cli -p 6003 ping || redis-server --port 6003
redis-cli -p 6007 ping || redis-server --port 6007
newman run dht.postman_collection.json

