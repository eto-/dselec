from enum import Enum
import numpy as np
from scipy.stats import norm
from scipy.signal import lfilter

class SiPM:
    class PE:
        class T(Enum):
            PE = 1
            DCR = 2
            AP = 3
            DICT = 4
            PHCT = 5
        def __init__(self, t, pet, c):
            if not isinstance(t, (int, float)) and not isinstance(pet, SiPM.PE.T): raise NameError('argument error')
            self.pet = pet
            self.t = t
            self.c = c
        def __str__(self):
            return 'PE at %.2e type %s charge %.2f' % (self.t, str(self.pet), self.c)


    class WAV:
        def __init__(self, id, w):
            self.id = id
            self.wav = w


    def __init__(self, conf, id):
        self.id = id
        self.gain, self.tau, self.sigma, self.scale = map(float, (conf['gain'], conf['tau'], conf['sigma'], conf['scale']))

        self.spread = float(conf['spread'])
        self.dcr = float(conf['dcr'])
        self.ap_tau = float(conf['ap-tau'])
        self.ap, self.dict, self.phct = map(float, (conf['ap'], conf['dict'], conf['phct']))
        if not 0 <= self.ap < 1 or not 0 <= self.dict < 1 or not 0 <= self.phct < 1:
            raise ValueError('ap, dict and phct are probabilities in the range [0,1)')


        self.gate, self.pre, self.sampling, self.jitter = map(float, (conf['gate'], conf['pre'], conf['sampling'], conf['jitter']))
        eff = float(conf['eff']); self.thresh = norm.ppf(1 - eff, 1, self.spread) if eff > 0 and self.spread > 0 else 0
        snr = float(conf['snr']); self.noise = self.gain / snr if snr > 0 else 0
        self.ceiling = 2**int(conf['bits'])
        self.baseline = int(conf['baseline'])
        if self.baseline < 4 * self.noise:
            print("warning: baseline value is too small and noise clipping will happen: ensure baseline > 4 gain / noise")

        self.pe_list = []


    def clear(self):
        self.pe_list.clear()


    def add_pes(self, ts, add_noise=True):
        if isinstance(ts, (int, float)): ts = [ ts ]
        for t in ts: 
            self.__add_pe(t, SiPM.PE.T.PE, add_noise)


    def add_dcr(self, start=np.nan):
        if self.dcr > 0:
            if np.isnan(start): start = -self.gate
            n = np.random.poisson((2 * self.gate - start) * self.dcr)
            if n:
                ts = np.random.uniform(start, 2 * self.gate, n)
                for t in ts: self.__add_pe(t, SiPM.PE.T.DCR)


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

        j = np.random.normal(0, self.jitter) if self.jitter > 0 else 0
        for i, o in enumerate(self.pe_list):
            self.pe_list[i].t = o.t - t0 + j

        return True


    def wav(self):
        bin = lambda t: int(t * self.sampling) # truncating to the previous bin, fine corrections done on spot
        skew_b = lambda t, t_b: t * self.sampling - t_b
        tau_b = self.tau * self.sampling

        fill = self.tau * 3
        w = np.zeros(bin(self.gate + fill) + 1)

        if self.tau > 0:
            for pe in self.pe_list: 
                t = pe.t + self.pre + fill
                if 0 < t < self.gate + fill:
                    t_b = bin(t)
                    w[t_b] += pe.c * np.exp(-skew_b(t, t_b) / tau_b)
            w = lfilter([self.scale * self.gain], [1, 1 / tau_b - 1], w)

        if self.sigma > 0:
            s = (1 - self.scale) * self.gain 
            g_b = lambda x: s * np.exp(-0.5 * x * x)
            r_b = range(-bin(self.sigma * 3), bin(self.sigma * 3) + 1)
            for pe in self.pe_list: 
                t = pe.t + self.pre + fill
                if 0 < t < self.gate + fill: 
                    t_b = bin(t)
                    for b in r_b:
                        x = t_b + b
                        if 0 <= x < w.size: 
                            w[x] += pe.c * g_b(b + skew_b(t, t_b))


        w = w[bin(fill):bin(self.gate + fill)] + self.baseline

        if self.noise > 0:
            w += np.random.normal(0, self.noise, w.size)

        w = np.round(w)

        w = np.clip(w, 0, self.ceiling)

        return SiPM.WAV(self.id, w.astype(int))


    @staticmethod
    def poissonian_loop(p): # mean p/(1-p) -- sd = (1-p)/sqrt(mean) => distribution is not poissonian
        def __poissonian_loop():
            r = 1 # 1 to account for this entry
            for i in range(np.random.poisson(p)): 
                r += __poissonian_loop()
            return r
        return __poissonian_loop() - 1 # -1 is required because __poissonian_loop starts from 1


    @staticmethod
    def binomial_loop(p): # mean p/(1-p) -- sd = (1-p)^1.5/sqrt(mean) => distribution is not poissonian
        def __binomial_loop():
            if np.random.uniform() > p:
                return 1
            return 1 + __binomial_loop()
        return __binomial_loop() - 1 # -1 is required because __binomial_loop starts from 1


    def __add_pe(self, t, pet, add_noise = True, c = 1): 
        if self.spread >= 0:
            self.pe_list.append(SiPM.PE(t, pet, c * np.random.normal(1, self.spread)))
        else:
            self.pe_list.append(SiPM.PE(t, pet, c))

        if add_noise:
            self.__add_phct(t, pet, c)
            self.__add_dict(t, pet, c)
            self.__add_ap(t, pet, c)


    def __add_phct(self, t, pet, c):
        if self.phct > 0 and pet != SiPM.PE.T.PHCT: # PHCT of PHCT already accounted
            for i in range(self.poissonian_loop(self.phct)): # phct loop unroll: generate directly poissonian distributed phct from probability
                self.__add_pe(t, SiPM.PE.T.PHCT)


    def __add_dict(self, t, pet, c):
        if self.dict > 0 and pet != SiPM.PE.T.DICT: # DICT of DICT already accounted
            for i in range(self.poissonian_loop(self.dict)): # dict loop unroll: gnerate directly poissonian distributed dict from probability
                self.__add_pe(t, SiPM.PE.T.DICT)


    def __add_ap(self, t, pet, c):
        if self.ap > 0 and self.ap_tau > 0 and pet != SiPM.PE.T.AP: # AP of AP already accounted
            n = self.binomial_loop(self.ap) # ap loop unroll: gnerate directly binomial distributed ap from probability
            for t_ap in 1 / np.random.exponential(1 / self.ap_tau, n): # 1/exp(tau/t) seems closer to the real distribution
                c = 1 - np.exp(-t_ap / self.tau) # at every pe the OV resets and the new charge only depends on the previous pe.
                t += t_ap
                self.__add_pe(t, SiPM.PE.T.AP, True, c)

