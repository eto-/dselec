from enum import Enum
import numpy as np
from scipy.stats import norm
from scipy.signal import lfilter

class PET(Enum):
    PE = 1
    DCR = 2
    AP = 3
    DICT = 4
    PHCT = 5

class PE:
    def __init__(self, t, pet, c):
        if not isinstance(t, (int, float)) and not isinstance(pet, PET): raise NameError('argument error')
        self.pet = pet
        self.t = t
        self.c = c

    def __str__(self):
        return "PE at " + "{:.2e}".format(self.t) + " type " + str(self.pet) + " charge " + "{:.2f}".format(self.c)

class SiPM:
    def __init__(self, conf, id):
        self.id = id
        self.gain = float(conf['gain'])
        self.spread = float(conf['spread'])
        self.tau = float(conf['tau'])
        self.dcr = float(conf['dcr'])
        self.ap = float(conf['ap'])
        self.ap_tau = float(conf['ap-tau'])
        self.dict = float(conf['dict'])
        self.phct = float(conf['phct'])

        self.sigma = float(conf['sigma'])
        self.scale = float(conf['scale'])

        eff = float(conf['eff'])
        self.thresh = 0 if not eff > 0 or not self.spread > 0 else norm.ppf(1 - eff, 1, self.spread)
        self.timing = float(conf['timing'])
        self.gate = float(conf['gate']) 
        self.pre = float(conf['pre'])
        self.sampling = float(conf['sampling'])
        self.baseline = int(conf['baseline'])
        snr = float(conf['snr'])
        self.noise = self.gain / snr if snr > 0 else 0
        self.binning = 1
        self.ceiling = 2**int(conf['bits']) * self.binning

        self.pe_list = []

    def clear(self):
        self.pe_list.clear()

    def add_pes(self, ts):
        if isinstance(ts, (int, float)): ts = [ ts ]
        for t in ts: 
            self.__add_pe(t, PET.PE)


    def trigger(self, skip_threshold = False):
        if not self.pe_list: return

        self.pe_list.sort(key=lambda x: x.t)

        t0 = np.nan
        for pe in self.pe_list:
            if not self.thresh or skip_threshold or pe.c > self.thresh:
                t0 = pe.t
                break
#                else: print("lost " + str(pe))
#                np.random.sample() < self.eff:

        if np.isnan(t0): 
            self.pe_list.clear()
            return False

        r = np.random.normal(0, self.timing)
        for i, o in enumerate(self.pe_list):
            self.pe_list[i].t = o.t - t0 + r

        return True


    def add_noises(self):
        self.__add_dcr()

        if not self.pe_list: return
        self.__add_phct()
        self.__add_dict()
        self.__add_ap()



    def wav(self):
        #b = lambda t: int(np.round(t * self.sampling))
        b = lambda t: int(t * self.sampling)

        fill = self.tau * 3
        w = np.zeros(b(self.gate + fill) + 1)

        if self.tau > 0:
            for pe in self.pe_list: 
                t = pe.t + self.pre + fill
                if 0 < t < self.gate + fill:
                    w[b(t)] += pe.c
            w = lfilter([self.scale * self.gain], [1, 1 / (self.tau * self.sampling) - 1], w)


        if self.sigma > 0:
            s = (1 - self.scale) * self.gain 
            r = range(-b(self.sigma * 3), b(self.sigma * 3) + 1)
            for pe in self.pe_list: 
                t = pe.t + self.pre + fill
                if 0 < t < self.gate + fill: 
                    g = lambda x: s * np.exp(-0.5 * x * x)
                    b_t = b(t)
                    for i in r:
                        x = i + b_t
                        if 0 <= x < w.size: 
                            w[x] += g(x / self.sampling - t)


        w = w[b(fill):b(self.gate + fill)] + self.baseline

        if self.noise > 0:
            w += np.random.normal(0, self.noise, w.size)

        w = np.round(w / self.binning) * self.binning

        w = np.clip(w, 0, self.ceiling)

        return w.astype(int)



    def __add_pe(self, t, pet, c = 1): 
        if self.spread >= 0:
            self.pe_list.append(PE(t, pet, c * np.random.normal(1, self.spread)))
        else:
            self.pe_list.append(PE(t, pet, c))


    def __phct(self):
        r = 0
        for i in range(np.random.poisson(self.phct)): r += self.__phct()
        return r

    def __add_dcr(self, start=np.nan):
        if self.dcr > 0:
            if np.isnan(start): start = -self.gate
            n = np.random.poisson((2 * self.gate - start) * self.dcr)
            if n:
                ts = np.random.uniform(start, 2 * self.gate, n)
                for t in ts: self.__add_pe(t, PET.DCR)

    def __add_phct(self):
        if self.phct > 0:
            for k in range(len(self.pe_list)):
                n = self.__phct()
                for i in range(n): self.__add_pe(self.pe_list[k].t, PET.PECT)

    def __add_dict(self):
        if self.dict > 0:
            for k in range(len(self.pe_list)):
                n = np.random.poisson(self.dict)
                for i in range(n): self.__add_pe(self.pe_list[k].t, PET.DICT)

    def __add_ap(self):
        if self.ap > 0 and self.ap_tau > 0:
            for k in range(len(self.pe_list)):
                if np.random.sample() < self.ap:
                    t = np.random.exponential(self.ap_tau)
                    c = 1 - np.exp(-t / self.tau)
                    self.__add_pe(self.pe_list[k].t + t, PET.AP, c)


