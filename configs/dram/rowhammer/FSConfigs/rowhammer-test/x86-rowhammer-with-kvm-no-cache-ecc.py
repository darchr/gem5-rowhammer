# Copyright (c) 2021 The Regents of the University of California
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

"""

This script shows an example of running a full system Ubuntu boot simulation
using the gem5 library. This simulation boots Ubuntu 18.04 using 2 KVM CPU
cores. The simulation then switches to 2 Timing CPU cores before running an
echo statement.

Usage
-----

```
scons build/X86/gem5.opt
./build/X86/gem5.opt configs/example/gem5_library/x86-ubuntu-run-with-kvm.py
```
"""

import os
from gem5.resources.resource import CustomResource, CustomDiskImageResource
from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.boards.kernel_disk_workload import KernelDiskWorkload
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.coherence_protocol import CoherenceProtocol
from gem5.resources.resource import Resource
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent

from gem5.utils.override import overrides
import argparse

parser = argparse.ArgumentParser(
    description="An example configuration script to run rowhammer-test with \
several different probabilities"
)

# The only positional argument accepted is the benchmark name in this script.

parser.add_argument(
    "--single-sided",
    type=str,
    required=False,
    default="1e7",
    help="Input the benchmark program to execute."
)

args = parser.parse_args()

class Myboard(X86Board):

    def __init__(
        self,
        clk_freq: str,
        processor,
        memory,
        cache_hierarchy,
    ) -> None:
        super().__init__(
            clk_freq=clk_freq,
            processor=processor,
            memory=memory,
            cache_hierarchy=cache_hierarchy,
        )
    @overrides(KernelDiskWorkload)
    def get_default_kernel_args(self):
        return [
            "earlyprintk=ttyS0",
            "console=ttyS0",
            "lpj=7999923",
            "root=/dev/hda2",
            "disk_device={disk_device}",
        ]

# This runs a check to ensure the gem5 binary is compiled to X86 and to the
# MESI Two Level coherence protocol.
requires(isa_required=ISA.X86, kvm_required=True)

from gem5.components.cachehierarchies.classic.no_cache import NoCache

# Here we setup a MESI Two Level Cache Hierarchy.
cache_hierarchy = NoCache()

# Setup the system memory.
memory = SingleChannelDDR3_1600(size="2GB")
memory._dram_class.trr_variant = 0

memory._dram_class.ranks_per_channel = 1
memory._dram_class.rh_stat_dump = False
memory._dram_class.half_double_prob = 1e10
# Double sided rowhammre should always be lower.
memory._dram_class.double_sided_prob = 1e5
# Rowhammer test performs single sided attacks
memory._dram_class.single_sided_prob = float(args.single_sided)
# Enable memory corruption
memory._dram_class.enable_memory_corruption = True
# Enable ECC
memory._dram_class.enable_ecc = True
memory._dram_class.p_matrix = os.path.join(os.getcwd(),
                                           "util/hammersim/pMatrix.txt")
memory._dram_class.ecc_algorithm = 1

# Here we setup the processor. This is a special switchable processor in which
# a starting core type and a switch core type must be specified. Once a
# configuration is instantiated a user may call `processor.switch()` to switch
# from the starting core types to the switch core types. In this simulation
# we start with KVM cores to simulate the OS boot, then switch to the Timing
# cores for the command we wish to run after boot.
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.KVM,
    switch_core_type=CPUTypes.TIMING,
    num_cores=1,
    isa=ISA.X86
)

# Here we setup the board. The X86Board allows for Full-System X86 simulations.
board = Myboard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Here we set the Full System workload.
# The `set_kernel_disk_workload` function for the X86Board takes a kernel, a
# disk image, and, optionally, a command to run.

# This is the command to run after the system has booted. The first `m5 exit`
# will stop the simulation so we can switch the CPU cores from KVM to timing
# and continue the simulation to run the echo command, sleep for a second,
# then, again, call `m5 exit` to terminate the simulation. After simulation
# has ended you may inspect `m5out/system.pc.com_1.device` to see the echo
# output.
command = ["echo rowhammer_test;",
        "echo 12345 | sudo -S /home/gem5/rowhammer-test/rowhammer_test;"]

# "rowhammer_test"
# + "echo 'This is running on Timing CPU cores.';" \
# + "sleep 1;"
# + "m5 exit;"

board.set_kernel_disk_workload(
    # The x86 linux kernel will be automatically downloaded to the if not
    # already present.
    kernel=CustomResource(
        os.path.join(
            os.path.expanduser("~"), ".cache/gem5/x86-linux-kernel-5.4.49"
        )
    ),
    # The x86 ubuntu image will be automatically downloaded to the if not
    # already present.
    disk_image=CustomDiskImageResource(
        os.path.join("/home/kaustavg/projects/kg-resources/src/rowhammer-fs/x86-disk-image-22-04/x86-ubuntu"),
        root_partition="1"
    ),
    readfile_contents=" ".join(command),
)

simulator = Simulator(
    board=board,
    on_exit_event={
        # Here we want override the default behavior for the first m5 exit
        # exit event. Instead of exiting the simulator, we just want to
        # switch the processor. The 2nd m5 exit after will revert to using
        # default behavior where the simulator run will exit.
        # ExitEvent.EXIT: (func() for func in [processor.switch]),
    },
)
simulator.run()
simulator.run()
simulator.run()
processor.switch()
simulator.run()
