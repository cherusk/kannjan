Title: rsync or cp over net based file systems
Date: 2016-08-16 01:00
Author: cherusk
Category: Systems Engineering 
Tags: comparison, cp, data migration, genbackupdata, ibvirt, KVM/Qemu, linux, networking, nfs, performance, rsync, virt-builder, vs
Slug: rsync-or-cp-over-net-based-file-systems
Status: published
Attachments: 2016/08/setup.png

Question
========

Skimming the net with all thinkable efforts I could find some passionately led discussions and interesting articles about cp and rsync performance comparisons. Foremost [LWN-CP-RSYNC](https://lwn.net/Articles/400489/) raised my attention for it promising in a technically perfect manner a more than doubling of throughput when opting for coreutils' cp in default local data migration setups instead for rsync.  For me being a Data Centre engineer,  I was wondering if cp would still outperform rsync when data is to be beamed over non-local, net based file systems. Although being vividly discussed, I could not find any recent and reliabe data to that topic online. I expected the for the local migration measured  findings to hold for net based file systems because of the minimalistic data pushing facilities of cp and the a little more complex architecture and algorithms of rsync. I did not consider cat or cpio here since both seem to show the more or less same performance level as cp.

Setup
=====

I chose a minimal but still lifelike enough setup to compare the two tools. All components were based on [KVM/Qemu](http://www.linux-kvm.org/page/Main_Page)  were controlled and run with [libvirt](http://wiki.libvirt.org/page/Main_Page) mechanism, especially virsh. I won't go into detail about that is done as the respective docs are more exhaustive on that as I could. What I want to point out here is [virt-builder](http://libguestfs.org/virt-builder.1.html) of the libguestfs package which made creating the VMs quite comfortable and quick.

![setup]({static}2016/08/setup.png){.alignnone .size-full .wp-image-69 width="2132" height="883"}

Mainly, I opted for NFS as a network based FS as it is open and quickly and with ease to configure. Moreover, it's still quite widespread in data centres as well.

Basically, the two opensuse 42.1 based VMs were the NFS serving machines. The fedora24 Server Version VM had the NFS client data pushing role. Fedora ran on kernel 4.5.7-300.fc24.x86\_64, the suse ones on 4.1.12-1-default. All machines had 2024 MB phys. RAM and 1 phys. Processor.

The virsh brought up and not manually tweakd virtual net I tested with:

------------------------------------------------------------------------

**\[root@suse42\_n1 \~\]\# iperf3 -s**

**\[root@fedora24 \~\]\# iperf3 -c suse42\_n1**

**\[...\]**

**- - - - - - - - - - - - - - - - - - - - - - - - -**

**\[ ID\] Interval Transfer Bandwidth Retr**

**\[ 4\] 0.00-10.00 sec 2.78 GBytes 2.39 Gbits/sec 15859 sender**

**\[ 4\] 0.00-10.00 sec 2.78 GBytes 2.39 Gbits/sec receiver**

------------------------------------------------------------------------

So not the fastest connection one seen in data centres but representative enough for the comparison.

The data source and sinks were **5GB** large Virtio-Disks with BTRFS on them. Going for BTRFS was quite arbitrary since the local backend FS was not of to much of avail for the comparison.

The mounts:

------------------------------------------------------------------------

**\[root@fedora24 \~\]\# nfsstat -m**  
**/source from suse42\_n1:/source**  
**Flags: rw,relatime,vers=4.2,rsize=262144,wsize=262144,namlen=255,hard,proto=tcp,port=0,**

**timeo=600,retrans=2,sec=sys,clientaddr=192.168.122.89,local\_lock=none,addr=192.168.122.158**

**/sink from suse42\_n2:/sink**  
**Flags: rw,relatime,vers=4.2,rsize=262144,wsize=262144,namlen=255,hard,proto=tcp,port=0,**

**timeo=600,retrans=2,sec=sysclientaddr,=192.168.122.89,local\_lock=none,addr=192.168.122.52**

------------------------------------------------------------------------

Approach
========

All the action was on the fedora24 node for it being the data pushing entity. I decided to have several runs with different data constellations in /source. [genbackupdata](http://linux.die.net/man/1/genbackupdata) was my tool of choice for data generation although not fully working. It promises files with distributed shape, but it can produce files only uniformly. Its **--delete**, **--rename**, or **--modify** flags were somehow not implemented. Still, a good choice to create random data.

I went for 6 runs and generated for each.

------------------------------------------------------------------------

**genbackupdata --create=SIZE \[--chunk-size=C\_SIZE\] \[--file-size=F\_SIZE\] --depth=3 /source/**

<table class="tg">
<tbody>
<tr>
<th class="tg-9hbo">
SIZE

</th>
<th class="tg-9hbo">
C\_SIZE

</th>
<th class="tg-9hbo">
F\_SIZE

</th>
<th class="tg-9hbo">
Gen. Files

</th>
</tr>
<tr>
<td class="tg-baqh" rowspan="3">
100M

</td>
<td class="tg-baqh">
-

</td>
<td class="tg-baqh">
-

</td>
<td class="tg-baqh">
2M

</td>
</tr>
<tr>
<td class="tg-baqh">
80000

</td>
<td class="tg-baqh">
80000

</td>
<td class="tg-baqh">
10M

</td>
</tr>
<tr>
<td class="tg-baqh">
160000

</td>
<td class="tg-baqh">
160000

</td>
<td class="tg-baqh">
20M

</td>
</tr>
<tr>
<td class="tg-baqh" rowspan="3">
500M

</td>
<td class="tg-baqh">
-

</td>
<td class="tg-baqh">
-

</td>
<td class="tg-baqh">
2M

</td>
</tr>
<tr>
<td class="tg-baqh">
80000

</td>
<td class="tg-baqh">
80000

</td>
<td class="tg-baqh">
10M

</td>
</tr>
<tr>
<td class="tg-baqh">
160000

</td>
<td class="tg-baqh">
160000

</td>
<td class="tg-baqh">
20M

</td>
</tr>
</tbody>
</table>
For instance for **genbackupdata --create=100M** we get:

**matthias@suse42\_n1:\~&gt; du -h /source/**  
**2,1M    /source/0/0/0/0/0**  
**2,0M    /source/0/0/0/0/1**  
**2,1M    /source/0/0/0/0/6**  
**2,1M    /source/0/0/0/0/2**  
**\[...\]**  
**17M    /source/0/0/0**  
**17M    /source/0/0**  
**17M    /source/0**  
**100M    /source/**

------------------------------------------------------------------------

Before every run I diligently cleaned up all the caches:

------------------------------------------------------------------------

**echo 1 &gt; /proc/sys/vm/drop\_caches**  
**echo 2 &gt; /proc/sys/vm/drop\_caches**  
**echo 3 &gt; /proc/sys/vm/drop\_caches**  
**swapoff -a**  
**sync**

------------------------------------------------------------------------

I tracked every run:

------------------------------------------------------------------------

**time -a -o measurem -f "real %e user %U sys %S avg-io-pg-fault %F fs-in %I fs-out %O avg-mem %K max-resident %M avg-res %t cpu %P% "**

------------------------------------------------------------------------

The CMD itself and intermediate steps abstractly:

1.  run copy
2.  pollute source to make delta sync necessary
3.  run sync
4.  cleanup /sink

and  in practice then:

------------------------------------------------------------------------

-    RSYNC:
    1.  **rsync -aHv --no-whole-file --progress /source/ /sink**
    2.  **find [<span style="color:#3465a4;">/etc/</span>](///etc/) -type f | sort -R input | head -n 50 | xargs echo "\`head -c 20 [<span style="color:#3465a4;">/dev/urandom\`"</span>](///dev/urandom%60%22) &gt;&gt; {}**
    3.  **rsync -aHv --no-whole-file --progress /source/ /sink**
    4.  **rm -r /sink/\***
-   CP**:**
    1.  **cp -au /source/cp -au /source/\* /sink/\* /sink/**
    2.  **find [<span style="color:#3465a4;">/etc/</span>](///etc/) -type f | sort -R input | head -n 50 | xargs echo "\`head -c 20 [<span style="color:#3465a4;">/dev/urandom\`"</span>](///dev/urandom%60%22) &gt;&gt; {}**
    3.  **rsync -aHv --no-whole-file --progress /source/ /sink**
    4.  **rm -r /sink/\***

------------------------------------------------------------------------

Outcome
=======

The table does not show CPU usage, since that was for all runs **&lt;5%** for cp and **near 20 %** for rsync. Therefore, the net was mainly the bottleneck, as expected.

<table class="tg">
<tbody>
<tr>
<th class="tg-031e">
Data Mass

</th>
<th class="tg-yw4l">
Filesize

</th>
<th class="tg-yw4l">
Tool

</th>
<th class="tg-031e">
Elapsed

</th>
<th class="tg-031e">
Sys

</th>
<th class="tg-031e">
User

</th>
</tr>
<tr>
<td class="tg-031e" rowspan="12">
100M

</td>
<td class="tg-kjho" rowspan="4">
2M

</td>
<td class="tg-yzt1" rowspan="2">
RSYNC

</td>
<td class="tg-031e">
229.15

</td>
<td class="tg-031e">
2.91

</td>
<td class="tg-031e">
0.80

</td>
</tr>
<tr>
<td class="tg-yw4l">
1.34

</td>
<td class="tg-yw4l">
0.20

</td>
<td class="tg-yw4l">
0.02

</td>
</tr>
<tr>
<td class="tg-d1kj" rowspan="2">
CP

</td>
<td class="tg-yw4l">
272.85

</td>
<td class="tg-yw4l">
1.86

</td>
<td class="tg-yw4l">
0.26

</td>
</tr>
<tr>
<td class="tg-yw4l">
1.72

</td>
<td class="tg-yw4l">
0.25

</td>
<td class="tg-yw4l">
0.02

</td>
</tr>
<tr>
<td class="tg-achz" rowspan="4">
10M

</td>
<td class="tg-yzt1" rowspan="2">
RSYNC

</td>
<td class="tg-yw4l">
51.02

</td>
<td class="tg-yw4l">
0.79

</td>
<td class="tg-yw4l">
0.51

</td>
</tr>
<tr>
<td class="tg-yw4l">
0.26

</td>
<td class="tg-yw4l">
0.03

</td>
<td class="tg-yw4l">
0.00

</td>
</tr>
<tr>
<td class="tg-d1kj" rowspan="2">
CP

</td>
<td class="tg-yw4l">
53.00

</td>
<td class="tg-yw4l">
0.38

</td>
<td class="tg-yw4l">
0.04

</td>
</tr>
<tr>
<td class="tg-yw4l">
0.26

</td>
<td class="tg-yw4l">
0.04

</td>
<td class="tg-yw4l">
0.00

</td>
</tr>
<tr>
<td class="tg-7crq" rowspan="4">
20M

</td>
<td class="tg-yzt1" rowspan="2">
RSYNC

</td>
<td class="tg-yw4l">
30.42

</td>
<td class="tg-yw4l">
0.52

</td>
<td class="tg-yw4l">
0.47

</td>
</tr>
<tr>
<td class="tg-yw4l">
0.15

</td>
<td class="tg-yw4l">
0.02

</td>
<td class="tg-yw4l">
0.00

</td>
</tr>
<tr>
<td class="tg-d1kj" rowspan="2">
CP

</td>
<td class="tg-yw4l">
28.59

</td>
<td class="tg-yw4l">
0.20

</td>
<td class="tg-yw4l">
0.03

</td>
</tr>
<tr>
<td class="tg-yw4l">
0.14

</td>
<td class="tg-yw4l">
0.02

</td>
<td class="tg-yw4l">
0.000

</td>
</tr>
<tr>
<td class="tg-031e" rowspan="12">
500M

</td>
<td class="tg-kjho" rowspan="4">
2M

</td>
<td class="tg-yzt1" rowspan="2">
RSYNC

</td>
<td class="tg-031e">
1022.57

</td>
<td class="tg-031e">
13.85

</td>
<td class="tg-031e">
4.17

</td>
</tr>
<tr>
<td class="tg-yw4l">
6.48

</td>
<td class="tg-yw4l">
0.96

</td>
<td class="tg-yw4l">
0.11

</td>
</tr>
<tr>
<td class="tg-d1kj" rowspan="2">
CP

</td>
<td class="tg-yw4l">
957.04

</td>
<td class="tg-yw4l">
7.73

</td>
<td class="tg-yw4l">
0.99

</td>
</tr>
<tr>
<td class="tg-yw4l">
6.22

</td>
<td class="tg-yw4l">
0.95

</td>
<td class="tg-yw4l">
0.09

</td>
</tr>
<tr>
<td class="tg-achz" rowspan="4">
10M

</td>
<td class="tg-yzt1" rowspan="2">
RSYNC

</td>
<td class="tg-yw4l">
244.52

</td>
<td class="tg-yw4l">
3.63

</td>
<td class="tg-yw4l">
2.54

</td>
</tr>
<tr>
<td class="tg-yw4l">
1.26

</td>
<td class="tg-yw4l">
0.02

</td>
<td class="tg-yw4l">
0.19

</td>
</tr>
<tr>
<td class="tg-d1kj" rowspan="2">
CP

</td>
<td class="tg-yw4l">
243.73

</td>
<td class="tg-yw4l">
1.81

</td>
<td class="tg-yw4l">
0.21

</td>
</tr>
<tr>
<td class="tg-yw4l">
1.30

</td>
<td class="tg-yw4l">
0.19

</td>
<td class="tg-yw4l">
0.01

</td>
</tr>
<tr>
<td class="tg-7crq" rowspan="4">
20M

</td>
<td class="tg-yw4l" rowspan="2">
RSYNC

</td>
<td class="tg-yw4l">
142.88

</td>
<td class="tg-yw4l">
2.69

</td>
<td class="tg-yw4l">
2.30

</td>
</tr>
<tr>
<td class="tg-yw4l">
0.62

</td>
<td class="tg-yw4l">
0.09

</td>
<td class="tg-yw4l">
0.01

</td>
</tr>
<tr>
<td class="tg-d1kj" rowspan="2">
CP

</td>
<td class="tg-yw4l">
132.73

</td>
<td class="tg-yw4l">
0.95

</td>
<td class="tg-yw4l">
0.08

</td>
</tr>
<tr>
<td class="tg-yw4l">
0.67

</td>
<td class="tg-yw4l">
0.10

</td>
<td class="tg-yw4l">
0.00

</td>
</tr>
</tbody>
</table>

------------------------------------------------------------------------

**\[root@fedora24 \~\]\# nfsiostat**

**suse42\_n2:/sink mounted on /sink:**

**ops/s rpc bklog**

**101.887 0.000**

**read: ops/s kB/s kB/op retrans avg RTT (ms) avg exe (ms)**

**3.138 51.153 16.300 0 (0.0%) 0.549 0.560**

**write: ops/s kB/s kB/op retrans avg RTT (ms) avg exe (ms)**

**6.654 109.051 16.389 0 (0.0%) 34.072 34.098**

**suse42\_n1:/source mounted on /source:**

**ops/s rpc bklog**

**79.758 0.000**

**read: ops/s kB/s kB/op retrans avg RTT (ms) avg exe (ms)**

**5.091 82.983 16.300 0 (0.0%) 0.730 0.740**

**write: ops/s kB/s kB/op retrans avg RTT (ms) avg exe (ms)**

**4.714 77.251 16.389 0 (0.0%) 25.937 25.960**

------------------------------------------------------------------------

I stopped here because I conceived no further insights could be made by having more runs. I am prepared to get corrected on that.

Conclusion
==========

Some insights I got herefrom were as expected. Others quite surprised me. I did not expect that the delta sync after a cp would be only **\~10-15%** percent less performant than the sync after a preceding rsync approach. Moreover, I expected both tools to have hard times when it comes to migrating small files, but I honestly fathomed cp to outstrip rsync here clearly. It does not. cp shows to be ahead when it comes to larger files. But still, the difference is not astoundingly significant so to speak. That may deviate with real hugely whopping files, what I may look into deeper.  What I mainly take away for me is, that in the **average real world case** it does not really matter which tool to choose for migrating data when  performance aspects with respects to network based file systems play a role. Coreutils' cp does not necessarly outperform rsync over network based file systems.
