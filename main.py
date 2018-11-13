#!/usr/bin/env python3.6
import configparser as cp
import numpy as np
import matplotlib.pyplot as plt
import sys
from sipm import SiPM
from wav import WAV
import cProfile

c = cp.ConfigParser()
c.read('config.ini')

c['__current__'] = dict(c.items(c['base'].get('daq', 'daq')) + 
                        c.items(c['base'].get('sipm', 'sipm')) +
                        c.items(c['base'].get('arma', 'arma')))

c['__current__']['file'] = sys.argv[1]
s = SiPM(c['__current__'])
o = WAV(c['__current__'])

np.random.seed(int(c['base']['seed']))

#a = c.sections()
#print(*a, sep=", ")

def loop(n):
    for i in range(0, n):
        #s.add_pes(np.random.uniform(0, 17e-6, 10)) 
        s.add_pes(0)
        s.add_dcr()
        s.trigger()
        s.add_noises()
#        print(*s.pe_list, sep="\n")
        w = s.wav()
        o.write(np.random.exponential(1/30), w)
        s.pe_list.clear()

loop(5000)
#cProfile.run('loop(10000)')
#plt.plot(w)
#plt.ylabel('waveform [bins]')
#plt.xlabel('time [samples]')
#plt.show()
