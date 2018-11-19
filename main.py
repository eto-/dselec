#!/usr/bin/env python3.6
import configparser as cp
import numpy as np
import matplotlib.pyplot as plt
import sys
from sipm import SiPM
from wav import WAV
import cProfile

class Main:
    def __init__(self, input=None, output=None):
        self.c = cp.ConfigParser()
        self.c.read('config.ini')
        self.c['__current__'] = dict(self.c.items(self.c['base'].get('daq', 'daq')) + 
                                     self.c.items(self.c['base'].get('sipm', 'sipm')) +
                                     self.c.items(self.c['base'].get('arma', 'arma')))

        if output is not None:
            self.c['__current__']['file'] = output
            self.o = WAV(c['__current__'])
        else: self.o = WAV()
        
        if self.c.has_option('base', 'seed'): np.random.seed(int(self.c['base']['seed']))

        self.s = SiPM(self.c['__current__'])

        self.v_sum = []
        self.v_max = []
        self.v_sd = []

    def test_loop(self, n, npe=1, noises=True, rate=100):
        bs = float(self.c['__current__']['baseline'])
        for i in range(0, n):
            self.s.pe_list.clear()

            if npe < 0: self.s.add_pes(np.zeros(-npe))
            elif npe > 0: self.s.add_pes(np.random.exponential(1.5e-6, np.random.poisson(npe)))
 
            if noises: self.s.add_dcr()

            self.s.trigger()

            if noises: self.s.add_noises()

            w = self.s.wav()

            self.v_sum.append(np.sum(w) - bs * w.size)
            self.v_max.append(np.max(w))
            self.v_sd.append(np.std(w))

            self.o.write(np.random.exponential(1/rate), w)


m = Main(None, None)
m.test_loop(5000, 1, True)
#cProfile.run('m.test_loop(5000, 100, True)')

k = np.mean(m.v_sum)

print("mean=%.2f sd=%.2f r=%.2f" % (np.mean(m.v_sum), np.std(m.v_sum), np.mean(m.v_sum)/np.std(m.v_sum)))
#print("mean2=" + str(np.mean(v2)))

#plt.plot(w)
#plt.ylabel('waveform [bins]')
#plt.xlabel('time [samples]')
#plt.show()
