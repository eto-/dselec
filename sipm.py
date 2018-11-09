from enum import Enum
import numpy as np
from scipy.stats import norm
from scipy.signal import lfilter

class PET(Enum):
    PE = 1
    DCR = 2
    AP = 3
    DICT = 4

class PE:
    def __init__(self, t, pet, c):
        if not isinstance(t, (int, float)) and not isinstance(pet, PET): raise NameError('argument error')
        self.pet = pet
        self.t = t
        self.c = c

    def __str__(self):
        return "PE at " + "{:.2e}".format(self.t) + " type " + str(self.pet) + " charge " + "{:.2f}".format(self.c)

class SiPM:
    def __init__(self, conf):
        self.gain = float(conf['gain'])
        self.spread = float(conf['spread'])
        self.tau = float(conf['tau'])
        self.dcr = float(conf['dcr'])
        self.ap = float(conf['ap'])
        self.ap_tau = float(conf['ap-tau'])
        self.dict = float(conf['dict'])

        self.thresh = norm.ppf(1-float(conf['eff']), 1, self.spread) * self.gain
        self.gate = float(conf['gate']) 
        self.pre = float(conf['pre'])
        self.sampling = float(conf['sampling'])
        #self.peak_f = norm(0, float(conf['sigma']))

        self.pe_list = []

    def _add_pe(self, t, pet, c = 1): 
        self.pe_list.append(PE(t, pet, c * self.gain * np.random.normal(1, self.spread)))

    def add_pes(self, ts):
        if not isinstance(ts, list): ts = [ ts ]
        for t in ts: 
            self._add_pe(t, PET.PE)

    def add_dcr(self, start=np.nan):
        if self.dcr > 0:
            if np.isnan(start): start = -self.gate
            n = np.random.poisson((2 * self.gate - start) * self.dcr)
            if n:
                ts = np.random.uniform(start, 2 * self.gate, n)
                for t in ts: self._add_pe(t, PET.DCR)

    def trigger(self):
        self.pe_list.sort(key=lambda x: x.t)

        t0 = np.nan
        for pe in self.pe_list:
            if pe.pet == PET.PE or pe.pet == PET.DCR:
                if pe.c > self.thresh:
                    t0 = pe.t
                    break
#                else: print("lost " + str(pe))
#                np.random.sample() < self.eff:

        if np.isnan(t0): 
            self.pe_list.clear()
            return

        for i, o in enumerate(self.pe_list):
            self.pe_list[i].t = o.t - t0 + self.pre


    def add_noises(self):
        if not self.pe_list: return

        if self.dict > 0:
            for pe in self.pe_list:
                if pe.pet == PET.PE or pe.pet == PET.DCR:
                    n = np.random.poisson(self.dict)
                    for i in range(0, n): self._add_pe(pe.t, PET.DICT)

        if self.ap > 0 and self.ap_tau > 0:
            for pe in self.pe_list:
                if pe.pet != PET.AP:
                    if np.random.sample() < self.ap:
                        t = np.random.exponential(self.ap_tau)
                        c = 1 - np.exp(-t / self.tau)
                        self._add_pe(pe.t + t, PET.AP, c)


    def wav(self):
        b = lambda t : int(round(t / self.sampling))
        pre = self.ap_tau * 3
        w = np.zeros(b(self.gate + pre) + 1)
        for pe in self.pe_list: 
            if pe.t > -pre and pe.t < self.gate:
                w[b(pe.t)] += pe.c

        w = lfilter([1], [1, 1 / self.tau - 1], w)

        #[pre:(self.gate + pre)]

        print(w.sum())
        return w






