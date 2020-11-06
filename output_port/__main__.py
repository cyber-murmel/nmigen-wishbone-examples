#!/usr/bin/env python3

from nmigen import *
from nmigen.sim import *
from argparse import ArgumentParser
from logging import debug, info, warning, error, basicConfig as logConfig
from logging import DEBUG, INFO, WARNING, ERROR
import random

from .output_port import OuputPort

def parse_arguments():
    parser = ArgumentParser(
        description="Python CLI Template",
        epilog="")
    
    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument("-q", "--quiet",   action="store_true", help="turn off warnings")
    verbose.add_argument("-v", "--verbose", action="count",      help="set verbose loglevel")

    parser.add_argument("--vcd",         type=str, default="/tmp/traces.vcd",         help="path to vcd file")
    parser.add_argument("--gtkw",        type=str, default="/tmp/traces.gtkw",        help="path to gtkw file")
    widths = (8, 16, 32, 64)
    parser.add_argument('--width',       type=int, choices=widths, default=widths[0], help="bus data width")
    parser.add_argument('--granularity', type=int, choices=widths,                    help="bus data granularity")
    parser.add_argument('--loop',        type=int, default=32,                        help="number of test loops to run")
    
    args = parser.parse_args()
    return args

def configure_logging(verbose, quiet):
    log_level = ERROR   if quiet else \
                WARNING if not verbose else \
                INFO    if 1 == verbose else \
                DEBUG   #  2 <= verbose
    logConfig(format="%(asctime)-15s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log_level)
    debug("DEBUG Log Level")

def main(args):
    width = args.width
    granularity = args.granularity if args.granularity else width

    dut = OuputPort(width, granularity)

    def process():
        gran = granularity

        def cycle(data, sel):
            # start cycle
            yield dut.cyc.eq(1)
            yield dut.sel.eq(sel)
            yield dut.dat_w.eq(data)
            yield dut.stb.eq(1)
            yield dut.we.eq(1)
            # wait for ack
            ack = yield dut.ack
            while not ack:
                yield Tick()
                ack = yield dut.ack
            # stop cycle
            yield dut.cyc.eq(0)
            yield dut.sel.eq(0)
            yield dut.dat_w.eq(0)
            yield dut.stb.eq(0)
            yield dut.we.eq(0)
        
        # make reproducible
        random.seed(42)

        while gran <= width:
            n_sel_bits = gran//granularity
            for _ in range(args.loop):
                for sel in range(width//gran):
                    expected = random.randrange(1<<gran)
                    yield from cycle(expected<<(gran*sel), ((1<<n_sel_bits)-1)<<(sel*n_sel_bits))
                    # wait for signal propagation through register
                    yield Tick()
                    # compare
                    actual = yield dut.dat_r.word_select(sel, gran)
                    assert actual == expected
            
            gran <<= 1
    
    sim = Simulator(dut)
    with sim.write_vcd(args.vcd, args.gtkw, traces=dut.ports()):
        # Add a clock to our design
        sim.add_clock(1/25e6)
        # Add 'process' as a testbench process
        sim.add_sync_process(process)
        # Run the simulation
        sim.run()

    info("All tests passed!")
    info("Run `gtkwave {}` to inspect wave forms".format(args.gtkw))

if "__main__" == __name__:
    args = parse_arguments()
    configure_logging(args.verbose, args.quiet)
    main(args)
