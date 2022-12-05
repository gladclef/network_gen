# parse pcap files into .csv files

import os
import sys
import glob
import re


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} scratch_dir")
        return
    scratch_dir = sys.argv[1]
    os.chdir(os.path.join(scratch_dir, "output"))

    rconn = re.compile(r".*ppp-(\d+)-(\d+)\.pcap")
    for file in glob.glob("20_*.pcap"):
        match = rconn.match(file)
        if match is None:
            continue

        node = int(match.groups()[0])
        interface = int(match.groups()[1])

        # all tshark output options:
        # -e ip.src -e ip.dst -e ip.len -e ip.flags.df -e ip.flags.mf -e ip.fragment -e ip.fragment.count -e ip.fragments -e ip.ttl -e ip.proto -e tcp.window_size -e tcp.ack -e tcp.seq -e tcp.len -e tcp.stream -e tcp.urgent_pointer -e tcp.flags -e tcp.analysis.ack_rtt -e tcp.segments -e tcp.reassembled.length -e ssl.handshake -e ssl.record -e ssl.record.content_type -e ssl.handshake.cert_url.url_len -e ssl.handshake.certificate_length -e ssl.handshake.cert_type -e ssl.handshake.cert_type.type -e ssl.handshake.cert_type.types -e ssl.handshake.cert_type.types_len -e ssl.handshake.cert_types -e ssl.handshake.cert_types_count -e dtls.handshake.extension.len -e dtls.handshake.extension.type -e dtls.handshake.session_id -e dtls.handshake.session_id_length -e dtls.handshake.session_ticket_length -e dtls.handshake.sig_hash_alg_len -e dtls.handshake.sig_len -e dtls.handshake.version -e dtls.heartbeat_message.padding -e dtls.heartbeat_message.payload_length -e dtls.heartbeat_message.payload_length.invalid -e dtls.record.content_type -e dtls.record.content_type -e dtls.record.length -e dtls.record.sequence_number -e dtls.record.version -e dtls.change_cipher_spec -e dtls.fragment.count -e dtls.handshake.cert_type.types_len -e dtls.handshake.certificate_length -e dtls.handshake.certificates_length -e dtls.handshake.cipher_suites_length -e dtls.handshake.comp_methods_length -e dtls.handshake.exponent_len -e dtls.handshake.extension.len -e dtls.handshake.extensions_alpn_str -e dtls.handshake.extensions_alpn_str_len -e dtls.handshake.extensions_key_share_client_length -e http.request -e udp.port -e frame.time_relative -e frame.time_delta -e tcp.time_relative -e tcp.time_delta
        os.system(f"tshark -r {file} -T fields -e frame.time_relative -e ip.src -e ip.dst -e ip.len -E header=y -E separator=, -E quote=d -E occurrence=f > 20_pcap_ppp-{node}-{interface}.csv")

if __name__ == "__main__":
    main()