#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import sys
from config import Config
from sipm import SiPM
from wav import WAV
import cProfile

class Main:
    def __init__(self):
        self.c = Config(0, -1)

        self.o = WAV(self.c())
        self.s = SiPM(self.c(), 33)


    def test_loop(self, n, npe=1, noises=True, write=True):
        bs = float(self.c()['baseline'])
        v_sum = []
        v_max = []
        v_sd = []
        for i in range(n):
            self.s.pe_list.clear()

            if npe < 0: self.s.add_pes(np.zeros(-npe), noises)
            elif npe > 0: self.s.add_pes(np.random.exponential(1.5e-6, np.random.poisson(npe)), noises)
            
            if noises: self.s.add_dcr()

            self.s.trigger(not noises)

            w = self.s.wav()

            v_sum.append(np.sum(w.wav) - bs * w.wav.size)
            v_max.append(np.max(w.wav))
            v_sd.append(np.std(w.wav))

            if (write): self.o.write(None, [w])

        with open('peak_%.1f_%s.txt' % (npe, noises), 'w') as f: 
            for i in v_sum: 
                f.write("%d\n" % i)
        return [np.mean(v_sum), np.std(v_sum), np.mean(v_max), np.mean(v_sd)]



m = Main()

it = 5000
spe = m.test_loop(it, -1, True, False)
spe2 = m.test_loop(it, -1, False, False)
print("SPE mean charge = %.2f (with noise = %.2f <-> %.2f) with sd = %.2f (spread = %.2f)" % (spe2[0], spe[0], spe[0]/spe2[0], spe[1], spe[1]/spe2[0]))
spe[0] = spe2[0]

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
