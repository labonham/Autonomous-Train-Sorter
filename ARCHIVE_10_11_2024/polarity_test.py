import pigpio 
from time import sleep


outPin = 17;
outPin2 = 27;

savedTurnout = 23;
savedTurnout2 = 22;


def main(args):
	pi = pigpio.pi()
	pi.set_mode(outPin, pigpio.OUTPUT)
	pi.set_mode(outPin2, pigpio.OUTPUT)
	
	pi.set_mode(savedTurnout, pigpio.OUTPUT)
	pi.set_mode(savedTurnout2, pigpio.OUTPUT)   
	try:
		while True:
			pi.write(outPin,1)
			pi.write(outPin2,0)
			pi.write(savedTurnout,1)
			pi.write(savedTurnout2,0)
	except KeyboardInterrupt:
		pi.set_mode(outPin, pigpio.INPUT)
		pi.set_mode(outPin2, pigpio.INPUT) 
		pi.set_mode(savedTurnout, pigpio.INPUT)
		pi.set_mode(savedTurnout2, pigpio.INPUT) 
		pi.write(outPin,0)
		pi.write(outPin2,0)
		pi.write(savedTurnout,0)
		pi.write(savedTurnout2,0)
		

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
