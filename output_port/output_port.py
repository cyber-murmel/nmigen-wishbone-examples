from math import ceil, log2
from nmigen import *
from nmigen_soc.wishbone import *

class OuputPort(Elaboratable, Interface):
    def __init__(self, data_width, granularity=None):
        self.size = 1
        Interface.__init__(self,
                           data_width = data_width,
                           granularity = granularity,
                           addr_width = ceil(log2(self.size + 1)))
        self.out = Signal(self.data_width)
    
    def elaborate( self, platform ):
        m = Module()
        m.d.comb += [
            self.ack.eq(self.stb),
            self.out.eq(self.dat_r),
        ]
        with m.If(self.stb & self.we):
            if self.data_width == self.granularity:
                # select lines can be ignored
                    m.d.sync += [ self.out.eq(self.dat_w) ]
            else:
                for i, sel in enumerate(self.sel):
                    with m.If(sel):
                        dat_r_slice, dat_w_slice = (
                            signal.word_select(i, self.granularity) 
                                for signal in (self.dat_r, self.dat_w))
                        m.d.sync += [ dat_r_slice.eq(dat_w_slice) ]
        return m

    def ports(self):
        return (self.cyc, self.stb, self.sel, self.we, self.dat_w, self.ack, self.dat_r)
