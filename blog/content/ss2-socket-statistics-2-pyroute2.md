Title: ss2 - Socket Statistics 2 (pyroute2)
Date: 2018-09-18 13:29
Author: cherusk
Category: LNX Systems Engineering
Tags: automation, flows, json, kernel, linux, linux engineering, machine readable, metrics, network stack, python, socket, statistics, tcp flows, tcp/ip, tool, utility
Slug: ss2-socket-statistics-2-pyroute2
Status: published

Gist
----

Disseminating a complementary and viably a more modern alternative to the established **ss** utility shipped with the well-known **iproute** package.

#### How to attain ss2?

It's part of the [pyroute2 package install routines](https://github.com/svinota/pyroute2), so please follow those upstream to allow me to reduce redundancy in this regard.

#### Example Run

**ss2** is offering, amongst many output formats, machine readable dumps of the kernel socket statistics. For it's renowned merits, json was chosen as the foremost default dumping format.

Mission is to proffer to the user of it everything the kernel can actually export as context to sockets.

Currently, as it is in its infancy, so not all aspects provided by ss have been implemented yet.

```
# ss2 --help
  
 usage: ss2 [-h] [-x] [-t] [-l] [-a] [-p] [-r]ss2 - socket statistics depictor meant as a complete and convenient surrogate 
 for iproute2/misc/ss2optional arguments: 
 -h, --help show this help message and exit 
 -x, --unix Display Unix domain sockets. 
 -t, --tcp Display TCP sockets. 
 -l, --listen Display listening sockets. 
 -a, --all Display all sockets. 
 -p, --process show socket holding context 
 -r, --resolve resolve host names in addition 
```

     

On a recent kernel (4.17.19-200.fc28.x86\_64), following schema could be expected for TCP flows:

```  
# ss2 -t
{  
    "TCP": {  
        "flows": [  
            {  
                "src": "10.0.2.15",  
                "src_port": 43332,  
                "retrans": 0,  
                "dst": "172.25.136.144",  
                "cong_algo": "cubic",  
                "dst_port": 22,  
                "meminfo": {  
                    "r": 0,  
                    "t": 0,  
                    "w": 0,  
                    "f": 4096  
                },  
                "iface_idx": 0,  
                "inode": 45433,  
                "tcp_info": {  
                    "delivery_rate": 5615384,  
                    "retrans": 0,  
                    "data_segs_in": 19,  
                    "rto": 201.0,  
                    "segs_in": 35,  
                    "rtt": 0.943,  
                    "retransmits": 0,  
                    "bytes_received": 5349,  
                    "last_ack_sent": 0,  
                    "rcv_space": 29200,  
                    "rcv_mss": 1420,  
                    "max_pacing_rate": 18446744073709551615,  
                    "ca_state": 0,  
                    "min_rtt": 260,  
                    "segs_out": 26,  
                    "advmss": 1460,  
                    "state": "established",  
                    "last_ack_recv": 113749,  
                    "snd_wscale": 0,  
                    "pmtu": 1500,  
                    "busy_time": 8000,  
                    "bytes_acked": 5630,  
                    "rcv_ssthresh": 49800,  
                    "total_retrans": 0,  
                    "last_data_recv": 113749,  
                    "unacked": 0,  
                    "fackets": 0,  
                    "sndbuf_limited": 0,  
                    "sacked": 0,  
                    "reordering": 3,  
                    "pacing_rate": 30944495,  
                    "rttvar": 0.859,  
                    "snd_cwnd": 10,  
                    "last_data_sent": 113995,  
                    "null": 0,  
                    "rcv_wscale": 0,  
                    "probes": 0,  
                    "notsent_bytes": 0,  
                    "data_segs_out": 15,  
                    "snd_ssthresh": null,  
                    "lost": 0,  
                    "ato": 40.0,  
                    "rwnd_limited": 0,  
                    "rcv_rtt": 0.0,  
                    "delivery_rate_app_limited": 1,  
                    "snd_mss": 1460,  
                    "opts": []  
                }  
            }  
        ]  
    }  
}  
```
