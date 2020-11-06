from math import ceil, log2
from nmigen import *
from nmigen_soc.wishbone import *

class SimpleOuputPort(Elaboratable, Interface):
    def __init__(self, data_width):
        self.size = 0
        Interface.__init__(self,
                           data_width=data_width,
                           addr_width = ceil(log2(self.size + 1)))
        self.out = Signal(self.data_width)
    
    def elaborate( self, platform ):
        m = Module()
        
        m.d.comb += [
            self.ack.eq(self.stb),
            self.dat_r.eq(self.out),
        ]

        with m.If(self.stb & self.we):
            m.d.sync += [
                self.out.eq(self.dat_w)
            ]
        
        return m

    def ports(self):
        return (self.cyc, self.stb, self.we, self.dat_w, self.ack, self.dat_r)