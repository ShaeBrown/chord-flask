from argparse import ArgumentParser
from dht import dht_server

if __name__ == '__main__':
  parser = ArgumentParser(
    description='PiplineDHT -- A simple distributed hash table')
  parser.add_argument('-k', '--host', action='store', default='localhost.localdomain',
                      help='hostname to bind to')
  parser.add_argument('-p', '--port', action='store', type=int,
                      required=True, help='port to bind to')
  parser.add_argument('-r', '--redis_port', action='store', type=int,
                      required=True, help='port for redis')
  parser.add_argument('-f', '--flush', action='store_true',
                      default=False, help="Flush the db for testing")

  args = parser.parse_args()
  dht_server.app.config["SERVER_NAME"] = "{0}:{1}".format(args.host, args.port)
  dht_server.app.config['REDIS_PORT'] = args.redis_port
  dht_server.app.config['HOST'] = args.host
  dht_server.app.config['FLUSH'] = args.flush
  dht_server.app.run(host=args.host, port=args.port)