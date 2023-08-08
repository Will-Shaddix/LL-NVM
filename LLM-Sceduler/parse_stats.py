# This python file will read in a stats.txt file from gem5 and parse it based on the given stats
# The expected input is a path to the stats.txt, a file containing all the  stats you want, and an output directory to write this information for.
# This Should enable graph generation to be much easier
import argparse



import os
#rootdir = '/home/wshaddix/dram_cache/dramCacheController/res_test'



args = argparse.ArgumentParser()

args.add_argument(
    "stats_path",
    type = str,
    help = "Path to stats.txt"
)

args.add_argument(
    "param",
    type = str,
    help = "Path to txt file wit parameters to read in"
)

args.add_argument(
    "output_dir",
    type = str,
    help = "Path to output directory"
)

options = args.parse_args()

print(options)

#f = open(options.stats_path, 'r')
rootdir = options.stats_path
avg = 0
for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        myPath = os.path.join(subdir, file)
        print(myPath)

        if "stats.txt" in myPath:
            avg = 0
            leng = 0
            print("in if!")
            f = open(myPath, 'r')
            content = f.readlines()

            param_f = open(options.param, 'r')
            write_f = open(options.output_dir, 'a')

            params = param_f.readlines()

            write_f.write("\n" + myPath + ":\n")

            for line in content: # for each line in stats.txt
                split_line = line.split() # split the line by white space
                if len(split_line) > 1:# tests if this line of stats is actual stats
                    for param in params:# for every parameter in param file
                        if param.split()[0] in split_line[0]:# checks if param is in the stat line
                            # print(split_line[0])
                            #write_f.write("\t" + split_line[0] + ": " + split_line[1]+ "\n")
                            avg = avg + float(split_line[1])
                            print(avg)
                            leng +=1
                    
            write_f.write("\t" + "Average" + ": " + str(avg/leng)+ "\n")
            param_f.close()
            f.close()

