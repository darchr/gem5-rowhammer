from m5.objects import *
import m5
import os

class DRAM_TEST(DDR4_2400_8x8):
    ranks_per_channel = 1
    trr_variant = 0
    # not relevant stats
    trr_threshold = 32678
    counter_table_length = 6
    companion_table_length = 6
    rh_stat_dump = False
    half_double_prob = 1e3
    double_sided_prob = 1e5
    device_file = os.path.join(
        os.getcwd(),
        # "device_map.txt"
        # "simple-device-map-prob-15.txt"
        "prob-005.json"
    )


duration = int(1e11)


system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "4GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('1GB')]

system.generator0 = PyTrafficGen()
system.generator1 = PyTrafficGen()
system.generator2 = PyTrafficGen()
system.generator3 = PyTrafficGen()
# system.generator4 = PyTrafficGen()
# system.generator5 = PyTrafficGen()
# system.generator6 = PyTrafficGen()
# system.generator7 = PyTrafficGen()
system.generator8 = PyTrafficGen()

system.mem_ctrl = MemCtrl()

system.mem_ctrl.dram = DRAM_TEST(range=system.mem_ranges[0])

system.membus = L2XBar()

system.membus.cpu_side_ports = system.generator0.port
system.membus.cpu_side_ports = system.generator1.port
system.membus.cpu_side_ports = system.generator2.port
system.membus.cpu_side_ports = system.generator3.port
# system.membus.cpu_side_ports = system.generator4.port
# system.membus.cpu_side_ports = system.generator5.port
# system.membus.cpu_side_ports = system.generator6.port
# system.membus.cpu_side_ports = system.generator7.port

# for testing the victim row

system.membus.cpu_side_ports = system.generator8.port

system.mem_ctrl.port = system.membus.mem_side_ports

def get_data_chunk(row_number, width = 8):
    return row_number * 128

def createLinearTraffic0(tgen):
    yield tgen.createLinear(duration,   # duration
                            AddrRange(str(get_data_chunk(291)) + "kB").end,              # min_addr
                            AddrRange(str(get_data_chunk(291)) + "kB").end,              # max_adr
                            64,             # block_size
                            100,          # min_period
                            100,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)

# 

def createLinearTraffic1(tgen):
    yield tgen.createLinear(duration,   # duration
                            AddrRange(str(get_data_chunk(293)) + "kB").end,             # min_addr
                            AddrRange(str(get_data_chunk(293)) + "kB").end,              # max_adr
                            64,             # block_size
                            100,          # min_period
                            100,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)
    
    

def createLinearTraffic2(tgen):
    yield tgen.createLinear(duration,   # duration
                            AddrRange(str(get_data_chunk(290)) + "kB").end,              # min_addr
                            AddrRange(str(get_data_chunk(290)) + "kB").end,              # max_adr
                            64,             # block_size
                            800000000,          # min_period
                            800000000,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)

# 

def createLinearTraffic3(tgen):
    yield tgen.createLinear(duration,   # duration
                            AddrRange(str(get_data_chunk(294)) + "kB").end,             # min_addr
                            AddrRange(str(get_data_chunk(294)) + "kB").end,              # max_adr
                            64,             # block_size
                            800000000,          # min_period
                            800000000,          # max_period
                            100,             # rd_perc
                            0)              # data_limit
    yield tgen.createExit(0)

# def createLinearTraffic4(tgen):
#     yield tgen.createLinear(duration,   # duration
#                             AddrRange(str(get_data_chunk(8023)) + "kB").end,              # min_addr
#                             AddrRange(str(get_data_chunk(8023) + 7) + "kB").end,              # max_adr
#                             64,             # block_size
#                             2000,          # min_period
#                             2000,          # max_period
#                             100,             # rd_perc
#                             0)              # data_limit
#     yield tgen.createExit(0)

# # 

# def createLinearTraffic5(tgen):
#     yield tgen.createLinear(duration,   # duration
#                             AddrRange(str(get_data_chunk(8025)) + "kB").end,             # min_addr
#                             AddrRange(str(get_data_chunk(8025) + 7) + "kB").end,              # max_adr
#                             64,             # block_size
#                             2000,          # min_period
#                             2000,          # max_period
#                             100,             # rd_perc
#                             0)              # data_limit
#     yield tgen.createExit(0)

# def createLinearTraffic6(tgen):
#     yield tgen.createLinear(duration,   # duration
#                             AddrRange(str(get_data_chunk(8136)) + "kB").end,              # min_addr
#                             AddrRange(str(get_data_chunk(8136) + 7) + "kB").end,              # max_adr
#                             64,             # block_size
#                             2000,          # min_period
#                             2000,          # max_period
#                             100,             # rd_perc
#                             0)              # data_limit
#     yield tgen.createExit(0)

# # 

# def createLinearTraffic7(tgen):
#     yield tgen.createLinear(duration,   # duration
#                             AddrRange(str(get_data_chunk(8138)) + "kB").end,             # min_addr
#                             AddrRange(str(get_data_chunk(8138) + 7) + "kB").end,              # max_adr
#                             64,             # block_size
#                             2000,          # min_period
#                             2000,          # max_period
#                             100,             # rd_perc
#                             0)              # data_limit
#     yield tgen.createExit(0)


# ----- data -----
# def createLinearTraffic8(tgen):
#     yield tgen.createLinear(duration,   # duration
#                             AddrRange('47504kB').end,              # min_addr
#                             AddrRange('47505kB').end,              # max_adr
#                             64,             # block_size
#                             1000000,          # min_period
#                             1000000,          # max_period
#                             100,             # rd_perc
#                             0)              # data_limit
    # yield tgen.createExit(0)

root = Root(full_system=False, system=system)

m5.instantiate()

system.generator0.start(createLinearTraffic0(system.generator0))
system.generator1.start(createLinearTraffic1(system.generator1))
system.generator2.start(createLinearTraffic2(system.generator2))
system.generator3.start(createLinearTraffic3(system.generator3))
# system.generator4.start(createLinearTraffic4(system.generator4))
# system.generator5.start(createLinearTraffic5(system.generator5))
# system.generator6.start(createLinearTraffic6(system.generator6))
# system.generator7.start(createLinearTraffic7(system.generator7))

# system.generator8.start(createLinearTraffic8(system.generator8))
exit_event = m5.simulate()
