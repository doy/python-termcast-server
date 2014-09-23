import sys
import termcast_server

server = termcast_server.Server(sys.argv[1])
server.listen()
