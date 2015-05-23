#! /usr/bin/python
#
# hyperion.py
# receive commands from the android hyperion app
#
# 2014 (c) juewei@fabfolk.com
# Apply GPLv2.0 or ask.
#


import socket, select, sys, json

HOST = ''   	# Symbolic name, meaning all available interfaces
PORT = 19444	# Hyperion port

class server:

  def __init__(self):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    #Bind socket to local host and port
    try:
        server.bind((HOST, PORT))
    except socket.error as msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()

    server.listen(5)

    ss = {}
    ss[server.fileno()] = server
    self.server = server
    self.ss = ss
    self.verbose = 0

  def poll(self):
    data = None
    r = select.select(self.ss.values(), [], [], 0)[0]
    for s in r:
        if s == self.server:
            conn, addr = s.accept()
	    if self.verbose:
                print 'Connected with ' + addr[0] + ':' + str(addr[1])
	    self.ss[conn.fileno()] = conn
	else:
	    data = s.recv(256)
	    if not data:
	        del(self.ss[s.fileno()])
	        if self.verbose:
                    print 'Closing fd=' + str(s.fileno())
		s.close()
	    else:
	    	s.send("{\"success\": true}\n")
    self.data = data
    return data 

  def json(self, data=None):
    """
     expected json format:
     {"command":"color","priority":50,"color":[99,0,28],"duration":14400000}
    """
    if data is None: data = self.data
    try:
      j = json.loads(data)
    except Exception as e:
      if self.verbose:
          print "%s: bad json: '%s'\n" % (e, data)
      return None
    return j

  def color(self, data=None):
    d = self.json(data)
    if d:
      if d.has_key('color'):
        return d['color']
      else:
        if self.verbose:
          print "unknown json command: %s" % data
    return None

  def duration(self, data=None):
    d = self.json(data)
    if d:
      if d.has_key('duration'):
        return d['duration']
    return 0


if __name__ == '__main__':
    hyp = server()
    hyp.verbose = 1

    import time

    while 1:
	if (hyp.poll()): 
	  rgb = hyp.color()
	  if rgb:
	    print "r=%d, g=%d, b=%d" % (rgb[0], rgb[1], rgb[2])
	time.sleep(0.2)
	print >> sys.stderr, ".",

