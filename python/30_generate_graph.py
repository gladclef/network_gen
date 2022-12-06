# generate graphs from the parsed pcaps from 20_parse_pcaps.py
import glob
import os
import re
import sys
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

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

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} scratch_dir")
        return
    scratch_dir = sys.argv[1]
    os.chdir(os.path.join(scratch_dir, "output"))

    # get the bytes used per node from the pcap files
    files = []
    for file in glob.glob("20_pcap_ppp-*.csv"):
        files.append(file)
    node_packets = parse_pcaps(files)

    # collapse lists to second level granularity
    new_node_packets: dict[int, list[list[float], list[int]]] = {}
    for nodeIdx in node_packets:
        time_size_list = node_packets[nodeIdx]
        time_size_list.sort(key=lambda ts: ts[0])

        window = []
        ts_persec = [[], []]
        def record_window_value(t):
            # add a sum to the dict
            ts_persec[0].append( t )
            ts_persec[1].append( sum([ts[1] for ts in window]) )

        # convert to second level granularity
        window_time = 0
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

        new_node_packets[nodeIdx] = ts_persec

    # graph each node
    fig, ax = plt.subplots()
    colors = [c for c in mcolors.TABLEAU_COLORS]
    for nodeIdx, ts_persec in new_node_packets.items():
        color = colors[nodeIdx]
        ax.plot(ts_persec[0], ts_persec[1], color=color)

    plt.show()

if __name__ == "__main__":
    main()