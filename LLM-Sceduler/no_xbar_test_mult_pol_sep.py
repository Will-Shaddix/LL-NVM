from m5.objects import *
from m5.util.convert import *
from m5.util import addToPath
import m5
import argparse
from m5.objects.DRAMInterface import *
#from m5.objects.DRAMAlloyInterface import *
from m5.objects.NVMInterface import *
from math import log
import math

def interleave_addresses(dram_class, num_chnl, intlv_size, start, size):

    num_chnls = num_chnl
    intlv_bits = int(math.log(num_chnls, 2))
    cache_line_size = 64
    intlv_low_bit = int(math.log(cache_line_size, 2))

    ret_list = []


    for i in range (num_chnl):
        ret_list.append(AddrRange( start=start,
             size=size,
             intlvHighBit = intlv_low_bit + intlv_bits - 1,
             intlvBits = intlv_bits, ##number of bits for interleaving 
             intlvMatch = i))

    return ret_list

args = argparse.ArgumentParser()

args.add_argument(
    "traffic_mode",
    type = str,
    help = "Traffic type to use"
)

args.add_argument(
    "rd_prct",
    type=int,
    help="Read Percentage",
)

args.add_argument(
    "hit",
    type=int,
    help="Read Percentage",
)

args.add_argument(
    "dirty",
    type=int,
    help="Read Percentage",
)

args.add_argument(
    "near_mem_type",
    type=str,
    help="NVM or DRAM",
)

args.add_argument(
    "far_mem_type",
    type=str,
    help="NVM or DRAM or LL_NVM_PCM or LL_NVM_PCM_3",
)

args.add_argument(
    "policy",
    type=str,
    help="Policy for Policy Manager",
)

args.add_argument(
    "num_tgens",
    type=int,
    help="number of traffic generators",
)

args.add_argument('duration', type = str,
                    help = '''real time duration to generate traffic
                    e.g. 1s, 1ms, 1us, 1ns''')

args.add_argument('injection_rate', type = int,
                    help = '''The amount of traffic generated
                    by the traffic generator in GBps''')

args.add_argument(
    'mem_size', 
    type = int,
    help = '''The memory size in GB'''
)

args.add_argument(
    'num_chnls', 
    type = int,
    help = '''Number of boith near and far memory channels'''
)

options = args.parse_args()
# options.num_near_chnls = 3
# options.num_far_chnls = 3
options.num_near_chnls = options.num_chnls
options.num_far_chnls = options.num_chnls

options.unified_queue = 0

options.duration = int(toLatency(options.duration) * 1e12)

options.block_size = 64

injection_period = int((1e12 * options.block_size) /
                    (options.injection_rate * 1073741824))
options.min_period = injection_period
options.max_period = injection_period

bpc = 64
num_LLM_chnls = options.num_near_chnls * bpc
num_chnls = options.num_near_chnls
num_far_chnls = options.num_far_chnls
num_far_LLM_chnls = num_far_chnls * bpc
#mem_sizes = 6
mem_sizes = options.mem_size


system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "5GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = 'timing'



# system.monitors = [CommMonitor(sample_period="10000ns") for i in range(num_far_chnls)]

system.generators = [PyTrafficGen() for i in range(options.num_tgens)]

if(options.near_mem_type == "LLM" or options.near_mem_type == "LL_NVM_PCM" or options.near_mem_type == "LL_NVM_PCM3"):
    #system.monitors = [CommMonitor(sample_period="10000ns") for i in range(num_far_chnls)]
    num_chnls = num_LLM_chnls
    system.scheds = [MemScheduler(read_buffer_size = 1, write_buffer_size = 32, resp_buffer_size = 64, unified_queue = options.unified_queue, \
                            service_write_threshold = 100 - int(options.rd_prct)) for i in range(num_far_chnls)]
    
if(options.far_mem_type == "LLM" or options.far_mem_type == "LL_NVM_PCM" or options.far_mem_type == "LL_NVM_PCM3"):
    num_chnls = num_far_LLM_chnls
    system.far_scheds = [MemScheduler(read_buffer_size = 1, write_buffer_size = 32, resp_buffer_size = 64, unified_queue = options.unified_queue, \
                            service_write_threshold = 100 - int(options.rd_prct)) for i in range(num_far_chnls)]

ctrl_list = []
for i in range(0, num_far_chnls):
    curr_mem = str(int(i * mem_sizes / num_far_chnls)) + 'GiB' # Takes the desred memory size and divies up between policy managers
    next_mem = str(int((i+1) * mem_sizes / num_far_chnls)) + 'GiB' 
    #print("Policy manager", curr_mem, next_mem)
    ctrl_list.append(PolicyManager(range=AddrRange(curr_mem, next_mem), dram_cache_size = ('20MiB')))
    ctrl_list[i].tRP = '14.16ns'
    ctrl_list[i].tRCD_RD = '14.16ns'
    ctrl_list[i].tRL = '14.16ns' 

