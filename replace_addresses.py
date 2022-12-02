# This program creates a file "trace_custom_addrs.tr"
# which is a duplicate of "n-node-ppp.tr"
# except that the ip addresses have been replaced with addresses that
# relect the source and destination node indexes. The new format for
# the ip addresses is:
#     i.j.*.*
# where:
#     i is the source node index
#     j is the destination node index
#     * are the values from the ns3 assigned addresses

import sys

def get_addrs_matrix(addr_lines):
    """ Returns the current address name for interface from node i --to--> i, and the proposed new name. """
    ntotal = len(addr_lines)

    # this will be the map from current names to new proposed names
    ret: list[list[tuple(str,str)]] = []
    ret = [[("","") for x in range(ntotal)] for y in range(ntotal)]

    # build the return map
    # new addresses are of the form "10.i.j.*"
    for i, addr_line in enumerate(addr_lines):
        for j, curr_addr in enumerate(addr_line.split(" ")):
            if i >= ntotal or j >= ntotal:
                continue
            if curr_addr == "x":
                continue
            addr_parts = curr_addr.split(".")
            new_addr = f"{i}.{j}.{addr_parts[2]}.{addr_parts[3]}"
            ret[i][j] = (curr_addr, new_addr)
    
    return ret

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} scratch_dir")
    scratch_dir = sys.argv[1]

    with open(scratch_dir+"/output/n-node-ppp.tr", "r") as fin:
        trace_lines = fin.readlines()
    with open(scratch_dir+"/output/node_interfaces.txt", "r") as fin:
        addr_lines = fin.readlines()
    
    # get the new addresses, and replace them in the new trace file
    addrs_matrix = get_addrs_matrix(addr_lines)
    with open(scratch_dir+"/output/trace_custom_addrs.tr", "w") as fout:
        fout.write(f"# This file was generated with \"python {' '.join(sys.argv)}\"\n")
        for line in trace_lines:
            oline = line
            for addrs_row in addrs_matrix:
                for old, new in addrs_row:
                    if old != "" and new != "":
                        line = line.replace(old, new)
            fout.write(line)