from flask import Flask, redirect, url_for, request, logging, abort, render_template
import os
import requests
from dotenv import load_dotenv
from dht.dht import DHTNode

load_dotenv()
app = Flask(__name__, static_folder="../visualize/dist", static_url_path="")
app.secret_key = os.environ["secret_key"]
m = 10
node = None

@app.before_first_request
def startup():
  global node
  addr = app.config['SERVER_NAME']
  node = DHTNode(addr, m)
  print("This server's id is {0}".format(node.id))

@app.route('/', methods=['GET'])
def ping():
  """
  Returns when the server is ready.
  """
  return ''

@app.route('/dht/peers/view', methods=['GET'])
def view_peers():
  p = peers_id().split('\n')
  p = list(map(int, p))
  return render_template('visualize.html', m=m, peers=p)

@app.route('/db/view/<key>', methods=['GET'])
def view_key_path(key):
  p = peers_id().split('\n')
  p = list(map(int, p))
  path = get_key_path(key).split("\n")
  path = list(map(int, p))
  key = node.get_hash(key)
  return render_template('visualize.html', m=m, peers=p, key=key, path=path)


@app.route('/db/path/<key>', methods=['GET'])
def get_key_path(key):
  val = node.get_key(key)
  if val or node.successor == node.host:
    return node.id
  path = [str(node.id)]
  h = node.get_hash(key)
  succ_id = node.get_hash(node.successor)
  if DHTNode.between(h, node.id, succ_id, inclusive=True):
    path.append(str(succ_id))
    return "\n".join(path)
  addr = node.closest_preceding_node(id)
  if addr == node.host:
    return "\n".join(path)
  url =  "http://" + addr + url_for('get_key_path', key=key)
  r = request.get(url)
  if r.status_code != 200:
    return abort(404)
  path += r.text.split("\n")
  return "\n".join(path)

@app.route('/dht', methods=['GET'])
def keys():
  """
  Returns all keys stored on THIS node in plain text separated by a new line:
    <key1>\n<key2>\n...
  """
  return "\n".join(node.table.keys())

@app.route('/db/<key>', methods=['GET'])
def get(key):
  """
  Returns the value for the key stored in this DHT or an empty response
  if it doesn't exist.
  """
  
  val = node.get_key(key)
  if val:
    return val
  h = node.get_hash(key)
  succ = _find_successor(node, h)
  if succ == node.host:
    return ""
  if succ:
    url = "http://" + succ + url_for('get', key=key)
    return redirect(url, code=302)
  return abort(404)

@app.route('/db/<key>', methods=['POST', 'PUT'])
def put(key):
  """
  Upserts the key into the DHT. The value is equal to the body of the HTTP
  request.
  """
  h = node.get_hash(key)
  succ = _find_successor(node, h)
  if succ == node.host:
    node.set_key(key, request.data.decode())
    return "ok", 200
  if succ:
    url = "http://" + succ + url_for('put', key=key)
    res = requests.post(url, data=request.data)
    if res.status_code != 200:
      return abort(404)
    return "ok", 200
  return abort(404)

@app.route('/db/<key>', methods=['DELETE'])
def delete(key):
  """
  Deletes the key from the DHT if it exists, noop otherwise.
  """
  val = node.get_key(key)
  if val:
    node.delete_key(key)
    return "deleted", 200
  h = node.get_hash(key)
  succ = _find_successor(node, h)
  if succ == node.host:
    return "non existent", 200
  if succ:
    url = "http://" + succ + url_for('get', key=key)
    return redirect(url, code=307)
  return abort(404)

@app.route('/dht/peers', methods=['GET'])
def peers():
  """
  Returns the names of all peers that form this DHT in plain text separated by and a new line:
    <peer1>\n<peer2>\n
  """
  peers = []
  peers.append(node.host)
  succ = node.successor
  while succ and succ not in peers: # TODO will there be a circle?
    peers.append(succ)
    url = "http://{0}/dht/get_successor".format(succ)
    r = requests.get(url)
    if r.status_code == 200:
      succ = r.text
    else:
      abort(404)
  return "\n".join(peers)

@app.route('/dht/peers/id', methods=['GET'])
def peers_id():
  """
  Returns the names of all peers in their id form that form this DHT in plain text separated by and a new line:
    <peer1>\n<peer2>\n
  """
  peers = []
  peers.append(str(node.id))
  curr = node.host
  succ = node.successor
  while succ and succ != curr:
    peers.append(str(node.get_hash(succ)))
    url = "http://{0}/dht/get_successor".format(succ)
    r = requests.get(url)
    if r.status_code == 200:
      curr = succ
      succ = r.text
    else:
      abort(404)
      return
  return "\n".join(peers)

@app.route('/dht/join', methods=['POST', 'PUT'])
def join():
  """
  Join a new DHT. At least one node of the DHT that we are joining will
  be present in the request body.
  HTTP request body will look like:
    <name1>:<host1>:<port1>\n<name2>:<host2>:<port2>...
  """
  addrs = request.data.decode().split("\n")
  try:
    for addr in addrs:
      node.join(addr)
    return "ok", 200
  except ConnectionError:
    abort(404)

@app.route('/dht/leave', methods=['GET'])
def leave():
  """
  Leave the current DHT. This request should only retrn the DHT this node
  is leaving has stabilized and this node is a standalone node now; noop is
  not part of any DHT.
  """
  raise NotImplementedError

@app.route('/dht/get_successor', methods=['GET'])
def get_successor():
  if node.successor:
    return node.successor
  return ""

@app.route('/dht/find_successor', methods=['GET'])
def find_successor():
  id = int(request.args.get('id'))
  return _find_successor(node, id)

@app.route('/dht/get_predecessor', methods=['GET'])
def get_predecessor():
  if node.predecessor:
    return node.predecessor
  return node.host

@app.route('/dht/notify', methods=['POST', 'PUT'])
def notify():
  addr = request.args.get('addr')
  updated = node.notify(addr)
  if updated:
    return "predecessor updated", 200
  return "predecessor not updated", 200

@app.route('/dht/closest_preceding_node', methods=["GET"])
def closest_preceding_node():
  id = int(request.args.get('id'))
  return node.closest_preceding_node(id)

def _find_successor(node, id):
  if node.host == node.successor:
    return node.host
  if DHTNode.between(id, node.id, node.get_hash(node.successor), inclusive=True):
    return node.successor
  url = "http://{0}/dht/closest_preceding_node?id={1}".format(node.successor, id)
  r = requests.get(url)
  n0 = r.text
  url =  "http://{0}/dht/find_successor?id={1}".format(n0, id)
  res = requests.get(url)
  return res.text
    
