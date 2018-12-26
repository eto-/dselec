#!/usr/bin/env python3
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


    def test_loop(self, n, npe=1, noises=True, rate=100):
        bs = float(self.c['__current__']['baseline'])
        v_sum = []
        v_max = []
        v_sd = []
        for i in range(n):
            self.s.pe_list.clear()

            if npe < 0: self.s.add_pes(np.zeros(-npe))
            elif npe > 0: self.s.add_pes(np.random.exponential(1.5e-6, np.random.poisson(npe)))
            
            if noises: self.s.add_noises()

            self.s.trigger(not noises)

            w = self.s.wav()

            v_sum.append(np.sum(w) - bs * w.size)
            v_max.append(np.max(w))
            v_sd.append(np.std(w))

            self.o.write(np.random.exponential(1/rate), w)

        with open('peak_%.1f_%s.txt' % (npe, noises), 'w') as f: 
            for i in v_sum: 
                f.write("%d\n" % i)
        return [np.mean(v_sum), np.std(v_sum), np.mean(v_max), np.mean(v_sd)]



m = Main(None, None)

it = 5000
spe = m.test_loop(it, -1, True)
spe2 = m.test_loop(it, -1, False)
spe[0] = spe2[0]
print("SPE mean charge = %.2f with sd = %.2f (spread = %.2f)" % (spe[0], spe[1], spe[1]/spe[0]))

it = 50000
n = 1.6
sim = m.test_loop(it, n, True)
print("Simulated %.1f npe (phct = %.1f)" % (n, n * 1/(1 - m.s.phct)))
print("Total npe = %.2f with sd = %.2f (spread = %.2f <-> expected %.2f)" % (sim[0] / spe[0], sim[1] / spe[0], sim[1]/sim[0], np.sqrt(spe[0] / sim[0])))


#cProfile.run("m.test_loop(1000, n, True)")
#print("mean2=" + str(np.mean(v2)))

#plt.plot(w)
#plt.ylabel('waveform [bins]')
#plt.xlabel('time [samples]')
#plt.show()
