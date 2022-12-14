/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2010 Egemen K. Cetinkaya, Justin P. Rohrer, and Amit Dandekar
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Egemen K. Cetinkaya <ekc@ittc.ku.edu>
 * Author: Justin P. Rohrer    <rohrej@ittc.ku.edu>
 * Author: Amit Dandekar       <dandekar@ittc.ku.edu>
 *
 * James P.G. Sterbenz <jpgs@ittc.ku.edu>, director
 * ResiliNets Research Group  http://wiki.ittc.ku.edu/resilinets
 * Information and Telecommunication Technology Center 
 * and
 * Department of Electrical Engineering and Computer Science
 * The University of Kansas
 * Lawrence, KS  USA
 *
 * Work supported in part by NSF FIND (Future Internet Design) Program
 * under grant CNS-0626918 (Postmodern Internet Architecture) and 
 * by NSF grant CNS-1050226 (Multilayer Network Resilience Analysis and Experimentation on GENI)
 *
 * This program reads an upper triangular adjacency matrix (e.g. adjacency_matrix.txt) and
 * node coordinates file (e.g. node_coordinates.txt). The program also set-ups a
 * wired network topology with P2P links according to the adjacency matrix with
 * nx(n-1) CBR traffic flows, in which n is the number of nodes in the adjacency matrix.
 */

// ---------- Header Includes -------------------------------------------------
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <unistd.h>

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/global-route-manager.h"
#include "ns3/mobility-module.h"
#include "ns3/netanim-module.h"
#include "ns3/assert.h"
#include "ns3/ipv4-global-routing-helper.h"

using namespace std;
using namespace ns3;

// ---------- Prototypes ------------------------------------------------------

void genOnOff(NodeContainer nodes, int from, int to, double packetRate, double startTime, double stopTime, uint16_t port, bool isExponential = false);
void runPythonFile(std::string filename);
void readNetSize(std::string netSizeFileName, int &ny, int &nx);
void readNDegrees(std::string ndegreesFileName, int &ndegrees);
vector<vector<bool> > readNxNMatrix (std::string adj_mat_file_name);
vector<vector<double> > readCordinatesFile (std::string node_coordinates_file_name);
void printCoordinateArray (const char* description, vector<vector<double> > coord_array);
void printMatrix (const char* description, vector<vector<bool> > array);

NS_LOG_COMPONENT_DEFINE ("GenericTopologyCreation");

double basePacketRate = 10;
double GlobalPacketRate = 1; // "1KBps"
double CoordinationPacketRate = 1; // "1KBps"
double InternetPacketRate = 10; // "1KBps"

