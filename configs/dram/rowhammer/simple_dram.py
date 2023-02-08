from m5.objects import *
import m5

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "4GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = 'timing'

system.generator = PyTrafficGen()

class DRAM_TEST(DDR4_2400_16x4):
    ranks_per_channel = 1


system.mem_ranges = [AddrRange('256MB')]

system.mem_ctrl = MemCtrl()

system.mem_ctrl.dram = DRAM_TEST(range=system.mem_ranges[0])
#system.mem_ctrl.command_window = '2ns'
#system.mem_ctrl.nvm = HBM_2000_4H_1x128(range=system.mem_ranges[1])




#system.mem_ctrl.dram.tREFI = "2000"
#system.mem_ctrl.nvm.tREFI = "2000"
#system.mem_ctrl.dram.read_buffer_size = "256"

# comment one of these policies
#system.mem_ctrl.mem_sched_policy = "frfcfs"
#system.mem_ctrl.mem_sched_policy = "fcfs"

system.mem_ctrl.port = system.generator.port


def createRandomTraffic(tgen):
    yield tgen.createRandom(10000000,   # duration
                            0,              # min_addr
                            AddrRange('256MB').end,              # max_adr
                            64,             # block_size
                            1000,          # min_period
                            1000,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)

def createLinearTraffic(tgen):
    yield tgen.createLinear(10000000,   # duration
                            0,              # min_addr
                            AddrRange('3kB').end,  # max_adr
                            64,             # block_size
                            1000,          # min_period
                            1000,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)


root = Root(full_system=False, system=system)

m5.instantiate()
system.generator.start(createLinearTraffic(system.generator))
exit_event = m5.simulate()

