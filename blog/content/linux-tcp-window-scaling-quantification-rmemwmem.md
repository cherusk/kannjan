Title: Linux TCP - window scaling quantification | rmem,wmem
Date: 2017-08-24 11:49
Author: cherusk
Category:  LNX Network Engineering Research
Tags: bottle-neck, congestion control, core emulator, data series, explanation, flent, hint, interpretation, linux, network stack, research, scaling, tcp, tcp flows, tcp rmem, tcp wmem, testbed, transeive window scaling, Tuning
Slug: linux-tcp-window-scaling-quantification-rmemwmem
Status: published
Attachments: 2017/08/cdf_1.png, 2017/08/batch-2017-11-05t124309-tcp_scal_eval_fl_4_tcp_cwnd.png, 2017/08/box_1.png, 2017/08/batch-2017-11-05t143144-tcp_scal_eval_fl_8_non_cong_totals.png, 2017/08/total20.png, 2017/08/batch-2017-11-05t124309-tcp_scal_eval_fl_4_totals.png, 2017/08/batch-2017-11-05t143144-tcp_scal_eval_fl_8_non_cong_tcp_cwnd.png, 2017/08/batch-2017-11-05t121002-tcp_scal_eval_fl_1_box_totals.png, 2017/08/batch-2017-11-05t143144-tcp_scal_eval_fl_8_non_cong_box_totals.png, 2017/08/batch-2017-11-05t124309-tcp_scal_eval_fl_4_box_totals.png, 2017/08/batch-2017-11-05t125407-tcp_scal_eval_fl_20_totals.png, 2017/08/cdf4.png, 2017/08/total_1.png, 2017/08/screenshot-from-2017-08-23-18-12-35.png, 2017/08/box20.png, 2017/08/tcp_cwnd2.png, 2017/08/batch-2017-11-05t121002-tcp_scal_eval_fl_1_tcp_cwnd.png, 2017/08/batch-2017-11-05t124309-tcp_scal_eval_fl_4_ping_cdf.png, 2017/08/toal4.png, 2017/08/batch-2017-11-05t121002-tcp_scal_eval_fl_1_ping_cdf.png, 2017/08/batch-2017-11-05t121002-tcp_scal_eval_fl_1_totals.png, 2017/08/batch-2017-11-05t134127-tcp_scal_eval_fl_1_non_cong_tcp_cwnd1.png, 2017/08/pin20png.png, 2017/08/batch-2017-11-05t143144-tcp_scal_eval_fl_8_non_cong_ping_cdf.png, 2017/08/batch-2017-11-05t125407-tcp_scal_eval_fl_20_ping_cdf.png, 2017/08/batch-2017-11-05t134127-tcp_scal_eval_fl_1_non_cong_box_totals.png, 2017/08/batch-2017-11-05t150055-tcp_scal_eval_fl2_non_cong_totals.png, 2017/08/batch-2017-11-05t125407-tcp_scal_eval_fl_20_box_totals.png, 2017/08/box4.png, 2017/08/batch-2017-11-05t134127-tcp_scal_eval_fl_1_non_cong_ping_cdf.png, 2017/08/tcp_cwnd1.png, 2017/08/batch-2017-11-05t150055-tcp_scal_eval_fl2_non_cong_box_totals.png, 2017/08/batch-2017-11-05t150055-tcp_scal_eval_fl2_non_cong_ping_cdf.png, 2017/08/batch-2017-11-05t134127-tcp_scal_eval_fl_1_non_cong_totals.png

 

Drive behind introspection
==========================

First, a researcher's curiosity what is the actual plasticity of this setting and further the urge for complementing rather incomplete, technical statements made around this topic findable everywhere.

Testbed outline
===============

All virtual, KVM or LXC based,  with a  most recent fedora26 (**kernel 4.11**) as VMs that are acting as the **sender** and **sink** for the runs. Apart from the window scaling, the network stack remained default configured as coming out of the box.

**Sender** and **Sink** were communicating via a **CORE Emulator **spanned L2 network, which seriously made handling the (**non**.)**bottle-neck-link (1 Gbps, 2ms latency)** setup a breeze for the run operator.

Very basic, though, all what is needed to demonstrate the nominal aspect of the objectives. Certainly, exercising stronger infrastructure (e.g. plain HW) or further tunings (see refs.) will alleviate/taint the picture in specifc directions, though, the principle of the observations will stay the same - which is key.

\[caption id="attachment\_2511" align="alignnone" width="882"\]![Screenshot from 2017-08-23 18-12-35]({static}2017/08/screenshot-from-2017-08-23-18-12-35.png){.alignnone .size-full .wp-image-2511 width="882" height="569"} Core EMULATOR based L2 test connection with artifcial **bottle-neck-link** in **blue**\[/caption\]

