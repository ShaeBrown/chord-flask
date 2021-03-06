# Flask Chord DHT
Implementation of the Chord DHT Peer-to-Peer algorithm using [Flask](http://flask.pocoo.org/).  
Visualization of the network and key retrieval using [D3](https://d3js.org/) 

## Build front end
If you don't have node.js [download here](https://nodejs.org/en/download/)
```
cd visualize
npm install
webpack
```
If you have [yarn](https://yarnpkg.com/en/docs/install), you can use the `yarn` command instead.
You can edit the parameters in [visualize.html](./visualize/visualize.html) to preview how the front end works.
## Build back end
### Install requirements
Ensure you have [python](https://www.python.org/downloads/) installed.  
If you do not have virtualenv installed you can do so by `pip install virtalenv`  
Now you can make a virtual environment and install the requirements:
```
virtualenv .venv
pip install -r requirements.txt
source .venv/bin/activate
```

Install redis
```bash
sudo apt-get install redis-server
```
### Run nodes
Run a redis server for each chord node
```
redis-server --port 6000
redis-server --port 6001
redis-server --port 6002
redis-server --port 6003
```

Now you can initalize each dht server
```
python runserver.py -p=5000 -r=6000
python runserver.py -p=5001 -r=6001
python runserver.py -p=5002 -r=6002
python runserver.py -p=5003 -r=6003
```

### Join nodes
I used [postman](https://www.getpostman.com/apps) to send requests. You can also use [curl](https://curl.haxx.se/download.html)
```bash
curl --location --request PUT "localhost.localdomain:5000/dht/join" \
  --data "localhost.localdomain:5001
localhost.localdomain:5002
localhost.localdomain:5003"
```

### Put key
```bash
curl --location --request PUT "localhost.localdomain:5000/db/keyval" \
  --data "this is the data"
```

### Get key
```bash
curl --location --request GET "localhost.localdomain:5002/db/keyval"
```

## Visualize network
Open in browser:
`localhost.localdomain:5000/dht/peers/view`

This is an example of what a visualization of the peer to peer network would look like:
![peer](./img/peers.png)

## Visualize key path
`localhost.localdomain:5000/db/view/somekey`

This is an example of what a path would look like when trying to find the key
![keypath](./img/keypath.png)

## Run tests
Postman tests can be run by calling this [script](./dht/test/run_postman_tests.sh), which starts all the chord nodes, and redis servers.

Or if you have postman installed: 

[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/ab23f768f73247af8bb0) 

Just make sure there are 5 servers running on port 5000, 5001, 5002, 5003, 5007, each with a redis server

Unit tests can be run using:
```
cd dht
python -m test.dht_node_test
```
