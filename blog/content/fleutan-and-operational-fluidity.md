Title: Fleutan - and operational FLUIDITY
Date: 2017-08-19 10:11
Author: cherusk
Category: LNX Network Engineering Research
Tags: analysis, bandwith product, bcc, correlation, cwnd, ebpf, flow grouping, flowing, flowing engineering, introspection, kernel, linux, linux engineering, mechanism, net traversal, network paths, network stack, networking, operations, perf, performance, python, qdisc, research, resource usage, ss, stack config, statistics, suite, system operations, tcp, tcp flows, tcp/ip, tool, traffic flows, traffic volume, trouble shooting, Tuning, user land
Slug: fleutan-and-operational-fluidity
Status: published
Attachments: 2017/08/logo.png

<!--[Influence on GitHub](https://github.com/cherusk/fleutan)-->
<!--=========================================================-->

![logo]({static}2017/08/logo.png){.alignnone .size-full .wp-image-2340 width="1400" height="1183"}

Notion
------

What is Fleutan? It's meant as a general tooling suite around all sort of flowing connected apparitions on unixoid systems (especially linux). Though, it's far from complete and should meanwhile rather been seen as a first illustrating radicales to show the desire for standardized open meta tooling suits around advanced network concepts in unxoid systems. The purpose was also not to compete with anything around in this area but rather either augment (install operators with wieldability) it or complement it, since brilliant suits and low level tooling is amplesomely around in the open wild.

**NB**: This blog is rather meant as another tentacle to make the Project conveniently spottable and therefore rather sparse in order to prevent forming a duplicate of the Github appearance. Look for link at the top. Moreover, I gave a similar outline on [quora](https://www.quora.com/unanswered/Endpoint-focussed-Scalable-Flows-Paths-wielding).

Use Cases
---------

Nominally, one would spin a <span class="inline_editor_value"><span class="rendered_qtext">SDN or comparable technologies allowing to take track of traffic as a minimum granularity on flow level as Fleutan does. In other words, some more or less centric component would do the aggregation and analysis in a holistic manner. Depending on the detail gathering strategies of a centric solution, though, for nifty trouble shooting or network related performance tuning decisions, only a closer look on the end nodes in scope makes a sane action taking or correlation tangible.  
</span></span>

E.g., let's take a look at convenient way to see the associativity between active network processing entities (processes) and the cpu core usage distribution with Fleutan over time. This example is trivial, but it illustrates that from this one can quickly get an overview for which network intensive processes for instance affinity tunings on a global manner are profitable to performance. In this case, the firefox processes are rather dancing around and could be tuned.

>     # fleutan flows --cpu -i 5
>     ~>/usr/lib/thunderbird/thunderbird(2847)
>     tcp              192.168.10.50#34718                     212.227.17.170#993
>     tcp              192.168.10.50#55258                     194.25.134.115#993
>     ___
>
>     ####################################################################################################
>     *************************************************************************          100.00          0
>                                                                                          0.00          1
>                                                                                          0.00          2
>                                                                                          0.00          3
>                                                                                          0.00          4
>                                                                                          0.00          5
>                                                                                          0.00          6
>                                                                                          0.00          7
>     ...
>     ~>hexchat(11290)
>     tcp       2003:62:4655:968b:18d0:33a6:3314:7c7#34482               2001:5a0:3604:1:64:86:243:181#6667
>     tcp       2003:62:4655:968b:18d0:33a6:3314:7c7#38930               2a02:2f0d:bff0:1:81:18:73:123#6667
>     tcp       2003:62:4655:968b:18d0:33a6:3314:7c7#35660                 2605:ac00:0:39::38#6697
>     ___
>
>     ####################################################################################################
>                                                                                          0.00          0
>                                                                                          0.00          1
>                                                                                          0.00          2
>                                                                                          0.00          3
>     *************************************************************************          150.00          4
>                                                                                          0.00          5
>                                                                                          0.00          6
>                                                                                          0.00          7
>     ...
>     ~>/usr/lib/firefox/firefox(11181)
>     tcp       2003:62:4655:968b:18d0:33a6:3314:7c7#59780                2a00:1450:4021:c::b#443
>     tcp       2003:62:4655:968b:18d0:33a6:3314:7c7#59774                2a00:1450:4021:c::b#443
>     tcp       2003:62:4655:968b:18d0:33a6:3314:7c7#44950               2a00:1450:4001:81f::200e#443
>     ___
>
>     ####################################################################################################
>     ************************                                                            15.00          0
>     **************                                                                       9.00          1
>     ***************************************                                             24.00          2
>     *****************************                                                       18.00          3
>     ****                                                                                 3.00          4
>                                                                                          0.00          5
>     **************************************************************************          45.00          6
>     ***********************************************************                         36.00          7

On top, might wants to rebalance the flowing activity being currently gushed out of the network stack  over the different queueing discipline instances on the egress side of the stack.

>     # fleutan flows -q -i 5
>
>     qdisc queues #>
>     load (bytes) per qu
>     ####################################################################################################
>     ███████████████████████                                                              0.3K          0
>     ██████████████████████████████████████████████████████████████████████████          1.00K          1
>     ----
>
>     flowing volumes per qu ##>
>     0
>     #######################################################################################################################################################
>     ████                                                         66.00                 192.168.10.50#47956         91.1.49.97#80                         
>     █████                                                        78.00                            ::#58                      ::#0                          
>     ██████                                                       86.00          2003:62:4625:d1a4:a166:cf47:30a6:e612#51358 2a00:1450:4001:80b::200a#80    
>     ██████                                                       86.00          2003:62:4625:d1a4:a166:cf47:30a6:e612#51360 2a00:1450:4001:80b::200a#80    
>
>     ----
>     flowing volumes per qu ##>
>     1
>     #######################################################################################################################################################
>     ██████                                                       86.00          2002:22:4625:d1a4:a166:cf47:30a6:e612#51360 2a00:1450:4001:80b::200a#80    
>     ███████                                                     112.00                 192.168.10.50#43660        192.111.249.9#443                        
>     ████████████                                                172.00          2003:62:4625:d1a4:a166:cf47:30a6:e612#55834 2a02:26f0:fc::5c7a:317c#80     
>     ██████████████████████████████████████████████████          710.00          2003:62:4625:d1a4:a166:cf47:30a6:e612#54292 2a00:1450:4001:819::200e#443   

For further examples, please visit the Github appearance.

Thinkable Outlook
-----------------

-   incorporation into current open monitoring/analysis solutions like the ELK stack solution, namely as a backend mechanism to gather flowing related stats
-   growing several APIs to it or turning parts of it to a generic library to make it's purpose spinnable from different technologies
-   having a look at growing RDMA flowing and incoroporate it into the suite


