from struct import unpack, calcsize


HEADER_FMT = '=5ifi'
EVENT_FMT = '=2id17f7i'
PHOTO_ELECTRON_FMT = '=id'
PHOTON_FMT = '=2i4fd'
DEPOSIT_FMT = '=2i5fd'
DAUGHTER_FMT = '=4id7f'
USER_FMT = '=2i2fd'

class PE:
    def __init__(self, l):
        self.id = l[0]
        self.t = l[1]

class HEADER:
    def __init__(self, l):
        self.events = l[0]
        self.run = l[1]
        self.pdg = l[2]
        self.lar_index = l[3]
        self.scintillator_index = l[4]
        self.rate = l[5]
        self.detector_flag = l[6]

class EVENT:
    def __init__(self, event):
        self.id = event[0]
        self.pdg = event[1]
        self.time = event[2]
        self.energy = event[3]
        self.s1_energy, self.s2_energy, self.veto_vis_energy, self.mu_vis_energy = event[4:8]
        self.tpc_dep_energy, self.veto_dep_energy, self.mu_dep_energy = event[8:11]
        self.position = event[11:14]
        self.direction = event[14:17]
        self.center_of_mass = event[17:20]
        self.npe, self.veto_npe, self.mu_npe, self.nph = event[20:24]
        self.ndaughters, self.ndeposits, self.nusers = event[24:27]

class FIL:
    def __init__(self, conf):
        self.file_name = conf['input']
        self.dummy = self.file_name == 'none'
        if self.dummy: return

        self.file = open(self.file_name, "rb")
        self.header = HEADER(self.__get(HEADER_FMT))
        self.n = 0

    def __del__(self):
        if not self.dummy: self.file.close()

    def __io(self, size):
        b = self.file.read(size)
        if len(b) != size:
            raise EOFError
        return b

    def __get(self, fmt, check_size=True):
        size = 0
        if (check_size): size = unpack('i', self.__io(4))[0]
        b = self.__io(calcsize(fmt))
        if (check_size):
            size2 = unpack('i', self.__io(4))[0]
            if (size != size2):
                print(size)
                print(size2)
                assert size == size2

        return unpack(fmt, b)

    def __skip(self, fmt, n):
        if n > 0:
            self.file.seek(calcsize(fmt) * n, 1)

    def read(self):
        if self.dummy: return []

        size = self.__get('i', False)[0]
        event = EVENT(self.__get(EVENT_FMT, False))

        self.__skip(DAUGHTER_FMT, event.ndaughters)
        self.__skip(DEPOSIT_FMT, event.ndeposits)
        self.__skip(USER_FMT, event.nusers)
        self.__skip(PHOTON_FMT, event.nph)
        d = self.__get(PHOTO_ELECTRON_FMT[0] + PHOTO_ELECTRON_FMT[1:3] * event.npe, False)
        event.pes = tuple(PE(d[i * 2:i * 2 + 2]) for i in range(event.npe))

        #for i in range(event.npe):
        #    event.pes[i] = PE(self.__get(PHOTO_ELECTRON_FMT, False))
        self.__skip(PHOTO_ELECTRON_FMT, event.veto_npe)
        self.__skip(PHOTO_ELECTRON_FMT, event.mu_npe)

        size2 = self.__get('i', False)[0]

        assert size == size2

        return event

    def __next__(self):
        if self.dummy: return self.read()

        if (self.header.events > 0 and self.n >= self.header.events):
            raise StopIteration
        self.n = self.n + 1
        try:
            return self.read()
        except EOFError:
            raise StopIteration

    def __iter__(self):
        return self

#for c in FIL({'g4ds' : 'outRun.fil'}):
#    print (len(c))
