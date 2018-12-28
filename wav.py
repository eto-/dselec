import wave as wav
import numpy as np

class WAV:
    def __init__(self, conf):
        self.file_name = conf['output']
        self.dummy = self.file_name == 'none'
        if self.dummy: return

        self.file = wav.open(conf['output'], 'wb')
        self.file.setnchannels(1)
        self.file.setsampwidth(2)
        self.file.setframerate(int(float(conf['sampling'])/1e6))
        self.file.setcomptype('NONE', 'not compressed')
        self.counter = 0
        self.time = 0
        self.rate = float(conf.get('rate', '100'))

    def __del__(self):
        if not self.dummy:
            self.file.close()

    def write(self, e, ws):
        if self.dummy: return

        if e is None:
            self.time += np.random.exponential(1 / self.rate)
            self.counter += 1
        else:
            self.time = e.time
            self.counter = e.id

        data_len = sum(map(lambda w: 4 + w.wav.size, ws))

        time_tag = int(self.time / 8e-9) % 0xFFFFFFFF
        cpu_time_ms = int(round(self.time * 1e3))
        #uint16_t marker, header_length;
        #uint32_t counter, time_tag, n_samples, cpu_time_ms;
        #uint16_t n_channels, version;
        #uint32_t data_length, unused[3]
        f = wav.struct.pack('=2H4I2H4I', *(0xffff, 20, self.counter, time_tag, 0, cpu_time_ms, len(ws), 200, data_len, 0, 0, 0))
        for w in ws:
            #uint16_t channel, n_samples, unused[2];
            f = f + wav.struct.pack('=4H', *(w.id, w.wav.size, 0, 0))
            f = f + wav.struct.pack("=%dh" % w.wav.size, *w.wav)

        self.file.writeframes(f)


