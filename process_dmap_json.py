# importing the module
import json

# This script takes a device_map.json file
# and converts it into a device_map.txt file
# to make it easier to be parsed in C++ code

# Output file follows the following format
# Start of each new entry with "**"
# then the next lines will correspond to the following:
# 1) rank (actually right now this entry/line will be missing since the
# current tests are only done with single rank DRAM)
# 2) bank
# 3) the row number
# 4) a comma separated list of corrupt columns within a particular row (line ends with "e")

# opening the JSON file
data = open('device_map.json',)

# deserializing the data
data = json.load(data)

outfile = open("device_map.txt", "w")
outfile.write("**\n")
# 1 rank device
for bank in data["0"]:
      for row in data["0"][bank]:
            outfile.write(bank)
            outfile.write("\n")
            outfile.write(row)
            outfile.write("\n")
            for col in range(len(data["0"][bank][row])):
                  #print(col)
                  outfile.write(str(data["0"][bank][row][col]))
                  outfile.write(",")
            outfile.write("e\n")
            outfile.write("**\n")
outfile.close()
