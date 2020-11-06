from math import ceil, log2
from nmigen import *
from nmigen_soc.wishbone import *
from nmigen_soc.memory import *


class RAM(Elaboratable, Interface):
    def __init__(self, data_width, granularity, depth):
        if not granularity:
            granularity = data_width

        self.memories = [
            {
                "memory": memory,
                "read_port": memory.read_port(),
                "write_port": memory.write_port(),
            }
            for memory in (
                Memory(width=granularity, depth=depth)
                for _ in range(0, data_width, granularity)
            )
        ]

        Interface.__init__(
            self,
            data_width=data_width,
            granularity=granularity,
            addr_width=self.memories[0]["read_port"].addr.shape().width,
        )

    def elaborate(self, platform):
        we = Signal()
        m = Module()

        m.d.comb += [
            self.ack.eq(self.stb),
            we.eq(self.stb & self.we),
        ]
        for i, memory in enumerate(self.memories):
            m.submodules += [
                memory["read_port"],
                memory["write_port"],
            ]
            dat_r_slice, dat_w_slice = (
                signal.word_select(i, self.granularity)
                for signal in (self.dat_r, self.dat_w)
            )
            m.d.comb += [
                memory["read_port"].addr.eq(self.adr),
                dat_r_slice.eq(memory["read_port"].data),
                memory["write_port"].addr.eq(self.adr),
                memory["write_port"].data.eq(dat_w_slice),
                memory["write_port"].en.eq(we),
            ]
        return m

    def ports(self):
        # wishbone interface
        ports = [
            self.adr,
            self.dat_w,
            self.dat_r,
            self.sel,
            self.cyc,
            self.stb,
            self.we,
            self.ack,
        ]
        # memory cells
        for memory in self.memories:
            for cell in memory["memory"]:
                ports += [cell]
        return ports