system.mem_ctrl = ctrl_list

# system.loc_mem_ctrlrs = [HBMCtrl() for i in range(8)]
system.loc_mem_ctrlrs = [MemCtrl() for i in range(num_chnls)]

if(options.near_mem_type == "DRAM"):
    loc_ranges = interleave_addresses(DDR4_2400_16x4, options.num_near_chnls, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel

    for i in range (0,num_chnls):
        system.loc_mem_ctrlrs[i].dram = DDR4_2400_16x4(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?

        system.loc_mem_ctrlrs[i].port = system.mem_ctrl.loc_req_port # system.membusPolManLocMem.mem_side_ports



elif(options.near_mem_type == "HBM"):
    loc_ranges = interleave_addresses(HBM_1000_4H_1x128, options.num_near_chnls, 128, 0, '6GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel

    # sizes
    
    for i in range (0,num_chnls):
        curr_mem = str(int(i * mem_sizes / num_chnls)) + 'GiB'
        next_mem = str(int((i+1) * mem_sizes / num_chnls)) + 'GiB'

        system.loc_mem_ctrlrs[i].dram = HBM_1000_4H_1x128(range=AddrRange(curr_mem, next_mem), in_addr_map=False, null=True) # why the dram and dram_2?

    #for mem_ctrl in system.mem_ctrl:
        system.loc_mem_ctrlrs[i].port =  system.mem_ctrl[i].loc_req_port#system.membusPolManLocMem.mem_side_ports #mem_ctrl.loc_req_port #system. system.membusPolManLocMem.mem_side_ports

elif(options.near_mem_type == "LLM"):
    loc_ranges = interleave_addresses(LLM, num_LLM_chnls, 128, 0, '6GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel



    for i in range(options.num_near_chnls):

        system.scheds[i].cpu_side = system.mem_ctrl[i].loc_req_port #system.membusPolManLocMem.mem_side_ports 


    #print(len(system.loc_mem_ctrlrs), "here!")
    for i in range (0,num_LLM_chnls):
        curr_mem = str(int( (i * 1024 * mem_sizes) / num_LLM_chnls)) + 'MiB'
        next_mem = str(int(((i+1) * 1024 * mem_sizes) / num_LLM_chnls)) + 'MiB'
        
        system.loc_mem_ctrlrs[i].dram =LLM(range=AddrRange(curr_mem, next_mem), in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram =LLM(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram_2 = DDR4_2400_16x4(range=loc_ranges[2*i+1], in_addr_map=False, null=True)
        # system.scheds[i].cpu_side = system.mem_ctrl.loc_req_port # system.membusPolManLocMem.mem_side_ports

        # system.loc_mem_ctrlrs[i].port = system.mem_ctrl.loc_req_port # system.membusPolManLocMem.mem_side_ports
        system.scheds[int(i / bpc)].mem_side = system.loc_mem_ctrlrs[i].port
            
        #system.loc_mem_ctrlrs[i].port = system.membusPolManLocMem.mem_side_ports
        
elif(options.near_mem_type == "LL_NVM_PCM"):
    loc_ranges = interleave_addresses(LL_NVM_PCM, num_LLM_chnls, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel

    for i in range (0,num_LLM_chnls):
        system.loc_mem_ctrlrs[i].dram =LL_NVM_PCM(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram_2 = DDR4_2400_16x4(range=loc_ranges[2*i+1], in_addr_map=False, null=True)
        # system.loc_mem_ctrlrs[i].port = system.membusPolManLocMem.mem_side_ports
        for mem_ctrl in system.mem_ctrl:
            #system.scheds[i].cpu_side = system.mem_ctrl.loc_req_port # system.membusPolManLocMem.mem_side_ports
            system.scheds[i].cpu_side = mem_ctrl.loc_req_port # system.membusPolManLocMem.mem_side_ports
        system.scheds[i].mem_side = system.loc_mem_ctrlrs[i].port
        
elif(options.near_mem_type == "LL_NVM_PCM_3"):
    loc_ranges = interleave_addresses(LL_NVM_PCM_3, 8, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel

    for i in range (0,num_LLM_chnls):
        system.loc_mem_ctrlrs[i].dram =LL_NVM_PCM_3(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram_2 = DDR4_2400_16x4(range=loc_ranges[2*i+1], in_addr_map=False, null=True)
        # system.loc_mem_ctrlrs[i].port = system.membusPolManLocMem.mem_side_ports
        system.scheds[i].cpu_side = system.mem_ctrl.loc_req_port # system.membusPolManLocMem.mem_side_ports
        system.scheds[i].mem_side = system.loc_mem_ctrlrs[i].port
    #system.far_mem_ctrl.dram = NVM_2400_1x64(range=AddrRange('3GiB'), in_addr_map=False, null=True)
# main memory

# DRAM Main memory

system.far_mem_ctrl = [MemCtrl() for i in range(num_far_chnls)]


if(options.far_mem_type == "DRAM"):
    for i in range (0,num_far_chnls):
        curr_mem = str(int(i * mem_sizes / num_chnls)) + 'GiB'
        next_mem = str(int((i+1) * mem_sizes / num_chnls)) + 'GiB'
        system.far_mem_ctrl[i] = MemCtrl()
        system.far_mem_ctrl[i].dram = DDR3_1600_8x8(range=AddrRange(curr_mem, next_mem), in_addr_map=False, null=True)


elif(options.far_mem_type == "NVM"):
    
    for i in range (0,num_far_chnls):
        curr_mem = str(int(i * mem_sizes / num_far_chnls)) + 'GiB'
        next_mem = str(int((i+1) * mem_sizes / num_far_chnls)) + 'GiB'
        # print(curr_mem, next_mem, i)
        system.far_mem_ctrl[i] = MemCtrl()
        system.far_mem_ctrl[i].dram = NVM_2400_1x64(range=AddrRange(curr_mem, next_mem), in_addr_map=False, null=True)
    

elif(options.far_mem_type == "LLM"):

    far_ranges = interleave_addresses(LLM, num_far_LLM_chnls, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel

    for i in range (0,num_far_LLM_chnls):
        system.far_mem_ctrlrs[i].dram =LLM(range=far_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        
        system.far_scheds[i].cpu_side = system.mem_ctrl.loc_req_port # system.membusPolManLocMem.mem_side_ports
        system.far_scheds[i].mem_side = system.far_mem_ctrlrs[i].port
        
        
elif(options.far_mem_type == "LL_NVM_PCM"):
    system.far_mem_ctrl = MemCtrl()
    system.far_mem_ctrl.dram = LL_NVM_PCM(range=AddrRange('3GiB'), in_addr_map=False, null=True)

        
elif(options.far_mem_type == "LL_NVM_PCM_3"):
    system.far_mem_ctrl = MemCtrl()
    system.far_mem_ctrl.dram = LL_NVM_PCM3(range=AddrRange('3GiB'), in_addr_map=False, null=True)
else:
    print("INVALID MEMORY TYPE: " + str(options.far_mem_type))


if(options.far_mem_type != "LLM"):

    for i in range(0, num_far_chnls):
        system.mem_ctrl[i].far_req_port = system.far_mem_ctrl[i].port


# system.membus = L2XBar(width=64)
system.membus = IOXBar(width=64)

system.membus.frontend_latency = 1
system.membus.response_latency  = 1
#system.membus.max_routing_table_size = 90000

for mem_ctrl in system.mem_ctrl:
    mem_ctrl.port = system.membus.mem_side_ports # for moved comm monitor
    mem_ctrl.orb_max_size = 256 # 256
    #system.mem_ctrl.dram_cache_size = "128MiB"
    # mem_ctrl.dram_cache_size = "512MiB"
    mem_ctrl.dram_cache_size = "1MiB"
    mem_ctrl.always_hit = False
    mem_ctrl.always_dirty = False


for generator in system.generators:
    generator.port = system.membus.cpu_side_ports


def createRandomTraffic(tgen, tgen_options):
    yield tgen.createRandom(tgen_options.duration,  # duration getting rid of 2 0's
                            0,                      # min_addr
                            AddrRange(str(options.mem_size) + 'GiB').end,  # max_addr
                            tgen_options.block_size,                     # block_size
                            tgen_options.min_period,                   # min_period was 10
                            tgen_options.max_period,                   # max_period was 10
                            tgen_options.rd_prct,        # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)

def createLinearTraffic(tgen, tgen_options):
    yield tgen.createLinear(tgen_options.duration,  # duration 
                            0,                      # min_addr
                            AddrRange(str(options.mem_size) + 'GiB').end,  # max_addr
                            tgen_options.block_size,# block_size
                            tgen_options.min_period,# min_period was 10
                            tgen_options.max_period,# max_period
                            tgen_options.rd_prct,   # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)
    
def createStridedTraffic(tgen, tgen_options):
    yield tgen.createStrided(tgen_options.duration,            # duration 
                            0,                      # min_addr
                            AddrRange('3GiB').end,  # max_adr
                            64,                     # block_size
                            10000,                   # min_period was 1000
                            10000,                   # max_period
                            tgen_options.rd_prct,        # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)

root = Root(full_system=False, system=system)

m5.instantiate()

if options.traffic_mode == 'linear':
    for generator in system.generators:
        generator.start(createLinearTraffic(generator, options))
elif options.traffic_mode == 'random':
    for generator in system.generators:
        generator.start(createRandomTraffic(generator, options))
else:
    print('Wrong traffic type! Exiting!')
    exit()

exit_event = m5.simulate()
print(f"Exit reason {exit_event.getCause()}")


