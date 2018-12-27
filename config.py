import numpy as np
import configparser as cp
import sys, getopt

class Config:
    def __init__(self):
        c = self.__argv();

        if not 'o' in c.keys() or not 'i' in c.keys():
            print("input and output files are mandatory")
            self.__help(1)

        self.__cp(c)
        
    def __call__(self): return self.c['__current__']
    def all(self): return self.c

    def __argv(self):
        r = { 'p' : [], 'c' : 'config.ini' }

        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:o:c:p:")
        except getopt.GetoptError:
            self.__help(2)

        for opt, arg in opts:
            if opt == '-h': self.__help()
            elif opt == '-p': r['p'].append(arg)
            else: r[opt[1]] = arg

        return r

    def __help(self, n):
        print(sys.argv[0] + "i:o:[c:p:h]")
        print(" -i          input file (fil format)")
        print(" -o          output file (wav format), none for nothing")
        print(" -c file     configuration file (default config.ini)")
        print(" -p s:n:v    configuration option in section s, name n, value v (in case of spaces quotes are needed)")
        print(" -h          this help")
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

        self.c['__current__']['output'] = opts['o']
        self.c['__current__']['input'] = opts['i']

        if self.c.has_option('base', 'seed'): np.random.seed(int(self.c['base']['seed']))


