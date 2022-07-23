from m5.objects import *
import m5

class DRAM_TEST(DDR4_2400_16x4):
    ranks_per_channel = 1
    rowhammer_threshold = 5



system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "4GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('256MB')]

system.generator1 = PyTrafficGen()
system.generator2 = PyTrafficGen()
system.generator3 = PyTrafficGen()

system.mem_ctrl = MemCtrl()

system.mem_ctrl.dram = DRAM_TEST(range=system.mem_ranges[0])

system.membus = L2XBar()

system.membus.cpu_side_ports = system.generator1.port
system.membus.cpu_side_ports = system.generator2.port
system.membus.cpu_side_ports = system.generator3.port
system.mem_ctrl.port = system.membus.mem_side_ports
system.mem_ctrl.dram.tREFI = "2000s"

#system.mem_ctrl.port = system.generator1.port
#system.mem_ctrl.port = system.generator2.port

def createLinearTraffic1(tgen):
    yield tgen.createLinear(100000000,   # duration
                            AddrRange('128kB').end,              # min_addr
                            AddrRange('132kB').end,              # max_adr
                            64,             # block_size
                            2000,          # min_period
                            2000,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)

def createLinearTraffic2(tgen):
    yield tgen.createLinear(100000000,   # duration
                            AddrRange('384kB').end,             # min_addr
                            AddrRange('386kB').end,              # max_adr
                            64,             # block_size
                            2000,          # min_period
                            2000,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)


def createLinearTraffic3(tgen):
    yield tgen.createLinear(10000000,   # duration
                            0,              # min_addr
                            AddrRange('1kB').end,              # max_adr
                            64,             # block_size
                            1000000,          # min_period
                            1000000,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)


root = Root(full_system=False, system=system)

m5.instantiate()
system.generator1.start(createLinearTraffic1(system.generator1))
system.generator2.start(createLinearTraffic2(system.generator2))
system.generator3.start(createLinearTraffic3(system.generator3))
exit_event = m5.simulate()
