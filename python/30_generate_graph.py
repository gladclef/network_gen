# generate graphs from the parsed pcaps from 20_parse_pcaps.py
import glob
import os
import pickle
import re
import sys
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from python.MicroGrid import *

constant_internet_rate = 50 * 1000 # 10KBps for worst-case scenario internet traffic, viewing cameras or the such

def parse_pcaps(files: list[str]) -> dict[int, list[list[float, int]]]:
    """ Parses pcap files and returns the size of the packets found.

    Returns
    -------
        dict( nodeid, [[time, packet size]+] ) """
    rconn = re.compile(r"20_pcap_ppp-(\d+)-(\d+)\.csv")
    ret: dict[int, list[list[float, int]]] = {}

    for file in files:
        match = rconn.match(file)
        if match is None:
            continue

        node = int(match.groups()[0])
        interface = int(match.groups()[1])

        with open(file, "r") as fin:
            header = None
            for line in fin:
                line = line.strip()
                if header is None:
                    header = line
                    continue
                if "," not in line:
                    continue

                # example line
                # "0.000000000", "10.0.0.2", "10.0.0.1", "540"
                parts = [s.strip('"') for s in line.split(",")]
                time = float(parts[0])
                nbytes = int(parts[3])+2 # +2 for bytes on the wire

                if node not in ret:
                    ret[node] = []
                ret[node].append([time, nbytes])

    return ret

