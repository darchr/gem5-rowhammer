# Information on using the RowHammer Branch (HammerSim)

## Introduction

This file contains information on how to get started with the RowHammer module.
gem5 does not support RowHammer/data corruption by default but this repository adds several modifications to enable probabilistic modeling of RowHammer within gem5 in very fine-grained resolution, at the capacitor level.

TL;DR If you want to understand the code structure and data corruption, see [#understanding HammerSim](#understanding-the-code-structure).
TL;DR If you want to add a new mitigation, see [#adding new mitigation](#adding-a-new-rowhammer-mitigation).
TL;DR If you're interested to start using the infrastructure ASAP, see [#using HammerSim](#using-hammersim)

## Changes in the source and parameters to specify

Changes to the gem5's source is confined to the following files:
- `src/mem/DRAMInterface.py`
- `src/mem/mem_ctrl.cc`
- `src/mem/mem_ctrl.hh`
- `src/mem/packet.hh`
- `src/mem/dram_interface.hh`
- `src/mem/dram_interface.cc`
- `src/mem/mem_interface.hh`
- `src/mem/mem_interface.cc`
- `src/mem/SConscript`

Most of the RowHammer parameters are defined in `src/mem/DRAMInterface.py`.
In the class `DRAMInterface`, we have defined the following parameters:
- `device_file` - Absolute path to the device map file. The "device map" file
  refers to a list of all weak cells in the DRAM device. Currently we only
  only flip bits at the column level. The resolution of a bit flip can be
  further tuned to be at the capacitor level. This file is a `.json` file with
  the following format:
  ```json
  {
    "rank_number": {
        "bank_number": {
            "row_number": ["(int)list_of_all_weak_columns"],
        }
    }
  }
  ```
  For getting started, you can use the map included in the repository under `prob-005.json.zip`.
  This map is statistically generated using VARIUS
  (S. Sarangi et al.) (see the abstract/writeup for details). You can also
  generate this map from the hardware using a RowHammer software like TRRespass
  (P. Frigo et al.) or Blacksmith (P. Jattke et al.).
- `rowhammer_threshold` - This is the number of activates requires to trigger a
  single bitflip in a victim row. This number is taken from previous research
  (Y. Kim et al., J. S. Kim et al.) which states that the minimum activates
  required for DDR3 DRAM DIMMs is 139,000 and DDR4 DRAM DIMMs is 50,000. LPDDR
  numbers are even lower (~8,000 -- 16,000).
- `counter_table_length` - This is a Target Row Refresh (TRR) specific
  parameter. TRR is the mitigation mechanism present in all modern day DDR4
  DRAM DIMMs. Most of these TRR parameters are either reverse-engineered via
  previously mentioned RowHammer softwares or are taken from other reverse-
  engineering papers including but not limited to (H. Hassan et al.).
  `counter_table_length` is the total size of the main TRR table. TRR samples
  frequently activated rows. This table keeps a track of these rows.
- `trr_variant` - [0 -- 4]. We have implemented a version of the 2 TRR variants
  out of the three major DRAM vendors (Samsung, SK Hynix and MICRON) based on
  previous reverse-engineering techniques and also our own observations. This
  is not a 1:1 implementation of the actual TRR as it is proprietary, however
  we have tested for similar bitflips in same rows against real hardware.
  Following are the four different `trr_variants`:
  - 0: No TRR
  - 1: A counter table-based TRR mechanism, which works on a per-bank basis.
  - 2: A sampler-based TRR mechanism, which maintains a global refreshing
       scheme.
  - 3: Partially implemented another sampler-based TRR mechanism, which is not
       verified.
  - 4: PARA (Y. Kim et al.), one of the first RH mitigation mechanism, which
       issues activates to rows with a probability P. This is hard-coded to
       PARA-001 in the source.
- `companion_table_length` - Inserting a row into the companion table is tricky IMO.
  Therefore, I have used another small table, similar to the work called ProHIT (M. Son et al.).
  A row is initially inserted into the companion table first.
  Then, it is promoted to the counter table.
  This is specific to the TRR variant, which uses counter tables.
- `companion_threshold` - This is minimum number of activates required to make
  an entry into the companion table. Understandably, the threshold for the
  companion table is much lower than the actual TRR table (1024).
- `trr_stat_dump` - This is a boolean value ot dump all the actions of the TRR
  mechanism. One can set this to true to do a post-runtime analysis of
  RowHammer and TRR.
- `rh_stat_dump` - Similar to `trr_stat_dump`, you can also dump the stats of
  the RowHammer triggers. This is helpful for post-runtime analysis.
- `single_sided_prob` - The number of bitflips observed with a single-sided
  RowHammer attack is much lower than a double-sided rowhammer attack. We saw
  that this drop is 1e7 times less probable than a double-sided RowHammer
  attack.
- `half_double_prob` - Half-double (Google) is even more rare than a single
  sided RowHammer attack. We could not reproduce this with our experimental
  hardware setup. Therefore, we took this number from the Half-Double report.
  We kept this probability at 1/1e9.

## Understanding the code structure

Change to gem5 in HammerSim is quite invasive, meaning that dram_interface was directly modified without adding new SimObjects.
The justification is that this is a separate fork of gem5, that models hardware equivalent of a DRAM DIMM within the simulator.
Since RowHammer is baked into the DIMM directly, we decided to make changes directly into the dram_interface.

RowHammer is implemented using counters called `rhTriggers[row][4]` per row per bank.
Each of these counters count the likelyhood of the neighboring rows getting triggered.
Whenever there is an ACTIVATE for a row *r*, the `rhTriggers[row]` increment by 1.
ACTIVATE is implemented in the method
```cpp
void
DRAMInterface::activateBank(Rank& rank_ref, Bank& bank_ref,
                       Tick act_tick, uint32_t row)
```
`rhTriggers` keeps a track of rows *r - 2*, *r - 1*, *r + 1* and *r + 2* using the four counter indices.
Since ACTIVATING the row and then PRECHARGING the same row nullifies the likelyhood of a bit flip, the rhTriggers of rows *r - 2*, *r - 1*, *r + 1* and *r + 2* are updated with respect to row *r*.

Whenever `rhTrigger[row][index]` crosses the `rowhammer_threshold` (defined via python), there is a non-zero probability of a bitflip on the same row `row`.
There are four probability distributions to make this decision:
1. Whether the given capacitor is weak (See RowHammer PUF [], FP-Rowhammer [] and FP-Hammer []). Prior research have shown that not every bit has the same probability of flipping. There are strong and weak cells. This information in HammerSim is captured via a variation map, provided as the `device_map`.
2. The uniform probability of selecting a weak cell from a given set of weak cells.
3. The uniform probability of selecting a double-sided or a single-sided bitflip.
4. The uniform probability of causing a half-double bit flip.

RowHammer is checked in the method:
```cpp
void
DRAMInterface::checkRowHammer(Bank& bank_ref, MemPacket* mem_pkt)
{
  // each of the four conditions of having a bitflip is checked here.
}
```

This method `checkRowHammer()` is called after finishing a burst access to the DRAM:
```cpp
std::pair<Tick, Tick>
DRAMInterface::doBurstAccess(MemPacket* mem_pkt, Tick next_burst_at,
                             const std::vector<MemPacketQueue>& queue)
```
This makes sure to cause RowHammer bitflips if triggered in the current ACTIVATE.

To make changes on how RowHammer behaves, start with `checkRowHammer()` method.
This method automatically calls `doMemoryCorruption()` with the aggressor row address, and, victim locations.
```cpp
void
DRAMInterface::doMemoryCorruption(MemPacket* mem_pkt, uint8_t bank,
                uint32_t victim_row, uint16_t col, int distance) {
```
The correct victim location (victim row, column, and capacitor) is computed each time when a new bit is flipped, which makes data corruption an expensive feature.
Currently, we only support DRAM address mapping with `ro` as the high bits and `co` as the low order bits.
See how different mapping in gem5 work: [DRAM mappings in gem5](https://gem5-review.googlesource.com/c/public/gem5/+/51614/2/src/python/gem5/components/memory/ReadMe_MultiChannel_Memory.md).
We'll support other memory mappings soon with multi-channeled memory.

If you're using `rowhammer-test`, should be able to see your aggressor rows and victim rows correctly.

### Data structures for writing a new RowHammer Mitigation

HammerSim implements TRR using `trr_tables[TABLE_LENGTH][4 PARAMETERS]` to keep track of highly activated rows per bank.
Each entry stores the rank, bank, row and a count of activates.
Some TRR implementations are per rank.
There are a lot of data structures that can be reused for keeping track of frequent aggressors.
See `companion_table` for a multi-table TRR/mitigation method.

In addition, there are `flagged_entries` to make sure the same capacitor cannot flip twice.
Aggressors are deterministically tracked using `aggressor_rows`.

### Adding a new RowHammer Mitigation

Adding a new mitigation mechanism has to be done in the `dram_interface.cc` file.
This is done in:
```cpp
// the sampler/counter mechanism is defined here.
void
DRAMInterface::activateBank(Rank& rank_ref, Bank& bank_ref,
                       Tick act_tick, uint32_t row) {
    ...
    switch (trrVariant) {
        ...
        case N: {
            // write a new mitigation mechanism here.
        }
        ...
    }
    ...
}

// the inhibitor mechanism is implemented here. this is because the inhibitor
// mechanism is triggers when the DRAM device is locked for refreshing.
void
DRAMInterface::Rank::processRefreshEvent() {
    ...
    switch(dram.trrVariant) {
        ...
        case N: {
            // write the inhibitor mechanism here to keep DRAM timing
            // consistent.
        }
        ...
    }
    ...
}
```

RowHammer bitflips are checked in the following function:
```cpp
void
DRAMInterface::checkRowHammer(Bank& bank_ref, MemPacket* mem_pkt) {
    ...
}
```

#### Tutorial mitigation: TWICE tables

TWICE (E Lee et al.) is a good mitigation mechanism, easy to understand as a beginner to HammerSim.
In this tutorial, we show how to add TWICE in HammerSim.

TWICE mathematically calculates the theoretical maximum number of aggressors possible during one tREFW.
This is given by:
$$ N = \frac{tREFW}{RowHammer Threshold \times tRC} $$

For a simple DDR4 DIMM, $N = 25$
This can be further pruned via:

To implement tracking of these many aggressors per bank, we first define the trrTableLength in the python class for the DIMM.
```py
class TwiceDIMM():
    trr_table_length = N
    # We'll define a unique trr_variant number for this mitigation
    trr_variant = 10
```
We'll use the above trr\_variant to write our C++ changes.
For this, we'll directly use `trrTable` that tracks rows with activate count.

### Plating with error correcting codes (ECC)

TODO

HammerSim models a **functional (not timing)** ECC to detect and correct RowHammered bitflips.
We implement SECDED within a simplified interface.
ECC bits are computed and stored for each DRAM write.
Data is corrected if corrupt when read.
Since this is expensive to simulate in gem5 for full-system configureations, we selectively keep track of data that is corrupted.
If the user wants to simulate ECC, then at every data corruption, we track the original data for the ECC bits calculation.
At the time of reading the same data, we compute and use the ECC bits to correct up to 1 bit and detect up to 2 bits error.

## Using HammerSim

There are pre-defined config scripts, that can be directly used with HammerSim.
There are located in `configs/dram/rowhammer` directory.
There are both traffic generators and also full system scripts.
Note that the disk image path need to be replaced.

### Synthetic Traffic via gem5's Traffic Generators

### Full-System Simulation

#### Creating Full-System RowHammer Workload

Testing was done using [Google's rowhammer-test](https://github.com/google/rowhammer-test).
We ran one iteration of the hammering run for both single-sided and double-sided versions of RowHammer.
`m5 exit` is dropped before starting the workload and `m5 exit` is dropped at the end of the iteration (with or without bitflips).

To create the disk image, use:
```sh
git clone https://github.com/kaustav-goswami/gem5-resources.git
cd gem5-resources
git checkout rowhammer
cd src/rowhammer-fs
./build-x86.sh 22.04
```

To build the same kernel that we used for the full system simulation:
```sh
wget https://www.kernel.org/pub/linux/kernel/v5.x/linux-5.4.49.tar.xz
tar xvf linux-5.4.49.tar.xz
cd linux-5.4.49.tar.xz
menu config                                      # Use the default build
make -j32
```
Alternately, you can also build the same kernel from `gem5-resources` repository.

Use custom resource in gem5 to plug these artifacts.
```py
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
        os.path.join(os.getcwd(),
          "gem5-resources/src/rowhammer-fs/x86-disk-image-22-04/x86-ubuntu"),
        root_partition="1"
    ),
    readfile_contents=" ".join(command),
)
```

Scripts to run `rowhammer-test` is located in `configs/dram/rowhammer/FSConfigs/rowhammer-test/x86-rowhammer-with-kvm.py` (and there is a no cache version).

## More Information

More on HammerSim can be found here: https://arch.cs.ucdavis.edu/memory/simulation/security/2023/03/20/yarch-hammersim.html
