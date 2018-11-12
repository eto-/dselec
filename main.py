#!/usr/bin/env python3.6
import configparser as cp
import numpy as np
import matplotlib.pyplot as plt
from sipm import SiPM

c = cp.ConfigParser()
c.read('config.ini')

c['__current__'] = dict(c.items(c['base'].get('daq', 'daq')) + 
                        c.items(c['base'].get('sipm', 'sipm')) +
                        c.items(c['base'].get('arma', 'arma')))

s = SiPM(c['__current__'])
#a = c.sections()
#print(*a, sep=", ")

#s.add_pes(np.random.uniform(0, 17e-6, 10)) 
s.add_pes(0)
s.add_dcr()
s.trigger()
s.add_noises()

print (*s.pe_list, sep="\n")

w = s.wav()
plt.plot(w)
plt.ylabel('waveform [bins]')
plt.xlabel('time [samples]')
plt.show()

