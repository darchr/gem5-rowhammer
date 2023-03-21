

# This rowhammer pattern was found on a 8GB single rank Vendor A DIMM using
# blacksmith (https://github.com/comsec-group/blacksmith). The DRAM
# specifications are:
#
# ---=== SPD EEPROM Information ===---
# EEPROM CRC of bytes 0-125                        OK (0xBD97)
# # of bytes written to SDRAM EEPROM               384
# Total number of bytes in EEPROM                  512
# Fundamental Memory type                          DDR4 SDRAM
# SPD Revision                                     1.1
# Module Type                                      UDIMM
# EEPROM CRC of bytes 128-253                      OK (0x53D8)

# ---=== Memory Characteristics ===---
# Maximum module speed                             2400 MHz (PC4-19200)
# Size                                             8192 MB
# Banks x Rows x Columns x Bits                    16 x 16 x 10 x 64
# SDRAM Device Width                               8 bits
# Ranks                                            1
# AA-RCD-RP-RAS (cycles)                           17-17-17-39
# Supported CAS Latencies                          18T, 17T, 16T, 15T, 14T, 13T
#                                                  12T, 11T, 10T

# ---=== Timings at Standard Speeds ===---
# AA-RCD-RP-RAS (cycles) as DDR4-2400              17-17-17-39
# AA-RCD-RP-RAS (cycles) as DDR4-2133              15-15-15-35
# AA-RCD-RP-RAS (cycles) as DDR4-1866              13-13-13-30
# AA-RCD-RP-RAS (cycles) as DDR4-1600              11-11-11-26

# ---=== Timing Parameters ===---
# Minimum Cycle Time (tCKmin)                      0.833 ns
# Maximum Cycle Time (tCKmax)                      1.600 ns
# Minimum CAS Latency Time (tAA)                   13.750 ns
# Minimum RAS to CAS Delay (tRCD)                  13.750 ns
# Minimum Row Precharge Delay (tRP)                13.750 ns
# Minimum Active to Precharge Delay (tRAS)         32.000 ns
# Minimum Active to Auto-Refresh Delay (tRC)       45.750 ns
# Minimum Recovery Delay (tRFC1)                   350.000 ns
# Minimum Recovery Delay (tRFC2)                   260.000 ns
# Minimum Recovery Delay (tRFC4)                   160.000 ns
# Minimum Four Activate Window Delay (tFAW)        21.000 ns
# Minimum Row Active to Row Active Delay (tRRD_S)  3.300 ns
# Minimum Row Active to Row Active Delay (tRRD_L)  4.900 ns
# Minimum CAS to CAS Delay (tCCD_L)                5.000 ns
# Minimum Write Recovery Time (tWR)                15.000 ns
# Minimum Write to Read Time (tWTR_S)              2.500 ns
# Minimum Write to Read Time (tWTR_L)              7.500 ns

# ---=== Other Information ===---
# Package Type                                     Monolithic
# Maximum Activate Count                           Unlimited
# Post Package Repair                              One row per bank group
# Soft PPR                                         Supported
# Module Nominal Voltage                           1.2 V
# Thermal Sensor                                   No

# ---=== Physical Characteristics ===---
# Module Height                                    32 mm
# Module Thickness                                 2 mm front, 1 mm back
# Module Reference Card                            A revision 2

# --------------------------------------------------------------------------- #

# The following aggressor addresses were collected from an Intel(R) Core
# i7-7700 machine with a single rank Vendor A DDR4 DRAM DIMM.

# Aggressor 0x203eafc000,row 8023.                                       
# Aggressor 0x203eb24000,row 8025.
# Aggressor 0x2002490000,row 292.
# Aggressor 0x20024d8000,row 294.
# Aggressor 0x201586c000,row 2755.
# Aggressor 0x20158b4000,row 2757.
# Aggressor 0x203f900000,row 8136.
# Aggressor 0x203f948000,row 8138.

# This suggests that the trr_length has to be <= 6 as atleast one single.
# only the row information is important here.
# writing 8 traffic generators for this script.

# utility method
def get_data_chunk(row_number, width = 8):
    return row_number * 128

from m5.objects import *
import m5

duration = int(1e11)

# Configuring the device type and the parameters specified by exeucting
# `decode-dimms`.
class Vendor_A_1R_x8(DDR4_2400_8x8):
    
    ranks_per_channel = 1
    trr_variant = 1
    
    # We don't know these values yet for vendor A.
    companion_threshold = 1024
    trr_threshold = 32768
    rowhammer_threshold = 50000
    counter_table_length = 6
    
    # Set this flag to True if you want to do a post simulation analysis. It is
    # recommended only when simulating full system.
    rh_stat_dump = False
    
    # The device size does not matter as the known good rowhammer patterns were
    # collected on 1 GB huge pages. This is discussed in details in the paper.
    # device_size = "1GiB"
    
    # tCK does not have a MIN and a MAX in gem5. We ignore this parameter and
    # use the devault value.
    
    # The following variables are overridden in this config script.
    tRCD = "13.75ns"
    tRP  = "13.75ns"
    tXAW = "21ns"
    
    # We are not making any changes to the power model.

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
system.generator4 = PyTrafficGen()
system.generator5 = PyTrafficGen()
system.generator6 = PyTrafficGen()
system.generator7 = PyTrafficGen()
system.generator8 = PyTrafficGen()

