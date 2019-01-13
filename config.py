import numpy as np
import configparser as cp
import sys, getopt, re

class Config:
    def __init__(self, i=1, o=1): # 1 = mandatory, -1 = optional, 0 = absent
        c = self.__argv(i, o);

        if i == 1 and not 'i' in c.keys():
            print('input file is mandatory')
            self.__help(1, i, o)

        if o == 1 and not 'o' in c.keys():
            print('output file is mandatory')
            self.__help(1, i, o)

        self.__cp(c)
        
    def __call__(self): return self.c['__current__']
    def all(self): return self.c

    def __argv(self, i, o):
        r = { 'p' : [], 'c' : 'config.ini' }

        try:
            s = 'hc:p:'
            if i: s += 'i:'
            if o: s += 'o:'
            opts, args = getopt.getopt(sys.argv[1:], s)
        except getopt.GetoptError:
            self.__help(2, i, o)

        for opt, arg in opts:
            if opt == '-h': self.__help(0, i, o)
            elif opt == '-p': r['p'].append(arg)
            else: r[opt[1]] = arg

        return r

    def __help(self, n, i, o):
        s = ' '
        if i: 
            if i > 0: s += 'i:'
            else: s += '[i:]'
        if o: 
            if o > 0: s += 'o:'
            else: s += '[o:]'
        s = re.sub('\]\[', "", s + '[c:p:h]')

        print(sys.argv[0] + s)
        if i: print(' -i          input file (fil format)')
        if o: print(' -o          output file (wav format), none for nothing')
        print(' -c file     configuration file (default config.ini)')
        print(' -p s:n:v    configuration option in section s, name n, value v (in case of spaces quotes are needed)')
        print(' -h          this help')
        sys.exit(n);

    def __cp(self, opts):
        self.c = cp.ConfigParser()
        self.c.read(opts['c'])

        for i in opts['p']:
            v = i.split(':')
            self.c[v[0]][v[1]] = v[2]


        self.c['__current__'] = dict(self.c.items('base') + 
                                     self.c.items(self.c['base'].get('detector', 'ds20k')) + 
                                     self.c.items(self.c['base'].get('daq', 'daq')) + 
                                     self.c.items(self.c['base'].get('sipm', 'sipm')) +
                                     self.c.items(self.c['base'].get('arma', 'arma')))

        if 'i' in opts.keys(): self.c['__current__']['input'] = opts['i']
        if 'o' in opts.keys(): 
            self.c['__current__']['output'] = opts['o']
        else:
            self.c['__current__']['output'] = 'none'


        if self.c.has_option('base', 'seed'): np.random.seed(int(self.c['base']['seed']))


