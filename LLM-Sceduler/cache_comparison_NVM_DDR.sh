for IR in 2 10 20 #50
do
    for RD in  0 #100 50 #0 
    do
        for tgen in 2 16 32
        do


            # build/X86/gem5.opt --outdir=no_xbar_res/NVM_Backing/LLM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol_sep.py  random  $RD  0 0 LLM NVM FirstTouch $tgen 100us $IR 8 2&
            # build/X86/gem5.opt --outdir=no_xbar_res/NVM_Backing/HBM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol_sep.py  random  $RD  0 0 HBM NVM FirstTouch $tgen 100us $IR 8 2

            # build/X86/gem5.opt --debug-flags=PolicyManager --outdir=no_xbar_res/NVM_Backing/HBM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol.py  random  $RD  0 0 HBM NVM FirstTouch $tgen 100us $IR &
            #build/X86/gem5.opt --outdir=no_xbar_res/NVM_Backing/HBM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol_sep.py  random  $RD  0 0 HBM NVM FirstTouch $tgen 1000us $IR 8 4
            #build/X86/gem5.opt --outdir=no_xbar_res/NVM_Backing/HBM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol.py  random  $RD  0 0 HBM NVM FirstTouch $tgen 8us $IR 
            #gdb --args build/X86/gem5.opt --outdir=no_xbar_res/NVM_Backing/LLM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol_sep.py  random  $RD  0 0 LLM NVM FirstTouch $tgen 1000us $IR 8 4
            # build/X86/gem5.opt -re --debug-flags=DRAM,MemCtrl,AddrRanges,MemoryAccess --outdir=no_xbar_res/NVM_Backing/LLM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol_sep.py  random  $RD  0 0 LLM NVM FirstTouch $tgen 1000us $IR 8 1
            #build/X86/gem5.opt --outdir=no_xbar_res/DDR_Backing/HBM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol_sep.py  random  $RD  0 0 HBM DRAM FirstTouch $tgen 1000us $IR 8 4
            
            
            build/X86/gem5.opt -re --debug-flags=PolicyManager --outdir=no_xbar_res/NVM_Backing/LLM_Cache/RANDOM/RD$RD/tgen$tgen/BW$IR    no_xbar_test_mult_pol_sep.py  random  $RD  0 0 LLM NVM FirstTouch $tgen 1000us $IR 8 2

        done
    done
done