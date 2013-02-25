#!C:\python23\python.exe

from socket import *
from getopt import *
import os
import sys
import signal
import thread

LOCALPORT = 22222
WWWPORT = 80

psd = 0
csd = 0
wsd = 0

###############################
# Parse HTTP Response Info
###############################
def GetResponseInfo(response):
  return response.find("Content-Type: text/html")

###############################
# Modifying HTTP request header
###############################
def GetModRequest(request):
	tmplines = request.splitlines()
	try:
		tmpaddr = tmplines[0].split('/')
		httpaddr = 'http://' + tmpaddr[2]
		return request.replace(httpaddr, '')
	except IndexError:
		return None
	
##############################
# Termination
##############################
def Terminate(signo, f):
	global psd, csd, wsd
	print 'signal interrupt(%s)' % (signo,)
	if psd : psd.close()
	if csd : csd.close()
	if wsd : wsd.close()
	thread.exit()
	sys.exit(0)

##############################
# Main
##############################
def child(csd, psd, opt):
	#########################
	# From client web browser
	# couldn't send lots of bytes by method POST 
	#request = ''
	#while 1 :
	#	rqt = csd.recv(1024)
	#	request += rqt
	#	if not rqt : break		
	
	request = csd.recv(65536)
	###########################
	# Parse HTTP request header
	tmpheader = request.split()
	tmpurl = tmpheader[1].split('/') 
	try:
		method = tmpheader[0]
		url = tmpheader[1]
		webserver = tmpurl[2]
		version = tmpheader[2]
	except IndexError :
		print 'Bad Request'
		csd.close()
		thread.exit(-1)
		
	if webserver.find(":") >= 0 :
		sport = webserver.split(":")
		onlyserv_addr = sport[0]
		wwwport = int(sport[1])
	else :
		onlyserv_addr = webserver
		wwwport = WWWPORT
	
	########
	# Output
	if (opt & 1)== 1 : 
		print '['+method+'] ['+url+']'

	wsd = socket(AF_INET, SOCK_STREAM)

	try:
		wsd.connect((onlyserv_addr, wwwport))
	except:
		print 'connect: Connection Refused'
		csd.close()
		thread.exit()
	
	###############################
	# Modifying HTTP request header
	mod_request = GetModRequest( request )
	
	if not mod_request:
		print 'request modify error'
		wsd.close()
		csd.close()
		thread.exit()

	########################
	# To Requested webserver
	wsd.send( mod_request )
	if (opt & 2) == 2 :
		print mod_request
	
	response = ''
	while 1 :
		rsp = wsd.recv(1024)
		response += rsp
		if not rsp : break		
	
	#######################
	# To Client web browser
	if GetResponseInfo( response ) >= 0 and (opt & 4 ) == 4 :
		print response
		
	try:
		csd.send( response )
	except socket.error :
		print "socket error"
		wsd.close()
		csd.close()
		thread.exit()
	
	wsd.close()
	csd.close()
	thread.exit()

def usage():
	print """-p [port]
-s : show simplify
-o : show request
-q : show response
"""
	sys.exit(0)

def Proxy(opt, port):
	global psd, csd, wsd
	if port != 0 :
		LOCALPORT = port
	psd = socket(AF_INET, SOCK_STREAM)
	psd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	psd.bind(('', LOCALPORT))
	psd.listen(5)

	while 1:
		csd, caddr = psd.accept()
		thread.start_new(child, (csd,psd,opt))
		#csd.close()

if __name__ == '__main__' :
	try:
		options, argument = getopt(sys.argv[1:], "p:oqs")
	except:
		usage()

	signal.signal(signal.SIGINT, Terminate)
		
	port = LOCALPORT
	opt = 0
	for option, optarg in options:
		if option == "-p" :
			port = int(optarg)
		elif option == "-s" :
			opt += 1
		elif option == "-q" :
			opt += 2
		elif option == "-o" :
			opt += 4
		else :
			usage()
	Proxy(opt, port)