system.mem_ctrl = MemCtrl()

system.mem_ctrl.dram = Vendor_A_1R_x8(range=system.mem_ranges[0])

system.membus = L2XBar()

system.membus.cpu_side_ports = system.generator0.port
system.membus.cpu_side_ports = system.generator1.port
system.membus.cpu_side_ports = system.generator2.port
system.membus.cpu_side_ports = system.generator3.port
system.membus.cpu_side_ports = system.generator4.port
system.membus.cpu_side_ports = system.generator5.port
system.membus.cpu_side_ports = system.generator6.port
system.membus.cpu_side_ports = system.generator7.port

# for testing the victim row

system.membus.cpu_side_ports = system.generator8.port
system.mem_ctrl.port = system.membus.mem_side_ports


def createLinearTraffic0(tgen):
    yield tgen.createLinear(duration,
                            AddrRange(str(get_data_chunk(292)) + "kB").end,
                            AddrRange(str(get_data_chunk(292) + 7) + "kB").end,
                            64,
                            2000,
                            2000,
                            100,
                            0)
    yield tgen.createExit(0)

# 

def createLinearTraffic1(tgen):
    yield tgen.createLinear(duration,
                            AddrRange(str(get_data_chunk(294)) + "kB").end,
                            AddrRange(str(get_data_chunk(294) + 7) + "kB").end,
                            64,
                            2000,
                            2000,
                            100,
                            0)
    yield tgen.createExit(0)
    
    

def createLinearTraffic2(tgen):
    yield tgen.createLinear(duration,
                            AddrRange(str(get_data_chunk(2755)) + "kB").end,
                            AddrRange(str(get_data_chunk(2755) + 7)+ "kB").end,
                            64,
                            2000,
                            2000,
                            100,
                            0)
    yield tgen.createExit(0)

# 

def createLinearTraffic3(tgen):
    yield tgen.createLinear(duration,
                            AddrRange(str(get_data_chunk(2757)) + "kB").end,
                            AddrRange(str(get_data_chunk(2757) + 7)+ "kB").end,
                            64,
                            2000,
                            2000,
                            100,
                            0)
    yield tgen.createExit(0)

def createLinearTraffic4(tgen):
    yield tgen.createLinear(duration,
                            AddrRange(str(get_data_chunk(8023)) + "kB").end,
                            AddrRange(str(get_data_chunk(8023) + 7)+ "kB").end,
                            64,
                            2000,
                            2000,
                            100,
                            0)
    yield tgen.createExit(0)

# 

def createLinearTraffic5(tgen):
    yield tgen.createLinear(duration,
                            AddrRange(str(get_data_chunk(8025)) + "kB").end,
                            AddrRange(str(get_data_chunk(8025) + 7)+ "kB").end,
                            64,
                            2000,
                            2000,
                            100,
                            0)
    yield tgen.createExit(0)

def createLinearTraffic6(tgen):
    yield tgen.createLinear(duration,
                            AddrRange(str(get_data_chunk(8136)) + "kB").end,
                            AddrRange(str(get_data_chunk(8136) + 7)+ "kB").end,
                            64,
                            2000,
                            2000,
                            100,
                            0)
    yield tgen.createExit(0)

# 

def createLinearTraffic7(tgen):
    yield tgen.createLinear(duration,
                            AddrRange(str(get_data_chunk(8138)) + "kB").end,
                            AddrRange(str(get_data_chunk(8138) + 7)+ "kB").end,
                            64,
                            2000,
                            2000,
                            100,
                            0)
    yield tgen.createExit(0)


# ----- data -----
def createLinearTraffic8(tgen):
    yield tgen.createLinear(duration,
                            AddrRange('37504kB').end,
                            AddrRange('37505kB').end,
                            64,
                            1000000,
                            1000000,
                            100,
                            0)
    yield tgen.createExit(0)

root = Root(full_system=False, system=system)

m5.instantiate()

system.generator0.start(createLinearTraffic0(system.generator0))
system.generator1.start(createLinearTraffic1(system.generator1))
system.generator2.start(createLinearTraffic2(system.generator2))
system.generator3.start(createLinearTraffic3(system.generator3))
system.generator4.start(createLinearTraffic4(system.generator4))
system.generator5.start(createLinearTraffic5(system.generator5))
system.generator6.start(createLinearTraffic6(system.generator6))
system.generator7.start(createLinearTraffic7(system.generator7))

system.generator8.start(createLinearTraffic8(system.generator8))
exit_event = m5.simulate()
