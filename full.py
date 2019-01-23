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

            for s in self.s: s.clear()

            if ev is not None:
                for pe in ev.pes:
                    self.s[pe.id].add_pes(pe.t)

            w = []

            for s in self.s:
                s.add_dcr()
                if s.trigger(): w.append(s.wav())

            self.o.write(ev, w)

            n = n + 1



m = Main()

if m.c.all()['base'].getboolean('profile'): cProfile.run("m.loop()")
else: m.loop()