int main (int argc, char *argv[])
{
    //LogComponentEnableAll(LogLevel::LOG_INFO);

    // ---------- Simulation Variables ------------------------------------------

    // Change the variables and file names only in this block!

    double SimTime        = 3.00 + 8;
    double SinkStartTime  = 1.0001;
    double SinkStopTime   = 2.90001 + 8;
    double AppStartTime   = 2.0001;
    double AppStopTime    = 2.80001 + 8;

    std::stringstream ss;
    ss << (int)(basePacketRate * 1000);
    Config::SetDefault  ("ns3::OnOffApplication::PacketSize",StringValue (ss.str()));
    ss << "Bps";
    Config::SetDefault ("ns3::OnOffApplication::DataRate",  StringValue (ss.str()));
    std::string LinkRate ("10Mbps");
    std::string LinkDelay ("2ms");
    //  DropTailQueue::MaxPackets affects the # of dropped packets, default value:100
    //  Config::SetDefault ("ns3::DropTailQueue::MaxPackets", UintegerValue (1000));

    srand ( (unsigned)time ( NULL ) );   // generate different seed each time

    std::string tr_name ("scratch/output/20_n-node-ppp.tr");
    std::string pcap_name ("scratch/output/20_n-node-ppp");
    std::string flow_name ("scratch/output/20_n-node-ppp.xml");
    std::string anim_name ("scratch/output/20_n-node-ppp.anim.xml");

    std::string net_size_file_name ("scratch/output/10_network_size.txt");
    std::string adj_mat_file_name ("scratch/output/10_adjacency_matrix.txt");
    std::string node_coordinates_file_name ("scratch/output/10_node_coordinates.txt");
    std::string ndegreesFileName ("scratch/output/10_n_degrees.txt");
    std::string node_interfaces_name ("scratch/output/20_node_interfaces.txt");

    uint16_t coordinationPort = 9;
    uint16_t globalPort = 10;
    uint16_t inetPort = 11;

    // remove old files
    std::stringstream scmd;
    char cwdbuf[2048];
    scmd << "rm " << getcwd(cwdbuf, sizeof(cwdbuf)) << "/scratch/output/20_*";
    FILE* in = popen(scmd.str().c_str(), "r");
    pclose(in);

    CommandLine cmd (__FILE__);
    cmd.Parse (argc, argv);
    
    // ---------- End of Simulation Variables ----------------------------------

    // ---------- Read Adjacency Matrix ----------------------------------------

    vector<vector<bool> > Adj_Matrix;
    Adj_Matrix = readNxNMatrix (adj_mat_file_name);
    int ny, nx;
    readNetSize(net_size_file_name, ny, nx);
    int ndegrees;
    readNDegrees(ndegreesFileName, ndegrees);

    // Optionally display 2-dimensional adjacency matrix (Adj_Matrix) array
    // printMatrix (adj_mat_file_name.c_str (),Adj_Matrix);

    // ---------- End of Read Adjacency Matrix ---------------------------------

    // ---------- Read Node Coordinates File -----------------------------------

    vector<vector<double> > coord_array;
    coord_array = readCordinatesFile (node_coordinates_file_name);

    // Optionally display node co-ordinates file
    // printCoordinateArray (node_coordinates_file_name.c_str (),coord_array);

    int n_nodes = coord_array.size ();
    int matrixDimension = Adj_Matrix.size ();

    if (matrixDimension != n_nodes || nx*ny != n_nodes)
    {
        NS_FATAL_ERROR ("The number of lines in coordinate file is: " << n_nodes << " not equal to the number of nodes in adjacency matrix size " << matrixDimension);
    }

    // ---------- End of Read Node Coordinates File ----------------------------

    // ---------- Network Setup ------------------------------------------------

    NS_LOG_INFO ("Create Nodes.");

    NodeContainer nodes;   // Declare nodes objects
    nodes.Create (n_nodes);

    NS_LOG_INFO("Create P2P Link Attributes.");

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue(LinkRate));
    p2p.SetChannelAttribute("Delay", StringValue(LinkDelay));

    NS_LOG_INFO ("Install Internet Stack to Nodes.");

    InternetStackHelper internet;
    internet.Install (NodeContainer::GetGlobal ());

    NS_LOG_INFO ("Assign Addresses to Nodes.");

    Ipv4AddressHelper ipv4_n;
    ipv4_n.SetBase ("10.0.0.0", "255.255.255.252");

    NS_LOG_INFO ("Create Links Between Nodes.");

    uint32_t linkCount = 0;

    // Create a p2p link from node i to node j.
    // p2p links are bidirectional, so we only need connections from i to j, and not also from j to i.
    std::string ip_names[n_nodes][n_nodes];
    for (size_t i = 0; i < Adj_Matrix.size (); i++)
    {
        for (size_t j = 0; j < Adj_Matrix[i].size (); j++)
        {
            if (Adj_Matrix[i][j] == 1) // connection from i --to--> j
            {
                NodeContainer n_links = NodeContainer (nodes.Get (i), nodes.Get (j));
                NetDeviceContainer n_devs = p2p.Install (n_links);
                ipv4_n.Assign (n_devs);
                ipv4_n.NewNetwork ();
                linkCount++;
                NS_LOG_INFO ("matrix element [" << i << "][" << j << "] is 1");

                // track interface names
                for (uint32_t k = 0; k < 2; k++) {
                    Ptr<NetDevice> device = n_devs.Get(k);
                    Ptr<Ipv4> ipv4 = device->GetNode()->GetObject<Ipv4>();
                    int32_t interface = ipv4->GetInterfaceForDevice(device);
                    Ipv4Address addr = ipv4->GetAddress(interface, ipv4->GetNAddresses(interface)-1).GetAddress();
                    std::stringstream saddr;
                    saddr << addr;
                    if (k == 0) {
                        ip_names[i][j] = saddr.str();
                    } else {
                        ip_names[j][i] = saddr.str();
                    }
                }
            }
            else
            {
                NS_LOG_INFO ("matrix element [" << i << "][" << j << "] is 0");
            }
        }
    }
    NS_LOG_INFO ("Number of links in the adjacency matrix is: " << linkCount);
    NS_LOG_INFO ("Number of all nodes is: " << nodes.GetN ());
    
    // Output the ip addresses associated with each node, to make analysis of the network
    // easier at the end.
    ofstream fout;
    fout.open(node_interfaces_name, std::ios_base::openmode::_S_out);
    for (int i = 0; i < n_nodes; i++) {
        for (int j = 0; j < n_nodes; j++) {
            if (ip_names[i][j].length() > 0) {
                fout << ip_names[i][j] << " ";
            } else {
                fout << "x ";
            }
        }
        fout << "\n";
    }
    fout.close();

    NS_LOG_INFO ("Initialize Global Routing.");
    Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

    // ---------- End of Network Set-up ----------------------------------------

    // ---------- Allocate Node Positions --------------------------------------

    NS_LOG_INFO ("Allocate Positions to Nodes.");

    MobilityHelper mobility_n;
    Ptr<ListPositionAllocator> positionAlloc_n = CreateObject<ListPositionAllocator> ();

    for (size_t m = 0; m < coord_array.size (); m++)
    {
        positionAlloc_n->Add (Vector (coord_array[m][0], coord_array[m][1], 0));
        Ptr<Node> n0 = nodes.Get (m);
        Ptr<ConstantPositionMobilityModel> nLoc =  n0->GetObject<ConstantPositionMobilityModel> ();
        if (!nLoc)
        {
            nLoc = CreateObject<ConstantPositionMobilityModel> ();
            n0->AggregateObject (nLoc);
        }
        // y-coordinates are negated for correct display in NetAnim
        // NetAnim's (0,0) reference coordinates are located on upper left corner
        // by negating the y coordinates, we declare the reference (0,0) coordinate
        // to the bottom left corner
        Vector nVec (coord_array[m][0], -coord_array[m][1], 0);
        nLoc->SetPosition (nVec);

    }
    mobility_n.SetPositionAllocator (positionAlloc_n);
    mobility_n.Install (nodes);

    // ---------- End of Allocate Node Positions -------------------------------

    // ---------- Create n*(n-1) CBR Flows -------------------------------------

    NS_LOG_INFO ("Setup Packet Sinks.");

    uint16_t ports[] = { coordinationPort, globalPort, inetPort };
    for (int i = 0; i < n_nodes; i++)
    {
        for (size_t pidx = 0; pidx < sizeof(ports)/sizeof(uint16_t); pidx++) {
            PacketSinkHelper sink ("ns3::UdpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), ports[pidx]));
            ApplicationContainer apps_sink = sink.Install (nodes.Get (i));   // sink is installed on all nodes
            apps_sink.Start (Seconds (SinkStartTime));
            apps_sink.Stop (Seconds (SinkStopTime));
        }
    }

    NS_LOG_INFO ("Setup CBR Traffic Sources.");

    for (int i = 0; i < n_nodes; i++)
    {
        int i_x = i % nx;
        int i_y = (i - i_x) / nx;
        for (int j = 0; j < n_nodes; j++)
        {
            int j_x = j % nx;
            int j_y = (j - j_x) / nx;

            // bursty coordination MMA traffic
            if (i == j) {
                continue;
            }
            
            // instead of doing a real path length check for degrees > 1, just check for the first degree
            // for nearly all cases this should be good enough and we don't have enough time to do it right
            if (ndegrees == 1 && !Adj_Matrix[i][j]) {
                continue;
            }

            // if we're within ndegrees of the node i, then generate a bursty MMA traffic connection
            if (abs(i_x - j_x) <= ndegrees && abs(i_y - j_y) <= ndegrees) {
                genOnOff(nodes, i, j, CoordinationPacketRate, AppStartTime, AppStopTime, coordinationPort, true);
            }
        }

        // constant internet traffic
        // genOnOff(nodes, i, j, InternetPacketRate, AppStartTime, AppStopTime, coordinationPort)
        // Don't actually simulate this, it is the same for every node.
        // Add this value in as a constant in post-processing.

        // generate the local, regional, and global broadcast packets
        // to simulate broadcasting, pick a j that is 1 degree away from i
        bool found = false;
        for (int x = -1; x <= 1; x++) {
            if (found) break;
            for (int y = -1; y <= 1; y++) {
                if (found) break;

                int j = y * nx + x;
                if (j < 0 || j >= n_nodes) continue;
                if (i == j) continue;
                if (Adj_Matrix[i][j]) {
                    found = true;
                    for (int k = 0; k < 3; k++) {
                        genOnOff(nodes, i, j, GlobalPacketRate, AppStartTime, AppStopTime, globalPort);
                    }
                }
            }
        }
    }

    // ---------- End of Create n*(n-1) CBR Flows ------------------------------

    // ---------- Simulation Monitoring ----------------------------------------

    NS_LOG_INFO ("Configure Tracing.");

    AsciiTraceHelper ascii;
    // p2p.EnableAsciiAll (ascii.CreateFileStream (tr_name));
    p2p.EnablePcapAll (pcap_name);

    // Ptr<FlowMonitor> flowmon;
    // FlowMonitorHelper flowmonHelper;
    // flowmon = flowmonHelper.InstallAll ();

    // Configure animator with default settings

    // AnimationInterface anim (anim_name);
    NS_LOG_INFO ("Run Simulation.");

    Simulator::Stop (Seconds (SimTime));
    Simulator::Run ();
    // flowmon->SerializeToXmlFile (flow_name.c_str(), true, true);
    Simulator::Destroy ();

    // ---------- End of Simulation Monitoring ---------------------------------

    // runPythonFile("scratch/python/20_parse_pcaps.py");

    return 0;

}