Run
===

Settings space
--------------

> **FED26 defaults**
>
> net.ipv4.tcp\_rmem = 4096 87380 **6291456**  
> net.ipv4.tcp\_wmem = 4096 16384 **4194304**

The overall quantification measurements were done for window max sizes of (stepwidth of 20 % of predecessor in either direction from default)

> 2516582 5033164 **6291456 (default)** 7549747 15099494 30198988 60397976

and settings were always exercised in sync for **tcp\_rmem,tcp\_wmem.** That was done for convenience purposes for the operator mostly, technically, it makes sense to let **wmem** drag a little behind **rmem.** See reference for details upon the latter - while, studying closely the series graphs should also give the notion of the why.

Moreover, the autoscaling effects of **net.ipv4.tcp\_mem** were circumvented by setting those to the systems available max memory, in order to keep the sender sending merely based on what is advertised and not being clamped down by some kernel steered memory conservation approach on either side of the transmission.

**Instrumentarium**
-------------------

All actual measurement taking was done in an automated fashion with the help of [flent](https://flent.org/), currently THE open network performance analysis suite for the TCP/IP stack.

Outcome
-------

Further, the operator chose the number of **injectors (TCP sender processes)** as a further degree of freedom to influence the **traffic load** onto the **bottle-neck-link**.

Saturated Bottleneck
--------------------

** Specifics: 1 Gbps, 2ms latency**

### 20 injectors

### ![batch-2017-11-05T125407-tcp\_scal\_eval\_fl\_20\_totals]({static}2017/08/batch-2017-11-05t125407-tcp_scal_eval_fl_20_totals.png){.alignnone .size-full .wp-image-2732 width="1929" height="619"}![batch-2017-11-05T125407-tcp\_scal\_eval\_fl\_20\_ping\_cdf]({static}2017/08/batch-2017-11-05t125407-tcp_scal_eval_fl_20_ping_cdf.png){.alignnone .size-full .wp-image-2730 width="1700" height="600"}![batch-2017-11-05T125407-tcp\_scal\_eval\_fl\_20\_box\_totals]({static}2017/08/batch-2017-11-05t125407-tcp_scal_eval_fl_20_box_totals.png){.alignnone .size-full .wp-image-2729 width="1850" height="845"}![tcp\_cwnd]({static}2017/08/tcp_cwnd1.png){.alignnone .wp-image-2733 width="704" height="949"}

### 4 injectors![batch-2017-11-05T124309-tcp\_scal\_eval\_fl\_4\_totals]({static}2017/08/batch-2017-11-05t124309-tcp_scal_eval_fl_4_totals.png){.alignnone .size-full .wp-image-2728 width="1929" height="619"}

![batch-2017-11-05T124309-tcp\_scal\_eval\_fl\_4\_ping\_cdf]({static}2017/08/batch-2017-11-05t124309-tcp_scal_eval_fl_4_ping_cdf.png){.alignnone .wp-image-2726 width="754" height="266"}![batch-2017-11-05T124309-tcp\_scal\_eval\_fl\_4\_box\_totals]({static}2017/08/batch-2017-11-05t124309-tcp_scal_eval_fl_4_box_totals.png){.alignnone .size-full .wp-image-2725 width="1850" height="845"}![batch-2017-11-05T124309-tcp\_scal\_eval\_fl\_4\_tcp\_cwnd]({static}2017/08/batch-2017-11-05t124309-tcp_scal_eval_fl_4_tcp_cwnd.png){.alignnone .size-full .wp-image-2727 width="2212" height="632"}

 

### 

 

### 1 injector

 

![batch-2017-11-05T121002-tcp\_scal\_eval\_fl\_1\_totals]({static}2017/08/batch-2017-11-05t121002-tcp_scal_eval_fl_1_totals.png){.alignnone .size-full .wp-image-2724 width="1929" height="619"}![batch-2017-11-05T121002-tcp\_scal\_eval\_fl\_1\_ping\_cdf]({static}2017/08/batch-2017-11-05t121002-tcp_scal_eval_fl_1_ping_cdf.png){.alignnone .size-full .wp-image-2722 width="1700" height="600"}![batch-2017-11-05T121002-tcp\_scal\_eval\_fl\_1\_box\_totals]({static}2017/08/batch-2017-11-05t121002-tcp_scal_eval_fl_1_box_totals.png){.alignnone .size-full .wp-image-2721 width="1850" height="845"}![batch-2017-11-05T121002-tcp\_scal\_eval\_fl\_1\_tcp\_cwnd]({static}2017/08/batch-2017-11-05t121002-tcp_scal_eval_fl_1_tcp_cwnd.png){.alignnone .size-full .wp-image-2723 width="1700" height="600"}

Non-Saturated Bottleneck
------------------------

**Specifics: infinite bandwitdh, 2ms latency  
**

### 8 injectors![batch-2017-11-05T143144-tcp\_scal\_eval\_fl\_8\_non\_cong\_totals]({static}2017/08/batch-2017-11-05t143144-tcp_scal_eval_fl_8_non_cong_totals.png){.alignnone .size-full .wp-image-2738 width="1929" height="619"}

![batch-2017-11-05T143144-tcp\_scal\_eval\_fl\_8\_non\_cong\_ping\_cdf]({static}2017/08/batch-2017-11-05t143144-tcp_scal_eval_fl_8_non_cong_ping_cdf.png){.alignnone .size-full .wp-image-2736 width="1700" height="600"}![batch-2017-11-05T143144-tcp\_scal\_eval\_fl\_8\_non\_cong\_box\_totals]({static}2017/08/batch-2017-11-05t143144-tcp_scal_eval_fl_8_non_cong_box_totals.png){.alignnone .size-full .wp-image-2735 width="1850" height="845"}![batch-2017-11-05T143144-tcp\_scal\_eval\_fl\_8\_non\_cong\_tcp\_cwnd]({static}2017/08/batch-2017-11-05t143144-tcp_scal_eval_fl_8_non_cong_tcp_cwnd.png){.alignnone .size-full .wp-image-2737 width="2212" height="1222"}

### 2 injectors

![batch-2017-11-05T150055-tcp\_scal\_eval\_fl2\_non\_cong\_totals]({static}2017/08/batch-2017-11-05t150055-tcp_scal_eval_fl2_non_cong_totals.png){.alignnone .size-full .wp-image-2742 width="1929" height="619"}![batch-2017-11-05T150055-tcp\_scal\_eval\_fl2\_non\_cong\_ping\_cdf]({static}2017/08/batch-2017-11-05t150055-tcp_scal_eval_fl2_non_cong_ping_cdf.png){.alignnone .size-full .wp-image-2740 width="1700" height="600"}![batch-2017-11-05T150055-tcp\_scal\_eval\_fl2\_non\_cong\_box\_totals]({static}2017/08/batch-2017-11-05t150055-tcp_scal_eval_fl2_non_cong_box_totals.png){.alignnone .size-full .wp-image-2739 width="1850" height="845"}

![tcp\_cwnd]({static}2017/08/tcp_cwnd2.png){.alignnone .size-full .wp-image-2747 width="1500" height="800"}

### 1 injector

![batch-2017-11-05T134127-tcp\_scal\_eval\_fl\_1\_non\_cong\_totals]({static}2017/08/batch-2017-11-05t134127-tcp_scal_eval_fl_1_non_cong_totals.png){.alignnone .size-full .wp-image-2746 width="1929" height="619"}![batch-2017-11-05T134127-tcp\_scal\_eval\_fl\_1\_non\_cong\_ping\_cdf]({static}2017/08/batch-2017-11-05t134127-tcp_scal_eval_fl_1_non_cong_ping_cdf.png){.alignnone .size-full .wp-image-2744 width="1700" height="600"}![batch-2017-11-05T134127-tcp\_scal\_eval\_fl\_1\_non\_cong\_box\_totals]({static}2017/08/batch-2017-11-05t134127-tcp_scal_eval_fl_1_non_cong_box_totals.png){.alignnone .size-full .wp-image-2743 width="1850" height="845"}

![batch-2017-11-05T134127-tcp\_scal\_eval\_fl\_1\_non\_cong\_tcp\_cwnd]({static}2017/08/batch-2017-11-05t134127-tcp_scal_eval_fl_1_non_cong_tcp_cwnd1.png){.alignnone .size-full .wp-image-2749 width="1700" height="600"}

Interpretation
--------------

It mostly aligns with the expectations as of which I had:

-   Is the **bottle-neck** **NOT** saturated then the latency determining factor is the traffic handling fortitude offered by the actual producer(**sender**)/consumer(**receiver**) on respective ends - boiling down to what 'hardware' is in use.
-   Otherwise, in a **link saturation situation**, allowing the sender to progress sending by keeping the TCP sink advertising, can increase the perceived latency. Since then in addition to the  **bottle-neck** and therefore  what the **TCP congestion control** (**cubic in this case**) does and can deliver - as recognizable by the distinctive sawtooth pattern for the latency and TCP socket cwnd samples -, a potentially standing queue formed on either or sender and sink side on socket buffer layer in the stack does influence the overall performance.

References
==========

### TCP specifics for novices

-   Fall KR, Stevens WR. TCP/IP Illustrated. Addison-Wesley Professional; 2011., 9780321336316
-   Peter L Dordal. [*Introduction to Computer Networks*](http://intronetworks.cs.luc.edu/current/html/). Department of Computer Science: Loyola University Chicago;

 
