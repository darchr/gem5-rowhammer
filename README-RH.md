# Information on using the RowHammer Branch (HammerSim)

## Introduction

This file contains information on how to get started with the RowHammer module.

## Changes in the source

Changes to the gem5's source is confined to the following files:
- `src/mem/DRAMInterface.py`
- `src/mem/mem_ctrl.cc`
- `src/mem/mem_Ctrl.hh`
- `src/mem/packet.hh`
- `src/mem/dram_interface.hh`
- `src/mem/dram_interface.cc`
- `src/mem/mem_interface.hh`
- `src/mem/mem_interface.cc`
- `src/mem/SConscript`

Most of the RowHammer parameters are defined in `src/mem/DRAMInterface.py`. In
the class `DRAMInterface`, we have defined the following parameters:
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
  For starters, you can use the map included in the repository under
  `prob-005.json.zip`. This map is statistically generated using VARIUS
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
- `companion_table_length` - Inserting a row into the companion table is
  tricky IMO. Therefore, I have used another small table, similar to the work
  called ProHIT (M. Son et al.). A row is initially inserted into the companion
  table first. Then, it is promoted to the counter table. This is specific to
  the TRR variant, which uses counter tables.
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

Adding a new mitigation mechanism has to be done in the `mem_interface.cc`
file. This is done in:
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

## Using HammerSim

There are pre-defined config scripts, that can be directly used with HammerSim.
There are located in `configs/dram/rowhammer` directory. There are both traffic
generators and also full system scripts. Note that the disk image path need to
be replaced.

## More Information

More on HammerSim can be found here: https://arch.cs.ucdavis.edu/memory/simulation/security/2023/03/20/yarch-hammersim.html