// ---------- Function Definitions -------------------------------------------

void genOnOff(NodeContainer nodes, int from, int to, double packetRate, double startTime, double stopTime, uint16_t port, bool isExponential)
{
    // We needed to generate a random number (rn) to be used to eliminate
    // the artificial congestion caused by sending the packets at the
    // same time. This rn is added to AppStartTime to have the sources
    // start at different time, however they will still send at the same rate.
    static Ptr<UniformRandomVariable> rand = CreateObject<UniformRandomVariable> ();
    static bool initialized = false;
    if (!initialized) {
        rand->SetAttribute ("Min", DoubleValue (0));
        rand->SetAttribute ("Max", DoubleValue (1));
        initialized = true;
    }
    double rn = rand->GetValue ();

    // get the "to" node
    Ptr<Node> toNode = nodes.Get (to);
    Ptr<Ipv4> toIpv4 = toNode->GetObject<Ipv4> ();
    Ipv4InterfaceAddress toIpv4_int_addr = toIpv4->GetAddress (1, 0);
    Ipv4Address toIp_addr = toIpv4_int_addr.GetLocal ();

    // build the onOff generator
    OnOffHelper onoff ("ns3::UdpSocketFactory", InetSocketAddress (toIp_addr, port)); // traffic flows from node[i] to node[j]
    if (isExponential) {
        std::stringstream ss;
        ss << "ns3::ExponentialRandomVariable[Mean=" << (packetRate / 2) << "]";
        onoff.SetAttribute ("OnTime", StringValue (ss.str()));
        ss.clear();
        ss << "ns3::ExponentialRandomVariable[Mean=" << (1.0 - (packetRate / 2)) << "]";
        onoff.SetAttribute ("OffTime",StringValue (ss.str()));
    } else {
        std::stringstream ss;
        ss << packetRate;
        onoff.SetConstantRate (DataRate (ss.str()));
    }

    // install on the "from" node
    ApplicationContainer apps = onoff.Install (nodes.Get (from));  // traffic sources are installed on all nodes
    apps.Start (Seconds (startTime + rn));
    apps.Stop (Seconds (stopTime));
}

