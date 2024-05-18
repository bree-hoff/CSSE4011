import serial
import sys
import os
import time
import numpy as np

from gui_parser import *

configFileName = 'AOP_6m_default.cfg'
CLIport = '/dev/tty.SLAB_USBtoUART'
Dataport = '/dev/tty.SLAB_USBtoUART3'


def main():
   
   parser = UARTParser(type="DoubleCOMPort")
 
   global CLIport, Dataport, configFileName
   parser.connectComPorts(CLIport, Dataport)
   
   with open(configFileName, 'r') as cfg_file:
      cfg = cfg_file.readlines()
   
   parser.sendCfg(cfg)
   sys.stdout.flush()
   while(True):
       output = parser.readAndParseUartDoubleCOMPort()
       if output: 
            point_cloud = output['pointCloud']
            if 'heightData' in output and output['heightData'] is not None:
                height = output['heightData'][0][1]
                print("Estimated Height:{:.2f}".format(height))
                if 0.5 <= height <= 1.9: # experiment with this 
                   print("Crouching")
                else: 
                    print("Not Crouching")
          
    
      


if __name__ == "__main__":
    main()