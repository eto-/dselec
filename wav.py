import wave as wav
import numpy as np

class WAV:
    def __init__(self, conf = None):
        if conf is None:
            self.dummy = True
            return

        self.dummy = False
        self.file = wav.open(conf['file'], 'wb')
        self.file.setnchannels(1)
        self.file.setsampwidth(2)
        self.file.setframerate(int(float(conf['sampling'])/1e6))
        self.file.setcomptype('NONE', 'not compressed')
        self.counter = 0
        self.cumulative_t = 0

    def __del__(self):
        if not self.dummy:
            self.file.close()

    def write(self, t, w):
        if self.dummy: return

        self.cumulative_t += t
        self.counter += 1

        t = int(self.cumulative_t / 8e-9) % 0xFFFFFFFF
        #uint16_t marker, header_length;
        f = b''.join([wav.struct.pack('H', i) for i in [0xffff, 20]])
        #uint32_t counter, time_tag, n_samples, cpu_time_ms, n_channels, unused[4];
        f = f + b''.join([wav.struct.pack('I', i) for i in [self.counter, t, w.size, int(round(self.cumulative_t * 1e3)), 1, 0, 0, 0, 0]])
        #uint16_t samples[0];
        f = f + b''.join([wav.struct.pack('h', i) for i in w])

        self.file.writeframes(f)


