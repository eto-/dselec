#!/usr/bin/env python3
import numpy as np
from config import Config
from sipm import SiPM
from wav import WAV
from fil import FIL
import cProfile

class Main:
    def __init__(self):
        self.c = Config()

        self.o = WAV(self.c())
        self.i = FIL(self.c())
        self.s = tuple(SiPM(self.c(), i) for i in range(int(self.c()['n_channels'])))

    def loop(self):
        n_max = int(self.c().get('ev_max', '10000000'))
        n = 0
        for ev in self.i:
            if n >= n_max: break

            for s in self.s: s.pe_list.clear()

            for pe in ev:
                self.s[pe.id].add_pes(pe.t)

            for s in self.s:
                s.add_noises()
                if s.trigger(): s.wav()

            n = n + 1



m = Main()
#m.loop()

cProfile.run("m.loop()")
#print("mean2=" + str(np.mean(v2)))

#plt.plot(w)
#plt.ylabel('waveform [bins]')
#plt.xlabel('time [samples]')
#plt.show()
