import configparser
from sipm import SiPM

c = configparser.ConfigParser()
c.read('config.ini')

c['__sipm__'] = dict(c.items(c['base'].get('daq', 'daq')) + c.items(c['base'].get('sipm', 'sipm')))

s = SiPM(c['__sipm__'])
#a = c.sections()
#print(*a, sep=", ")

s.add_pes([10e-9]) #,100e-9,1000e-9, 1e-3])
s.add_dcr()
s.trigger()
#s.add_noises()

print (*s.pe_list, sep="\n")

#s.wav()
