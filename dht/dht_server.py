from flask import Flask, redirect, url_for, request, logging, abort, render_template
import os
import requests
from dht.dht import DHTNode
import redis

app = Flask(__name__, static_folder="../visualize/dist", static_url_path="")
m = 10
node = None

@app.before_first_request
def startup():
  global node
  addr = app.config['SERVER_NAME']
  redis_db = redis.StrictRedis(host=app.config["HOST"], port=int(app.config["REDIS_PORT"]))
  node = DHTNode(addr, m, redis_db)
  try:
    print("Pinging db..")
    node.redis_db.ping()
  except redis.exceptions.ConnectionError:
    print("Cannot start redis instance on port {0}. Shutting down\n".format(app.config["REDIS_PORT"]))
    shutdown()
  if app.config['FLUSH']:
    node.redis_db.flushall()
  print("This server's id is {0}".format(node.id))

@app.route('/shutdown', methods=["GET"])
def shutdown():
  func = request.environ.get('werkzeug.server.shutdown')
  if func is None:
    raise RuntimeError('Not running with the Werkzeug Server')
  func()
  return "ok", 200

@app.route('/', methods=['GET'])
def ping():
  """
  Returns when the server is ready.
  """
  return ''

@app.route('/dht/flush', methods=['POST'])
def flush():
  node.redis_db.flushall()
  return "ok", 200

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
  path = list(map(int, path))
  key = node.get_hash(key)
  return render_template('visualize.html', m=m, peers=p, key=key, path=path)

@app.route('/db/path/<key>', methods=['GET'])
def get_key_path(key):
  val = node.get_key(key)
  succ = node.get_successor()
  if val or succ == node.host:
    return str(node.id)
  path = [str(node.id)]
  h = node.get_hash(key)
  if DHTNode.between_right_inclusive(h, node.get_hash(node.get_predecessor()), node.id):
    return "\n".join(path)
  succ_id = node.get_hash(succ)
  if DHTNode.between_right_inclusive(h, node.id, succ_id):
    path.append(str(succ_id))
    return "\n".join(path)
  addr = node.closest_preceding_node(h)
  if addr == node.host:
    return "\n".join(path)
  url =  "http://" + addr + url_for('get_key_path', key=key)
  r = requests.get(url)
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
  k = [s.decode() for s in node.redis_db.keys()]
  return "\n".join(k)

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
  if DHTNode.between_right_inclusive(h, node.get_hash(node.get_predecessor()), node.id):
    return ""
  succ = _find_successor(node, h)
  if succ == node.host:
    return ""
  if succ:
    url = "http://" + succ + url_for('get', key=key)
    res = requests.get(url)
    if res.status_code != 200:
      return abort(404)
    return res.text, 200
  return abort(404)

@app.route('/db/<key>', methods=['POST', 'PUT'])
def put(key):
  """
  Inserts the key into the DHT. The value is equal to the body of the HTTP
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


@app.route('/db/hash/<hash>', methods=['POST', 'PUT'])
def put_hash(hash):
  """
  Inserts the hash into the DHT. This is for transfering keys
  """
  node.redis_db.set(hash, request.data.decode())
  return "ok", 200

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
  if DHTNode.between_right_inclusive(h, node.get_hash(node.get_predecessor()), node.id):
    return "non existent", 200
  succ = _find_successor(node, h)
  if succ == node.host:
    return "non existent", 200
  if succ:
    url = "http://" + succ + url_for('delete', key=key)
    res = requests.delete(url)
    if res.status_code != 200:
      return abort(404)
    return res.text, 200
  return abort(404)

@app.route('/db/transfer', methods=['POST'])
def transfer():
  addr = request.args.get('addr')
  keys = [s.decode() for s in node.redis_db.keys()]
  for key in keys:
    if not DHTNode.between_right_inclusive(int(key), node.get_hash(addr), node.id):
      ok = node.transfer(int(key), addr)
      if not ok:
        abort(404)
  return "updated", 200

@app.route('/dht/peers', methods=['GET'])
def peers():
  """
  Returns the names of all peers that form this DHT in plain text separated by and a new line:
    <peer1>\n<peer2>\n
  """
  peers = []
  peers.append(node.host)
  succ = node.get_successor()
  curr = node.host
  while succ != curr and succ != peers[0]:
    peers.append(succ)
    url = "http://{0}/dht/get_successor".format(succ)
    r = requests.get(url)
    if r.status_code == 200:
      curr = succ
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
  succ = node.get_successor()
  while succ != curr and node.get_hash(succ) != int(peers[0]):
    peers.append(str(node.get_hash(succ)))
    url = "http://{0}/dht/get_successor".format(succ)
    try:
      r = requests.get(url)
      if r.status_code == 200:
        curr = succ
        succ = r.text
      else:
        return abort(404)
    except Exception:
      return abort(404)
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
    return abort(404)

@app.route('/dht/leave', methods=['GET'])
def leave():
  """
  Leave the current DHT. This request should only retrn the DHT this node
  is leaving has stabilized and this node is a standalone node now; noop is
  not part of any DHT.
  """
  ok = node.leave()
  if not ok:
    return abort(404)
  shutdown()
  return "ok", 200

@app.route('/dht/get_successor', methods=['GET'])
def get_successor():
  return node.get_successor()

@app.route('/dht/find_successor', methods=['GET'])
def find_successor():
  id = int(request.args.get('id'))
  return _find_successor(node, id)

@app.route('/dht/get_predecessor', methods=['GET'])
def get_predecessor():
  return node.get_predecessor()

@app.route('/dht/set_successor', methods=['POST', 'PUT'])
def set_successor():
  addr = request.args.get('addr')
  node.update_successor(addr)
  return "ok", 200

@app.route('/dht/set_predecessor', methods=['POST', 'PUT'])
def set_predecessor():
  addr = request.args.get('addr')
  node.update_predecessor(addr)
  return "ok", 200

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
  succ = node.get_successor()
  if node.host == succ:
    return node.host
  if DHTNode.between_right_inclusive(id, node.id, node.get_hash(succ)):
    return succ
  url = "http://{0}/dht/closest_preceding_node?id={1}".format(succ, id)
  r = requests.get(url)
  n0 = r.text
  url =  "http://{0}/dht/find_successor?id={1}".format(n0, id)
  res = requests.get(url)
  return res.text
    