def get_node_sliding_windows(pcap_files):
    # get the bytes used per node from the pcap files
    parsed_pcaps = parse_pcaps(pcap_files)

    # collapse lists to second level granularity
    node_windows: dict[int, list[list[float], list[int]]] = {}
    for nodeIdx in parsed_pcaps:
        time_size_list = parsed_pcaps[nodeIdx]
        time_size_list.sort(key=lambda ts: ts[0])

        # build our list to append to
        window = []
        ts_persec = [[], []]

        # helper function for recording values
        def record_window_value(t):
            """ appends the current window sum """
            ts_persec[0].append( t )
            bitrate = sum([ts[1] for ts in window]) + constant_internet_rate
            ts_persec[1].append( bitrate )

        # Slide our 1-second window over the list of packets, getting total bitrate at
        # a 1 second granularity.
        for ts in time_size_list:
            time = ts[0]

            # remove values no longer within the window
            to_remove = []
            for old_ts in window:
                if old_ts[0] < time-1:
                    to_remove.append(old_ts)
                else:
                    break
            for r in to_remove:
                window.remove(r)
                record_window_value(r[0]+1)

            # add this ts to the window
            window.append(ts)
            record_window_value(time)

        node_windows[nodeIdx] = ts_persec

    return node_windows

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} output_dir")
        return
    scratch_dir = sys.argv[1]
    colors = [c for c in mcolors.TABLEAU_COLORS]
    degrees = list(range(1, 6))

    # "all_degrees", "bitrate_per_node", "bitrate_per_node_norm", "bandwidth_by_degrees"
    which_plot = "bandwidth_by_degrees"
    highest_vals = []

    # evaluate for each of our output directories
    for ndegrees in degrees:
        od_name = f"output_{ndegrees}"
        output_dir = os.path.join(scratch_dir, od_name)
        print(output_dir)
        os.chdir(output_dir)

        # get the list of pcap files
        files = []
        for file in glob.glob("20_pcap_ppp-*.csv"):
            files.append(file)

        # parse the pcap files (or load cached results)
        picklefile = "node_sliding_windows.pickle"
        if os.path.exists(picklefile) and os.stat(picklefile).st_mtime > os.stat(files[0]).st_mtime:
            with open(picklefile, "rb") as fin:
                node_windows: dict[int, list[list[float], list[int]]] = pickle.load(fin)
        else:
            node_windows = get_node_sliding_windows(files)
            with open(picklefile, "wb") as fout:
                pickle.dump(node_windows, fout)

        # get the size of the network
        with open("10_network_size.txt", "r") as fin:
            ny = int(fin.readline())
            nx = int(fin.readline())

        # get the max values per node
        max_vals = [[], []]
        for nodeIdx, ts_persec in node_windows.items():
            # get the maximum value for each node
            mv = max(ts_persec[1])
            nodex = int(nodeIdx % nx)
            nodey = int((nodeIdx - nodex) / nx)
            max_vals[0].append([nodex, nodey])
            max_vals[1].append(mv)

        # overlay the bitrate on top of the network topology graph
        MGs = read_encoded_mgs("10_mgs_encoded.csv")
        for i in range(len(max_vals[0])):
            nodexy, mv = max_vals[0][i], max_vals[1][i]
            MGs[nodexy[1]][nodexy[0]].intensity = mv
        draw_adjacency_matrix(MGs, "30_adjacency_matrix.png", max(max_vals[1]))

        # report the max N nodes
        N = 5
        max_vals_n = []
        for n in range(N):
            # get the maximum nodes
            mval = max(max_vals[1])
            mvIdx = max_vals[1].index(mval)
            nodexy = max_vals[0][mvIdx]
            max_vals_n.append([nodexy, mval])
            max_vals[0].remove(nodexy)
            max_vals[1].remove(mval)
        print(max_vals_n)

        # set up the graph
        plotSaveName = ""
        plotAllNodes = False
        plotHighestVal = False
        if which_plot == "all_degrees":
            plt.subplot(3, 2, ndegrees)
            plt.title(f"{ndegrees} Degrees")
            plt.ylim([0, 10_000_000])
            if ndegrees % 2 != 1:
                plt.yticks([])
            if ndegrees < 4:
                plt.xticks([])
            if ndegrees == 5:
                plt.ylabel("Bytes")
                plt.xlabel("Seconds")
            plotAllNodes = True
        if which_plot == "bitrate_per_node":
            plt.subplot(1, 1, 1)
            plt.title(f"{ndegrees} Degrees")
            plotSaveName = "30_" + which_plot + ".png"
            plotAllNodes = True
        if which_plot == "bitrate_per_node_norm":
            plt.subplot(1, 1, 1)
            plt.title(f"{ndegrees} Degrees")
            plt.ylim([0, 10_000_000])
            plotSaveName = "30_" + which_plot + ".png"
            plotAllNodes = True
        if which_plot == "bandwidth_by_degrees":
            plotHighestVal = True

        # graph each node
        if plotAllNodes:
            for nodeIdx, ts_persec in node_windows.items():
                color = colors[nodeIdx % len(colors)]
                plt.plot(ts_persec[0], ts_persec[1], color=color)

        # graph just the highest value
        if plotHighestVal:
            highest_vals.append(max_vals_n[0][1])

        # save the graph
        if plotSaveName != "":
            plt.savefig(plotSaveName)

    # graph the highest values
    if which_plot == "bandwidth_by_degrees":
        plt.subplot(1, 1, 1)
        plt.xlabel("Degrees of Communication")
        plt.xticks(degrees)
        plt.ylabel("Max Bytes/Node")
        plt.title("Maximum Bandwidth Usage By Degree")
        # print(highest_vals)
        # print(np.polyfit(degrees, highest_vals, 2)) # [ 484076.28571429 -555146.51428572  250090.40000002]
        poly = [4.8e5*(degree**2) + -5.5e5*(degree) + 2.5e5 for degree in degrees]
        plt.plot(degrees, poly, color=colors[1])
        plt.plot(degrees, highest_vals, color=colors[0])
        plt.legend(["4.8e5*d^2 - 5.5e5*d + 2.5e5", "Simulated Values"])

    # save the graph part 2, electric boogaloo
    os.chdir(scratch_dir)
    if which_plot == "all_degrees":
        plt.savefig("30_all_degrees.png")
    if which_plot == "bandwidth_by_degrees":
        plt.savefig("30_bandwidth_by_degrees.png")

if __name__ == "__main__":
    main()