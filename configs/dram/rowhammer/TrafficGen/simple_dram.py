# Copyright (c) 2021-2023 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from m5.objects import *
import m5

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "4GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = "timing"

system.generator = PyTrafficGen()


class DRAM_TEST(DDR4_2400_16x4):
    ranks_per_channel = 1


system.mem_ranges = [AddrRange("256MB")]

system.mem_ctrl = MemCtrl()

system.mem_ctrl.dram = DRAM_TEST(range=system.mem_ranges[0])
# system.mem_ctrl.command_window = '2ns'
# system.mem_ctrl.nvm = HBM_2000_4H_1x128(range=system.mem_ranges[1])


# system.mem_ctrl.dram.tREFI = "2000"
# system.mem_ctrl.nvm.tREFI = "2000"
# system.mem_ctrl.dram.read_buffer_size = "256"

# comment one of these policies
# system.mem_ctrl.mem_sched_policy = "frfcfs"
# system.mem_ctrl.mem_sched_policy = "fcfs"

system.mem_ctrl.port = system.generator.port


def createRandomTraffic(tgen):
    yield tgen.createRandom(
        10000000,  # duration
        0,  # min_addr
        AddrRange("256MB").end,  # max_adr
        64,  # block_size
        1000,  # min_period
        1000,  # max_period
        100,  # rd_perc
        0,
    )  # data_limit
    yield tgen.createExit(0)


def createLinearTraffic(tgen):
    yield tgen.createLinear(
        10000000,  # duration
        0,  # min_addr
        AddrRange("3kB").end,  # max_adr
        64,  # block_size
        1000,  # min_period
        1000,  # max_period
        100,  # rd_perc
        0,
    )  # data_limit
    yield tgen.createExit(0)


root = Root(full_system=False, system=system)

m5.instantiate()
system.generator.start(createLinearTraffic(system.generator))
exit_event = m5.simulate()