void runPythonFile(std::string filename)
{
    std::stringstream scmd;
    char cwdbuf[2048];
    scmd << "python " << filename << " " << getcwd(cwdbuf, sizeof(cwdbuf)) << "/scratch";
    FILE* in = popen(scmd.str().c_str(), "r");
    pclose(in);
}

void readNetSize(std::string netSizeFileName, int &ny, int &nx)
{
    ifstream netSizeFile;
    netSizeFile.open(netSizeFileName.c_str(), ios::in);
    if (netSizeFile.fail ())
    {
        NS_FATAL_ERROR ("File " << netSizeFileName.c_str () << " not found");
    }

    std::string line;
    getline(netSizeFile, line);
    ny = atoi(line.c_str());
    getline(netSizeFile, line);
    nx = atoi(line.c_str());

    netSizeFile.close();
}

void readNDegrees(std::string netSizeFileName, int &ndegrees)
{
    ifstream netSizeFile;
    netSizeFile.open(netSizeFileName.c_str(), ios::in);
    if (netSizeFile.fail ())
    {
        NS_FATAL_ERROR ("File " << netSizeFileName.c_str () << " not found");
    }

    std::string line;
    getline(netSizeFile, line);
    ndegrees = atoi(line.c_str());

    netSizeFile.close();
}

vector<vector<bool> > readNxNMatrix (std::string adj_mat_file_name)
{
    ifstream adj_mat_file;
    adj_mat_file.open (adj_mat_file_name.c_str (), ios::in);
    if (adj_mat_file.fail ())
    {
        NS_FATAL_ERROR ("File " << adj_mat_file_name.c_str () << " not found");
    }
    vector<vector<bool> > array;
    int i = 0;
    int n_nodes = 0;

    while (!adj_mat_file.eof ())
    {
        string line;
        getline (adj_mat_file, line);
        if (line == "")
        {
            NS_LOG_WARN ("WARNING: Ignoring blank row in the array: " << i);
            break;
        }

        istringstream iss (line);
        bool element;
        vector<bool> row;
        int j = 0;

        while (iss >> element)
        {
            row.push_back (element);
            j++;
        }

        if (i == 0)
        {
            n_nodes = j;
        }

        if (j != n_nodes )
        {
            NS_LOG_ERROR ("ERROR: Number of elements in line " << i << ": " << j << " not equal to number of elements in line 0: " << n_nodes);
            NS_FATAL_ERROR ("ERROR: The number of rows is not equal to the number of columns! in the adjacency matrix");
        }
        else
        {
            array.push_back (row);
        }
        i++;
    }

    if (i != n_nodes)
    {
        NS_LOG_ERROR ("There are " << i << " rows and " << n_nodes << " columns.");
        NS_FATAL_ERROR ("ERROR: The number of rows is not equal to the number of columns! in the adjacency matrix");
    }

    adj_mat_file.close ();
    return array;

}

vector<vector<double> > readCordinatesFile (std::string node_coordinates_file_name)
{
    ifstream node_coordinates_file;
    node_coordinates_file.open (node_coordinates_file_name.c_str (), ios::in);
    if (node_coordinates_file.fail ())
    {
        NS_FATAL_ERROR ("File " << node_coordinates_file_name.c_str () << " not found");
    }
    vector<vector<double> > coord_array;
    int m = 0;

    while (!node_coordinates_file.eof ())
    {
        string line;
        getline (node_coordinates_file, line);

        if (line == "")
        {
            NS_LOG_WARN ("WARNING: Ignoring blank row: " << m);
            break;
        }

        istringstream iss (line);
        double coordinate;
        vector<double> row;
        int n = 0;
        while (iss >> coordinate)
        {
            row.push_back (coordinate);
            n++;
        }

        if (n != 2)
        {
            NS_LOG_ERROR ("ERROR: Number of elements at line#" << m << " is "  << n << " which is not equal to 2 for node coordinates file");
            exit (1);
        }

        else
        {
            coord_array.push_back (row);
        }
        m++;
    }
    node_coordinates_file.close ();
    return coord_array;

}

void printMatrix (const char* description, vector<vector<bool> > array)
{
    cout << "**** Start " << description << "********" << endl;
    for (size_t m = 0; m < array.size (); m++)
    {
        for (size_t n = 0; n < array[m].size (); n++)
        {
            cout << array[m][n] << ' ';
        }
        cout << endl;
    }
    cout << "**** End " << description << "********" << endl;

}

void printCoordinateArray (const char* description, vector<vector<double> > coord_array)
{
    cout << "**** Start " << description << "********" << endl;
    for (size_t m = 0; m < coord_array.size (); m++)
    {
        for (size_t n = 0; n < coord_array[m].size (); n++)
        {
            cout << coord_array[m][n] << ' ';
        }
        cout << endl;
    }
    cout << "**** End " << description << "********" << endl;

}

// ---------- End of Function Definitions ------------------------------------
