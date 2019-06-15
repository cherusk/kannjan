Title: Monitoring and Tuning the Linux Networking Stack: Egress (TX)
Date: 2016-12-25 19:59
Author: cherusk
Category: LNX Network Engineering Research
Tags: driver, driver queues, egress, ethtool, kernel, linux, Monitoring, msi, multi queueing, NAPI, network stack, networking, nic, performance, qdisc, queueing, queues, queuing discipline, sending, skb, softirq, stack traversal, tc, Traffic Control, transmission, transmit packet steering, transmitting, Tuning, TX, XPS
Slug: monitoring-and-tuning-the-linux-networking-stack-egress-tx
Status: published
Attachments: 2016/12/ns_tx_driv_qu_scale-svg.png

[Edit on Github](https://github.com/cherusk/kannjan/blob/master/linux_ns_egress)
================================================================================

-   [TL;DR](#TL;DR)
-   [Approach](#Approach)
-   [TX skb traversal starting](#traversal%20starting)
    -   [Higher Layer](#Higher%20Layer)
        -   [TCP egress skeleton](#TCP%20egress%20skeleton)
            -   [sending focal point: tcp\_sendmsg](#)
            -   [tcp\_write\_xmit and tcp\_transmit\_skb](#tcp_write_xmit%20and%20tcp_transmit_skb)
        -   [IP code paths](#IP%20code%20paths)
            -   [ip\_queue\_xmit](#ip_queue_xmit)
                -   coming data from TCP
                -   routing subsystem incurred costs
            -   [ip\_local\_out](#ip_local_out)
                -   [common tx sink for further protocols (like UDP)](#common%20tx%20sink%20for%20further%20protocols%20(like%20UDP))
                -   [\_\_ip\_local\_out](#__ip_local_out)
                -   first netfilter hurdle
            -   [ip\_output](#ip_output)
                -   dst\_output
                -   second netfilter hurdle
            -   [netfilter and iptables impact](#netfilter%20and%20iptables%20impact)
            -   [ip\_finish\_ouput](#ip_finish_ouput)
                -   [ip\_finish\_ouput2](#ip_finish_ouput2)
                -   [to qdisc - via neighboring modules](#to%20qdisc%20-%20via%20neighboring%20modules)
-   [Queuing Discipline (qdisc)](#qdisc)
    -   Higher Layer Interplay
        -   [\_\_dev\_queue\_xmit](#__dev_queue_xmit)
            -   Driver Interplay - queueful or queueless
        -   [\_\_dev\_xmit\_skb](#__dev_xmit_skb)
    -   [Core Mechanisms](#Core%20Mechanisms)
        -   [struct Qdisc](#struct%20Qdisc)
        -   [generic Traffic Control interface](#generic%20Traffic%20Control%20interface)
            -   [enqueue](#enqueue%20and%20dequeue)
            -   [dequeue](#enqueue%20and%20dequeue)
            -   [requeue and dev\_requeue\_skb](#requeue%20and%20dev_requeue_skb)
        -   [\_\_qdisc\_run](#__qdisc_run)
        -   [qdisc\_restart](#qdisc_restart)
            -   draining the qdisc
            -   dequeue\_skb
    -   [qdisc over multiple driver queues](#qdisc%20over%20multiple%20driver%20queues)
        -   [multiq](#multiq)
    -   [Monitoring](#Monitoring)
        -   [Using Linux Traffic Control (tc)](#Using%20Linux%20Traffic%20Control)
    -   Tuning
        -   [choosing proper qdisc](#choosing%20proper%20qdisc)
        -   [tweaking qdisc draining](#tweaking%20qdisc%20draining)
        -   [qdisc limit](#qdisc%20limit)
-   [Linux network device subsystem](#device%20subsystem)
    -   [NAPI / Device driver contract](#NAPI%20/%20Device%20driver%20contract)
        -   [device egress scheduling](#egress%20device%20scheduling)
            -   [\_\_netif\_schedule](#__netif_schedule)
            -   output\_queue device list
            -   [dev\_kfree\_skb\_irq](#dev_kfree_skb_irq)
                -   completion\_queue
        -   [TX softirq processing](#TX%20softirq%20processing)
            -   egress data processing loop
                -   net\_tx\_action
-   [Network Device Driver](http://Network%20Device%20Driver)
    -   [Upper Layer Interplay](#Upper%20Layer%20Interplay)
        -   [sch\_direct\_xmit](#sch_direct_xmit)
        -   [dev\_hard\_start\_xmit](#dev_hard_start_xmit)
        -   [dev\_reque\_skb](#dev_reque_skb)
        -   [processing feedback](#processing%20feedback)
    -   [actual driver handover](#actual%20driver%20handover)
        -   [dev\_queue\_xmit\_nit](#dev_queue_xmit_nit)
        -   [netdev\_start\_xmit](#netdev_start_xmit)
    -   [driver queues](#driver%20queues)
        -   [multiple egress queues](#multiple%20egress%20queues)
            -   [locking](#locking)
            -   cpu contention
        -   [Transmit Packet Steering - XPS](#xps)
        -   egress driver ring length
    -   Tuning
        -   [apply XPS](#apply%20XPS)
        -   [multi queuing](#Tune%20multi%20queuing)
            -   adjust queue count
        -   [adjust queue length](#adjust%20queue%20length)
    -   [CPU egress election](#election)
    -   [Hard-IRQs](#Hard-IRQs)
-   Conclusion
-   [Appendix](#Appendix)
    -   Illustrations
        -   [Driver Queue Based Scaling](#Driver%20Queue%20Based%20Scaling)

<!--more-->

TL;DR {#TL;DR}
=====

With this blog article I'm seeking to complement the [Linux RX Network Stack Monitoring and Tuning](https://blog.packagecloud.io/eng/2016/06/22/monitoring-tuning-linux-networking-stack-receiving-data/#hardware-accelerated-receive-flow-steering-arfs) with the TX concerns.

Approach {#Approach}
========

We'll traverse the Linux Network Stack Transmission from Top to Bottom from userland via high layer kernel concepts like sockets down to the Network Device itself. As the [article about the RX part of the stack](https://blog.packagecloud.io/eng/2016/06/22/monitoring-tuning-linux-networking-stack-receiving-data/#hardware-accelerated-receive-flow-steering-arfs) covered TX data structures and shared concepts between RX and TX mechanisms quite well, I'll try not to reiterate those here with every scrutiny as far as doable without losing comprehensibility. Base for work was kernel 4.9.

TX skb traversal starting {#traversal starting}
=========================

Higher Layer {#Higher Layer}
============

TCP egress skeleton {#TCP egress skeleton}
-------------------

### tcp\_sendmsg

Every userland sending system call you can think of like **sendto(), sendmsg(), send() or write()** eventually is getting handled by **tcp\_sendmsg**.

In code: [/net/ipv4/tcp.c](http://lxr.free-electrons.com/source/net/ipv4/tcp.c#L1097)

<div>

> ``` {style="color:#000000;background:#ffffff;"}
> int tcp_sendmsg(struct kiocb *iocb, struct sock *sk, struct msghdr *msg,
>                 size_t size)
> {
>         struct iovec *iov;
>         struct tcp_sock *tp = tcp_sk(sk);
> /*...*/
>                         
>             if (forced_push(tp)) {
>                                  tcp_mark_push(tp, skb);
>                                  __tcp_push_pending_frames(sk, mss_now, TCP_NAGLE_PUSH);
>                          } else if (skb == tcp_send_head(sk))
>                                  tcp_push_one(sk, mss_now);continue;
> /*...*/
>                          if (copied)
>                                  tcp_push(sk, flags & ~MSG_MORE, mss_now, TCP_NAGLE_PUSH);if ((err = sk_stream_wait_memory(sk, &timeo)) != 0)
>                                  goto do_error;
> /*...*/
>  
>  out:
>          if (copied)
>                  tcp_push(sk, flags, mss_now, tp->nonagle);
>          TCP_CHECK_TIMER(sk);
>          release_sock(sk);
> /*...*/
> }
> EXPORT_SYMBOL(tcp_sendmsg);
> ```

It's intended to spare you from the pkt assembling and error handling code parts. Important are the channels that lead further down. These are the highlighted **tcp\_push** wrappers, which are end up calling **tcp\_write\_xmit.**

</div>

### tcp\_write\_xmit and tcp\_transmit\_skb {#tcp_write_xmit and tcp_transmit_skb}

First in **tcp\_write\_xmit -** also even throughput and latency relevant - checks and adaptions for the **general** **pkt processing** further down in the stack are being made. **  
**

In code: [/net/ipv4/tcp\_output.c](http://lxr.free-electrons.com/source/net/ipv4/tcp_output.c#L2098)

> ``` {style="color:#000000;background:#ffffff;"}
> static int tcp_write_xmit(struct sock *sk, unsigned int mss_now, int nonagle,
>                           int push_one, gfp_t gfp)
> {
>         struct tcp_sock *tp = tcp_sk(sk);
>         struct sk_buff *skb;
>         unsigned int tso_segs, sent_pkts;
>         int cwnd_quota;
> /*...*/
>         while ((skb = tcp_send_head(sk))) {
>                 unsigned int limit;
>
>                 tso_segs = tcp_init_tso_segs(sk, skb, mss_now);
>                 BUG_ON(!tso_segs);
>
>                 cwnd_quota = tcp_cwnd_test(tp, skb);
>                 if (!cwnd_quota)
>                         break;
> /*...*/
>
>                 if (unlikely(tcp_transmit_skb(sk, skb, 1, gfp)))
>                         break;
> /*...*/
> }
> ```

From tcp\_transmit\_skb we're lead into network layer processing via the callback **icsk-&gt;icsk\_af\_ops-&gt;queue\_xmit** which is set to the IPv4 specific **ip\_queue\_xmit()** function during the IPv4 module initialization.

In code: [/net/ipv4/tcp\_output.c](http://lxr.free-electrons.com/source/net/ipv4/tcp_output.c#L908)

> ``` {style="color:#000000;background:#ffffff;"}
> static int tcp_transmit_skb(struct sock *sk, struct sk_buff *skb, int clone_it,
>                             gfp_t gfp_mask)
> {
>         const struct inet_connection_sock *icsk = inet_csk(sk);
>         struct inet_sock *inet;
>         struct tcp_sock *tp;
>
> /*...MY COMMENT: tcp specific skb chekcing and forming steps */
>
>         icsk->icsk_af_ops->queue_xmit(skb, &inet->cork.fl);
>
> /*...*/
>
>         return net_xmit_eval(err);
> }
>
> ```

Though, I don't want to go into tcp tuning knobs in detail since TCP is a highly complex tuning realm for itself. I might cover it in future updates. Excellent literature is around to give you insights if needed in ad hoc fashion.

Network Layer: IP code paths {#IP code paths}
----------------------------

### ip\_queue\_xmit

In this function on the way down, the routing table is consulted.

In code: [/net/ipv4/ip\_output.c](http://lxr.free-electrons.com/source/net/ipv4/ip_output.c#L400)

> ``` {style="color:#000000;background:#ffffff;"}
> int ip_queue_xmit(struct sock *sk, struct sk_buff *skb, struct flowi *fl)
> {
>         struct inet_sock *inet = inet_sk(sk);
>         struct net *net = sock_net(sk);
>         struct ip_options_rcu *inet_opt;
>         struct flowi4 *fl4;
>         struct rtable *rt;
>         struct iphdr *iph;
>         int res;
>
>         /* Skip all of this if the packet is already routed,
>          * f.e. by something like SCTP.
>          */
>         rcu_read_lock();
>         inet_opt = rcu_dereference(inet->inet_opt);
>         fl4 = &fl->u.ip4;
>         rt = skb_rtable(skb);
>         if (rt)
>                 goto packet_routed;
>
>         /* Make sure we can route this packet. */
>         rt = (struct rtable *)__sk_dst_check(sk, 0);
>         if (!rt) {
>
> /*...*/
>
>                  /* If this fails, retransmit mechanism of transport layer will
>                  * keep trying until route appears or the connection times
>                  * itself out.
>                  */
>                 rt = ip_route_output_ports(net, fl4, sk,
>                                            daddr, inet->inet_saddr,
>                                            inet->inet_dport,
>                                            inet->inet_sport,
>                                            sk->sk_protocol,
>                                            RT_CONN_FLAGS(sk),
>                                            sk->sk_bound_dev_if);
>                 if (IS_ERR(rt))
>                         goto no_route;
>                 sk_setup_caps(sk, &rt->dst);
>         }
>         skb_dst_set_noref(skb, &rt->dst);
>
> packet_routed:
>
> /*...*/
>         res = ip_local_out(net, sk, skb);
>         rcu_read_unlock();
>         return res;
>
> no_route:
> /*...*/
> }
> EXPORT_SYMBOL(ip_queue_xmit);
> ```

In the successful case, a route is available for the destination of the buffer, processing continues with **ip\_local\_out.**

### ip\_local\_out

#### common tx sink for further protocols (like UDP) {#common tx sink for further protocols (like UDP)}

**ip\_local\_out** is the shared knot in the paths down the stack for several transport protocols like **ip\_send\_skb**. But for understanding the egress path, covering one transport protocol is quite enough.

#### \_\_ip\_local\_out {#__ip_local_out}

With **ip\_local\_out** we've a wrapper around **\_\_ip\_local\_out** that mainly awaits the outcome of the netfilter interaction of **\_\_ip\_local\_out**.

In code: [/net/ipv4/ip\_output.c](http://lxr.free-electrons.com/source/net/ipv4/ip_output.c#L400)

> ``` {style="color:#000000;background:#ffffff;"}
> int ip_local_out(struct net *net, struct sock *sk, struct sk_buff *skb)
> {
>         int err;
>
>         err = __ip_local_out(net, sk, skb);
>         if (likely(err == 1))
>                 err = dst_output(net, sk, skb);
>
>         return err;
> }
> EXPORT_SYMBOL_GPL(ip_local_out);
> ```

If err is returned as 1, netfilter allowed the pkt to pass and the traversal continues with **dst\_output** further down. Otherwise, netfilter has consumed the pkt.

#### first netfilter hurdle {#first netfilter hurdle}

Here the netfilter hook call at the end of **\_\_ip\_local\_out**

> ``` {style="color:#000000;background:#ffffff;"}
> return nf_hook(NFPROTO_IPV4, NF_INET_LOCAL_OUT,
>                net, sk, skb, NULL, skb_dst(skb)->dev,
>                dst_output);
> ```

### ip\_output

The aforementioned **dst\_output** function unfolds the buffer related **output** handler which is in case of TCP over IPv4 initialized to **ip\_output**.

#### second netfilter hurdle {#second netfilter hurdle}

Here you see **ip\_output** condensed to its **essential** **content:** The second entry point to the netfilter along the egress path. If the buffer is allowed to pass according the rules, **ip\_finish\_output** is invoked as a callback on.

In code: [/net/ipv4/ip\_output.c](http://lxr.free-electrons.com/source/net/ipv4/ip_output.c#L370)

> ``` {style="color:#000000;background:#ffffff;"}
> return NF_HOOK_COND(NFPROTO_IPV4, NF_INET_POST_ROUTING,
>                     net, sk, skb, NULL, dev,
>                     ip_finish_output,
>                     !(IPCB(skb)->flags & IPSKB_REROUTED));
> ```

### netfilter and iptables impact {#netfilter and iptables impact}

As the authors in the [RX depiction](https://blog.packagecloud.io/eng/2016/06/22/monitoring-tuning-linux-networking-stack-receiving-data/#netfilter-and-iptables) did, I am not diving further into the intrinsics of netfiler and iptables mechanism at this stage.

***Important is though*:** the same statements hold valid for the mechanics of the egress path. The more complex and numerous your filtering rules are made up, the more performance penalties are incurred upon the egress pkt processing. Nevertheless, if the rules are needed, you may cannot circumvent those costs.

### ip\_finish\_ouput

I'll put GSO and fragmentation handling aside at first, and concentrate on the traversal further down via **ip\_finish\_ouput2.**

In code:[/net/ipv4/ip\_output.c](http://lxr.free-electrons.com/source/net/ipv4/ip_output.c#L287)

> ``` {style="color:#000000;background:#ffffff;"}
> static int ip_finish_output(struct net *net, struct sock *sk, struct sk_buff *skb)
> {
>         unsigned int mtu;
>
> /*...*/
>         if (skb_is_gso(skb))
>                 return ip_finish_output_gso(net, sk, skb, mtu);
>
>         if (skb->len > mtu || (IPCB(skb)->flags & IPSKB_FRAG_PMTU))
>                 return ip_fragment(net, sk, skb, mtu, ip_finish_output2);
>
>         return ip_finish_output2(net, sk, skb);
> }
> ```

#### ip\_finish\_ouput2

Within here we're at the rim between neighboring and queueing discipline. **dst\_neigh\_output** is the positive case, when the neighboring cache is already filled with the next hop of our buffer.

In code:[/net/ipv4/ip\_output.c](http://lxr.free-electrons.com/source/net/ipv4/ip_output.c#L182)

> ``` {style="color:#000000;background:#ffffff;"}
> static int ip_finish_output2(struct net *net, struct sock *sk, struct sk_buff *skb)
> {
> /*...*/
>         if (unlikely(!neigh))
>                 neigh = __neigh_create(&arp_tbl, &nexthop, dev, false);
>         if (!IS_ERR(neigh)) {
>                 int res = dst_neigh_output(dst, neigh, skb);
>
>                 rcu_read_unlock_bh();
>                 return res;
>         }
> /*...*/
>         return -EINVAL;
> }
> ```

#### to qdisc - via neighboring modules {#to qdisc - via neighboring modules}

The generic interface to neighboring **(ND or ARP)** exposes **dst\_neigh\_output.** Following it's core lines of code:**  
**

> ``` {style="color:#000000;background:#ffffff;"}
> hh = &n->hh;
> if ((n->nud_state & NUD_CONNECTED) && hh->hh_len)
>         return neigh_hh_output(hh, skb);
> else
>         return n->output(n, skb);
> ```

Here you see, if the neighboring node is in connected state, the layer 2 destination header sections are fetched from a header cache. Else, depending on the neighboring protocol used and the state of the neighboring entry (**NUD - neighbor unreachability detection**) specific actions behind the generic handler **n-&gt;output** are carried out (e.g. neighbor node probing or resolution).

Neighboring itself can be a difficile topic and is put out of scope of this post. Further, in high bandwidth network environment the tuning of neighboring is of marginal importance, because it's mostly constant O(1) cache filling cost is mainly paid only once when traffic is setting out and not incurred anymore later when the traffic is kept busy to the and from the node - the neighboring cache stays hot then.

When you can afford to phase in neighboring based proxying in your environment, then the neighboring modules do pose a tuning knob for you, since the **cost of routing** would be alleviated by the need of only a minimalistic, rather symbolic routing table. But for most enterprise environments, that's not viable on a larger scale.

Moreover, to pass packets further down, the neighboring module - in what state the entry may ever is - will eventually invoke **dev\_queue\_xmit**, which leads us to the queuing discipline network stack interface.

Queuing Discipline (qdisc) {#qdisc}
--------------------------

qdisc is the linux kernel network packet scheduling layer for Traffic Control purposes in between the NIC driver and the IP-Stack. It's composed of packet **scheduling algorithms** and its **own queues** apart from the driver ring buffers, but which are fed by the qdisc queues. The scheduling algorithms enqueue packets from other layers according their intention and thereby influence the transmission performance significantly.

We can find qdisc on RX paths as well for policing purposes, but as this post focuses on the egress path, I won't shed light onto the RX mechanisms here.

### Higher Layer Interplay {#Higher Layer Interplay}

#### \_\_dev\_queue\_xmit {#__dev_queue_xmit}

There's not much to say about **dev\_queue\_xmit** itself, it's simply wrapping **\_\_dev\_queue\_xmit** for the sake of one acceleration context parameter.

Approaching **\_\_dev\_queue\_xmit** on the other hand, discerns if it's about to transmit over a **queueless** or **queueful** device. Most HW based NICs work based on queues. For specific sorts of devices, like tunnelling or virtual ones (good examples would be the loopback) a queue is technically superfluous since either simply not needed (e.g. for the loopback) or its pkt buffers are being taken care of by a queue of a queueful device somewhere else in the stack.

In code: [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#L3316)

> ``` {#struct Qdisc style="color:#000000;background:#ffffff;"}
> static int __dev_queue_xmit(struct sk_buff *skb, void *accel_priv)
> {
>         struct net_device *dev = skb->dev;
>         struct netdev_queue *txq;
>         struct Qdisc *q;
>         int rc = -ENOMEM;
> /*...*/
>
>         txq = netdev_pick_tx(dev, skb, accel_priv);
>         q = rcu_dereference_bh(txq->qdisc);
>
>         trace_net_dev_queue(skb);
>         if (q->enqueue) {
>                 rc = __dev_xmit_skb(skb, q, dev, txq);
>                 goto out;
>         }
>
>         /* The device has no queue. Common case for software devices:
>            loopback, all the sorts of tunnels...
> ...*/
>         if (dev->flags & IFF_UP) {
>                 int cpu = smp_processor_id(); /* ok because BHs are off */
>
>                 if (txq->xmit_lock_owner != cpu) {
> /*...*/
>                         skb = validate_xmit_skb(skb, dev);
>                         if (!skb)
>                                 goto out;
>
>                         HARD_TX_LOCK(dev, txq, cpu);
>
>                         if (!netif_xmit_stopped(txq)) {
>                                 __this_cpu_inc(xmit_recursion);
>                                 skb = dev_hard_start_xmit(skb, dev, txq, &rc);
>                                 __this_cpu_dec(xmit_recursion);
>                                 if (dev_xmit_complete(rc)) {
>                                         HARD_TX_UNLOCK(dev, txq);
>                                         goto out;
>                                 }
>                         }
>                         HARD_TX_UNLOCK(dev, txq);
> /*...*/
>         return rc;
> }
> ```

Then, it either forks into**\_\_dev\_xmit\_skb,** when it's detecting a queueful device to transmit over - doing by checking if the qdisc enqueue callback does exist. Otherwise, it's phasing in a quasi direct transmit over a queueless device by **dev\_hard\_start\_xmit** with first grabbing the lock on the outgoing queue for the driving CPU and clearing it after the transmission attempts. More on [**dev\_hard\_start\_xmit**](#dev_hard_start_xmit) in the driver section.

#### **\_\_dev\_xmit\_skb** {#__dev_xmit_skb}

The main code paths there are framed by queue contention optimizations. More on queue contention in the driver section. Drilling it down, there are three important cases.

In Code: [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#L3086)

-   In case the qdisc has been deactived on purpose, drop the packets.

> ``` {style="color:#000000;background:#ffffff;"}
> if (unlikely(test_bit(__QDISC_STATE_DEACTIVATED, &q->state))) {
>         __qdisc_drop(skb, &to_free);
>         rc = NET_XMIT_DROP;
> }
> ```

-   For certain qdisc, when no previous data has been queued in, we can do a direct transmission attempt without queuing it first in the qdisc.

> ``` {style="color:#000000;background:#ffffff;"}
> else if ((q->flags & TCQ_F_CAN_BYPASS) && !qdisc_qlen(q) &&
>            qdisc_run_begin(q)) {
>         /*
>          * This is a work-conserving queue; there are no old skbs
>          * waiting to be sent out; and the qdisc is not running -
>          * xmit the skb directly.
>          */
>
>         qdisc_bstats_update(q, skb);
>
>         if (sch_direct_xmit(skb, q, dev, txq, root_lock, true)) {
>                 if (unlikely(contended)) {
>                         spin_unlock(&q->busylock);
>                         contended = false;
>                 }
>                 __qdisc_run(q);
>         } else
>                 qdisc_run_end(q);
>
>         rc = NET_XMIT_SUCCESS;
> }
> ```

-   This is the "regular case", as it were. The packets are first handed over to the queuing discipline and therefore put under its discretion of scheduling and queuing the data. The actual transmission is driven by the TX softirq context at the next opportunity, initiated by **\_\_qdisc\_run**. For details about the **\_\_qdisc\_run** read on in this section.

> ``` {style="color:#000000;background:#ffffff;"}
> else {
>         rc = q->enqueue(skb, q, &to_free) & NET_XMIT_MASK;
>         if (qdisc_run_begin(q)) {
>                 if (unlikely(contended)) {
>                         spin_unlock(&q->busylock);
>                         contended = false;
>                 }
>                 __qdisc_run(q);
>         }
> }
> ```

### **Core Mechanisms** {#Core}

Qdisc instances can be formed into sophisticated interrelations, mostly hierarchies, to implement complex Traffic Control needs. Here, I want to concentrate on the essentials of qdisc entities to unterstand it's workings for tuning needs.

#### generic Traffic Control interface {#generic Traffic Control interface}

#### enqueue and dequeue {#enqueue and dequeue}

You can see here the most important part of the Qdisc interface by which every qdisc implementation offers its specific scheduling logic: **enqueue** and **dequeue**.

In Code: [/include/net/sch\_generic.h](http://lxr.free-electrons.com/source/include/net/sch_generic.h#L47)

> ``` {style="color:#000000;background:#ffffff;"}
> struct Qdisc {
>         int                     (*enqueue)(struct sk_buff *skb, struct Qdisc *dev);
>         struct sk_buff *        (*dequeue)(struct Qdisc *dev);
> /*...*/
>         struct Qdisc_ops        *ops;
> /*...*/
>         struct Qdisc            *__parent;
>         struct netdev_queue     *dev_queue;
> /*...*/
> }
> ```

Either for putting skbs under its control or draining piled up skbs from previous TX runs from there. **Every Qdisc** instance is **associated** with a **net\_device** by its **queue**, as you can see. The \***\_\_parent** pointer gives evidence for the high nestability of Qdiscs. Internally, for realizing its logic, Qdisc might hold several virtual callback hubs with help of **<span style="color:#7f0055;">struct</span> Qdisc\_ops \*ops.**

#### requeue and dev\_requeue\_skb {#requeue and dev_requeue_skb}

**Requeuing** has been optimized by taking skb out of qdisc only if really transmittable. In case the transmission attempt fails, the queue length is reincremented and the net\_device is rescheduled for a further TX run on this CPU.

In Code: [/net/sched/sch\_generic.c](http://lxr.free-electrons.com/source/net/sched/sch_generic.c#L48)

> ``` {style="color:#000000;background:#ffffff;"}
> static inline int dev_requeue_skb(struct sk_buff *skb, struct Qdisc *q)
>  {
>          q->gso_skb = skb;
>          q->qstats.requeues++;
>          qdisc_qstats_backlog_inc(q, skb);
>          q->q.qlen++;    /* it's still part of the queue */
>          __netif_schedule(q);
>  
>          return 0;
>  }
> ```

In former kernel versions Qdisc instances used to have a **requeue** callback in their virtual interfaces.

#### \_\_qdisc\_run {#__qdisc_run}

When a device has been scheduled in for a transmission going over it, **\_\_qdisc\_run is** run in the **TX NAPI code paths** to dequeue the next skb meant for being transmited. At looking closer, we see **qdisc\_restart** is actually doing the grunt work. More to **disc\_restart** in the following section.

That's the code of [\_\_qdisc\_run](http://lxr.free-electrons.com/source/net/sched/sch_generic.c#L248):

> ``` {style="color:#000000;background:#ffffff;"}
> int quota = weight_p;
> int packets;
>
> while (qdisc_restart(q, &packets)) {
>         /*
>         * Ordered by possible occurrence: Postpone processing if
>         * 1. we've exceeded packet quota
>         * 2. another process needs the CPU;
>         */
>         quota -= packets;
>         if (quota <= 0 || need_resched()) {
>                 __netif_schedule(q);
>                 break;
>         }
> }
>
> qdisc_run_end(q);
> ```

You may remember the [**budget** tuning on **RX** side](https://blog.packagecloud.io/eng/2016/06/22/monitoring-tuning-linux-networking-stack-receiving-data/#adjusting-the-netrxaction-budget) for the **net\_rx\_action** run by the RX NAPI loop for the RX softIRQ processing. The same setting is taking effect in a similar manner on the TX side as the packet **quota**. One can easily confirm that by following the **weight\_p** global sysctl configuration variable to where it is exposed to the userland via the [**procFS** interface for the networking core](http://lxr.free-electrons.com/source/net/core/sysctl_net_core.c#L270):

> ``` {#dev_weight style="color:#000000;background:#ffffff none repeat scroll 0 0;"}
> {
>         .procname       = "dev_weight",
>         .data           = &weight_p,
>         .maxlen         = sizeof(int),
>         .mode           = 0644,
>         .proc_handler   = proc_dointvec
> },
> ```

Therefore, it has absolutely the same value and it's the upper limit of queued packets one instance of a TX softIRQ loop can deal with transmitting out until it releases the device and it's queue and does reschedule the device further transmissions if needed. We are coming to that when a reschedule is deemed necessary int the subsection covering **\_\_netif\_schedule** itself.

#### qdisc\_restart

In [/net/sched/sch\_generic.c](http://lxr.free-electrons.com/source/net/sched/sch_generic.c#L228):

> ``` {style="color:#000000;background:#ffffff;"}
> struct netdev_queue *txq;
> struct net_device *dev;
> spinlock_t *root_lock;
> struct sk_buff *skb;
> bool validate;
>
> /* Dequeue packet */
> skb = dequeue_skb(q, &validate, packets);
> if (unlikely(!skb))
>         return 0;
> ```

First, previously queued socket buffers (packets) are fetched from the qdisc. I'm not accidentally using the plural here, **dequeue\_skb** really can return a **list of packets**, depending on the behaviour of the current qdisc.

> ``` {style="color:#000000;background:#ffffff;"}
> root_lock = qdisc_lock(q);
> dev = qdisc_dev(q);
> txq = skb_get_tx_queue(dev, skb);
>
> return sch_direct_xmit(skb, q, dev, txq, root_lock, validate);
> ```

Then the device and its queue that are attached to the qdisc are determined. After that, **qdisc\_restart** is phasing in a transmission attempt via the TX device and its queue.

This is essentially how the queueing discipline is filled up and drained as transmission are ongoing via it. You also have a good idea now, where the qdisc and its mechanisms are located in the Linux TX network processing.

#### qdisc over multiple driver queues {#qdisc over multiple driver queues}

As already stated, it's not purpose of this blog post to fully unveil the intrinsics of the exhaustive choice of qdiscs.

Nevertheless, for high bandwidth egress the concept of multi queueing on driver and qdisc levels is essential. Justification enough to dive shallowly into **multiq**, the basic and from the netstack as a default overlay qdisc allocated mechanism, when multi qeueing on driver level is supported.

For more complex multi queueing traffic control tasks, e.g. for flow steering to certain TX queues, take a look at **mqprio**.

#### multiq

The init code is trivial and as expected so I'll spare it: Key is, that multiq initializes a **pfifo** for every TX queue if there has not been a qdisc allocated to it yet. The per TX queue held qdisc buffers is adoptable in case of pure fifo. Consult [LARTC](http://tldp.org/HOWTO/Adv-Routing-HOWTO/lartc.qdisc.html) for details and the full varieties of choice.

[Enqueuing](http://lxr.free-electrons.com/source/net/sched/sch_multiq.c#L67) works as with the targeted queue were a single queue with the multiq initiating the traffic control classification if present and further on framing the enqueuing into the sub queueing discipline with embedding it incontrol logic. Important: it does thereby **not deteriorate XPS** going abouts. Consult the **XPS** section of this post for more details.

> ``` {style="color:#000000;background:#ffffff;"}
>         qdisc = multiq_classify(skb, sch, &ret);
> /*...*/
>         ret = qdisc_enqueue(skb, qdisc, to_free);
>         if (ret == NET_XMIT_SUCCESS) {
>                 sch->q.qlen++;
>                 return NET_XMIT_SUCCESS;
>         }
>         if (net_xmit_drop_count(ret))
>                 qdisc_qstats_drop(sch);
>         return ret;
> ```

[Dequeuing](http://lxr.free-electrons.com/source/net/sched/sch_multiq.c#L95) does what stated in the [man page](https://linux.die.net/man/8/tc). *It will cycle though the bands and verify that the hardware queue associated with the band is not stopped prior to dequeuing a packet. It's meant to alleviate head of line blocking.  
*

> ``` {style="color:#000000;background:#ffffff;"}
> struct multiq_sched_data *q = qdisc_priv(sch);
> struct Qdisc *qdisc;
> struct sk_buff *skb;
> int band;
>
> for (band = 0; band < q->bands; band++) {
>         /* cycle through bands to ensure fairness */
>         q->curband++;
>         if (q->curband >= q->bands)
>                 q->curband = 0;
>
>         /* Check that target subqueue is available before
>          * pulling an skb to avoid head-of-line blocking.
>          */
>         if (!netif_xmit_stopped(
>             netdev_get_tx_queue(qdisc_dev(sch), q->curband))) {
>                 qdisc = q->queues[q->curband];
>                 skb = qdisc->dequeue(qdisc);
>                 if (skb) {
>                         qdisc_bstats_update(sch, skb);
>                         sch->q.qlen--;
>                         return skb;
>                 }
>         }
> }
> return NULL;
> ```

Whereby a **band** is a one of the multiple TX queues and its associated qdisc.

### Monitoring {#Monitoring}

#### Using Linux Traffic Control {#Using Linux Traffic Control}

For interacting with the Qeueing Discipline and its Traffic Control mechanisms from userland, there is a tool called **tc (man 8 tc)**.

> **linux:\~\$** tc -s -d qdisc show dev enp2s0  
> **qdisc** **pfifo\_fast** 0: root refcnt 2 bands 3 priomap 1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1  
> Sent 52084489 bytes 434946 pkt (**dropped** 0, **overlimits** 0 **requeues** 27)  
> **backlog** 0b 0p **requeues** 27**  
> **

Explanation of relevant fields:

-   **qdisc** **pfifo\_fast**: the current queueing discipline for the queried device. **pfifo\_fast** as default for single queued devices.
-   **dropped:** dropped buffers by qdisc because of algorithm decided to or the qdisc queue length has been exceeded
-   **overlimits:** depends on capabilities of qdisc: if it is doing traffic shaping, then the number of the current send limit having been reached by upper layers
-   **requeues:** supposed to be transmissions being reenqueued since of driver reporting it cannot transmit or take more TX for time being
-   **backlog:** bytes | buffers currently enqueued in qdisc**  
   **

Consult [LARTC](http://tldp.org/HOWTO/Adv-Routing-HOWTO/lartc.qdisc.html) for details of further output.

### Tuning {#Tuning}

#### choosing proper qdisc {#choosing proper qdisc}

I cannot and won't cover every aspect of qdisc algorithms and which one to choose when, because that's highly environment and purpose or traffic outline dependent. A good start is the [LARTC](http://tldp.org/HOWTO/Adv-Routing-HOWTO/lartc.qdisc.html) docs. Further, there has been done some brilliantly tangible research ([The Good, the Bad and the WiFi: Modern AQMs in a residential setting](http://www.sciencedirect.com/science/article/pii/S1389128615002479)) into certain aspects of qdiscs related to [buffer bloat](https://www.bufferbloat.net/projects/) and thereby induced latency quite recently. Although, these comparisons were focused on residential devices mainly, it should provide you with some additional pointers as to what qdisc to go for first when looking for prime performance.

Example for replacing for an iface the default qdisc **pfifo\_fast** with a **fq\_codel**:

>     # tc qdisc replace dev <your_dev> root fq_codel

For exchanging the leaf qdiscs of a multi queueing qdisc you can first adopt the default qdisc set for your net stack by:

>     # sysctl -w net.core.default_qdisc=fq_codel

After resetting the root mq qdisc for your iface, the previously set default qdisc is in place for every leaf in the mq qdisc:

>     # tc qdisc replace dev <your_dev> root mq

You can simply verify by doing:

>     # tc -s qdisc show <your_dev>

#### tweaking qdisc draining {#tweaking qdisc draining}

When you see numerous dropping and a high backlog, that might be an indicator that your TX stack paths may profit from a higher draining flux.

-   **cpu proportion spent on TX processing  
   **

<!-- -->

-   this sysctl paramater was already made acquaintend for [RX paths](https://blog.packagecloud.io/eng/2016/06/22/monitoring-tuning-linux-networking-stack-receiving-data/#tuning-adjust-the-napi-weight-of-the-backlog-poll-loop)
-   it has the same value as there when set for [TX paths NAPI](#dev_weight) (quota) processing
    -   NB: raising it has **side effects** for RX path NAPI processing and vice versa

Adjusting the value:

>     # sysctl -w net.core.dev_weight=900

-   **XPS**
    -   in SMP processor based systems with drivers supporting multi queuing, it can increase the outflux from qdisc by alleviating **CPU contention** for the **TX queues** and driver rings and further the need for qdisc reenqueuings as a symptom of high contention. Additionally, it increases the skb **cache locality** and therefore the **cache hit ratio** for network processing of the transmitting CPUs. More in the [driver section](#xps).

#### qdisc limit {#qdisc limit}

If it's setable and improving things is qdisc dependend. Further, what is the cause for a high backlog or dropping might be more importantly to fix than the length of the qdisc. Additionally, increasing the length may even deteriorate things by [spuring buffer bloat](https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/).

Though, in certain cases of high transmission rates, you might want your packets rather buffered than retransmitted by higher layers when high dropping is showing by querying your qdisc with tc.

Qdiscs have it set in different ways. For the default allocated qdisc **pfifo\_fast** with default length 1000 you have to do it with iproute2:

> \# ip link set enp2s0 txqueuelen 1200

Checking qdisc length:

> \$ ip l
>
> 1: enp2s0: &lt;BROADCAST,MULTICAST,UP,LOWER\_UP&gt; mtu 1500 qdisc **pfifo\_fast** state UP mode DEFAULT group default **qlen 1200**  
> link/ether fc:aa:14:1c:5d:ea brd ff:ff:ff:ff:ff:ff

Linux network device subsystem {#device subsystem}
==============================

After having learned where the queuing discipline is located and how it knobs together higher layers and the network device driver level, we'll peruse through the transmission model based on the NAPI - which you are already aware of from the RX guide.

NAPI / Device driver contract {#NAPI / Device driver contract}
-----------------------------

### egress device scheduling {#egress device scheduling}

#### \_\_netif\_schedule {#__netif_schedule}

When introducing the qdisc components of the kernel, we referenced **\_\_netif\_schedule** the first time. Its purpose is to register a net device seen eligible for being egress processed by a CPU.

Actually, **\_\_netif\_schedule** is only checking if the qdisc queue has already been scheduled, if not, **\_\_netif\_reschedule** kicks in: it does the actual NAPI egress registration.

Refer to: [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#L2254)

> ``` {style="color:#000000;background:#ffffff;"}
> struct softnet_data *sd;
> unsigned long flags;
>
> local_irq_save(flags);
> sd = &__get_cpu_var(softnet_data);
> q->next_sched = NULL;
> *sd->output_queue_tailp = q;
> sd->output_queue_tailp = &q->next_sched;
> raise_softirq_irqoff(NET_TX_SOFTIRQ);
> local_irq_restore(flags);
> ```

The steps it takes mainly are:

-   fetch the per CPU **softnet\_data** structure
-   links the **Qdisc \*q** into the per CPU **output\_queue** as part of **softnet\_data**
-   register a TX softirq loop run with **raise\_softirq\_irqoff** for the current CPU

Further, the **output\_queue** is consequently the queue of devices, that have something to transmit and have to be handled by the future hereby registered NAPI softirq loop runs.

#### \_\_dev\_kfree\_skb\_irq {#__dev_kfree_skb_irq}

You may have noticed that the driver mainly runs in interrupt context, and we it's commonplace know fact that code path in interrupt context have to be as quick as possible. As a consequence, the driver is not wasting time for releasing transmitted packets. The driver only links in skb ptr to a per CPU **completion\_queue**, that is part of the **softnet\_data** per CPU data structure.

In code [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#L2331):

> ``` {style="color:#000000;background:#ffffff none repeat scroll 0 0;"}
> void __dev_kfree_skb_irq(struct sk_buff *skb, enum skb_free_reason reason)
> {
> /*...*/
>
>         get_kfree_skb_cb(skb)->reason = reason;
>         local_irq_save(flags);
>         skb->next = __this_cpu_read(softnet_data.completion_queue);
>         __this_cpu_write(softnet_data.completion_queue, skb);
>         raise_softirq_irqoff(NET_TX_SOFTIRQ);
>         local_irq_restore(flags);
> }
> ```

Cleaning up is then done by the softirq processing loop in uncritical non-interrupt context. Notice, that its the same softirq loop to handle as for the egress transmission processing, namely **NET\_TX\_SOFTIRQ**. Details are given further down.**  
**

### TX softirq processing {#TX softirq processing}

Now we know enough for approaching the core of the TX softirq loop triggered by **NET\_TX\_SOFTIRQ.**

### egress data processing loop {#egress data processing loop}

The core handler for the egress processing is **net\_tx\_action**. It's covering two main cases.

Reference to code: [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#L3844)

-   cleaning up already transmitted skb instances
    -   here you can see the **completion\_queue** resurface again
    -   the rest is about freeing of skb held kernel memory

> ``` {style="color:#000000;background:#ffffff;"}
> struct softnet_data *sd = this_cpu_ptr(&softnet_data);
>
>         if (sd->completion_queue) {
>                 struct sk_buff *clist;
>
>                 local_irq_disable();
>                 clist = sd->completion_queue;
>                 sd->completion_queue = NULL;
>                 local_irq_enable();
>
>                 while (clist) {
>                         struct sk_buff *skb = clist;
>                         clist = clist->next;
>
>                         WARN_ON(atomic_read(&skb->users));
>                         if (likely(get_kfree_skb_cb(skb)->reason == SKB_REASON_CONSUMED))
>                                 trace_consume_skb(skb);
>                         else
>                                 trace_kfree_skb(skb, net_tx_action);
>
>                         if (skb->fclone != SKB_FCLONE_UNAVAILABLE)
>                                 __kfree_skb(skb);
>                         else
>                                 __kfree_skb_defer(skb);
>                 }
>
>                 __kfree_skb_flush();
>         }
> ```

-   transmitting packets by processing devices that have been registered for having something to transmit
    -   the previously **output\_queue** is consulted here to decide on what device to schedule in for processing next
    -   then the **qdisc\_run** ushers in packet transmission via the **qeueing discipline** interface

> ``` {style="color:#000000;background:#ffffff;"}
> if (sd->output_queue) {
>                 struct Qdisc *head;
>
>                 local_irq_disable();
>                 head = sd->output_queue;
>                 sd->output_queue = NULL;
>                 sd->output_queue_tailp = &sd->output_queue;
>                 local_irq_enable();
>
>                 while (head) {
>                         struct Qdisc *q = head;
>                         spinlock_t *root_lock;
>
>                         head = head->next_sched;
>
>                         root_lock = qdisc_lock(q);
>                         spin_lock(root_lock);
>                         /* We need to make sure head->next_sched is read
>                          * before clearing __QDISC_STATE_SCHED
>                          */
>                         smp_mb__before_atomic();
>                         clear_bit(__QDISC_STATE_SCHED, &q->state);
>                         qdisc_run(q);
>                         spin_unlock(root_lock);
>                 }
>         }
> ```

One may noticed, that the next net device for transmission is taken from the tail of the output\_queue, what may not always be the necessarly fairest approach among the devices.

Network Device Driver {#Network Device Driver}
=====================

Same here, I'm under the impression, that the essentials were well depicted at the RX guide when it comes to the Net Device Drivers, so I'll mainly focus on what is specific for the TX side of the stack in this area.

Upper Layer Interplay {#Upper Layer Interplay}
---------------------

### sch\_direct\_xmit

This function forms the driver feedback reaction framing around the transmission processing. It's transmitting several buffers and gives feedback of the device state after every transmit.

In Code: [/net/sched/sch\_generic.c](http://lxr.free-electrons.com/source/net/sched/sch_generic.c)

> ``` {style="color:#000000;background:#ffffff;"}
> /* And release qdisc */
> spin_unlock(root_lock);
>
> /*...*/
>
> if (likely(skb)) {
>         HARD_TX_LOCK(dev, txq, smp_processor_id());
>         if (!netif_xmit_frozen_or_stopped(txq))
>                 skb = dev_hard_start_xmit(skb, dev, txq, &ret);
>
>         HARD_TX_UNLOCK(dev, txq);
> } else {
>         spin_lock(root_lock);
>         return qdisc_qlen(q);
> }
> spin_lock(root_lock);
> ```

-   Requeuing has already been introdiced further up. Here, you its application. Every time the device reports, it cannot send anymore - may it be because its busy or for some other reason, then left overs are being requeued to the qdisc.

> ``` {style="color:#000000;background:#ffffff;"}
> if (dev_xmit_complete(ret)) {
>         /* Driver sent out skb successfully or skb was consumed */
>         ret = qdisc_qlen(q);
> } else {
>         /* Driver returned NETDEV_TX_BUSY - requeue skb */
>         if (unlikely(ret != NETDEV_TX_BUSY))
>                 net_warn_ratelimited("BUG %s code %d qlen %d\n",
>                                      dev->name, ret, q->q.qlen);
>
>         ret = dev_requeue_skb(skb, q);
> }
>
> if (ret && netif_xmit_frozen_or_stopped(txq))
>         ret = 0;
>
> return ret;
> ```

### dev\_hard\_start\_xmit

Here you can see the loop where single buffers are passed further to the hands of the driver via xmit\_one.

Code Reference: [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#L2920)

> ``` {style="color:#000000;background:#ffffff;"}
> struct sk_buff *skb = first;
>         int rc = NETDEV_TX_OK;
>
>         while (skb) {
>                 struct sk_buff *next = skb->next;
>
>                 skb->next = NULL;
>                 rc = xmit_one(skb, dev, txq, next != NULL);
>                 if (unlikely(!dev_xmit_complete(rc))) {
>                         skb->next = next;
>                         goto out;
>                 }
>
>                 skb = next;
>                 if (netif_xmit_stopped(txq) && skb) {
>                         rc = NETDEV_TX_BUSY;
>                         break;
>                 }
>         }
> ```

xmit\_one gives with **dev\_queue\_xmit\_nit** a copy of the skb to every tap registered in the path and then phases in the final hand over of the buffer to the driver egress mechanisms by invoking **netdev\_start\_xmit**.

In Code: [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#L2903)

> ``` {style="color:#000000;background:#ffffff;"}
> if (!list_empty(&ptype_all) || !list_empty(&dev->ptype_all))
>         dev_queue_xmit_nit(skb, dev);
>
> len = skb->len;
> trace_net_dev_start_xmit(skb, dev);
> rc = netdev_start_xmit(skb, dev, txq, more);
> trace_net_dev_xmit(skb, rc, dev, len);
> ```

### actual driver handover {#actual driver handover}

#### netdev\_start\_xmit

Egress processing is now culminating into driver realms.

Code ref: [/include/linux/netdevice.h](http://lxr.free-electrons.com/source/include/linux/netdevice.h#L4050)

1.  the virtual interface **dev-&gt;netdev\_ops** of the driver is fetched

> ``` {style="color:#000000;background:#ffffff;"}
> const struct net_device_ops *ops = dev->netdev_ops;
> int rc;
>
> rc = __netdev_start_xmit(ops, skb, dev, more);
> if (rc == NETDEV_TX_OK)
>         txq_trans_update(txq);
> ```

-   and used for the skb handover in **\_\_netdev\_start\_xmit  
   **to access the driver callback **ndo\_start\_xmit**

> ``` {style="color:#000000;background:#ffffff;"}
> skb->xmit_more = more ? 1 : 0;
> return ops->ndo_start_xmit(skb, dev);
> ```

From now on all processing is driver specific. The egress core from now on only has a reactive role to feedback given by drivers. How the tx-rings (driver queues) are maintained and handled is therefore driver specific code. The association between flow and driver tx-ring is drawn from the skb passed over. The skb keeps the ring index in its context.

#### **processing feedback**

The kernel is relying on feedback from the driver to react appropriately to its transmission attempts:

-   **NETDEV\_TX\_OK**: transmission was successfully taken over by driver
-   **NETDEV\_TX\_BUSY**: driver tx buffer ring exhausted and therefore cannot take over further data
-   **NETDEV\_TX\_LOCKED**: driver is locked by other CPU - (not for kernels &gt;4.9) reported for drivers who support own locking (feature **NETIF\_F\_LLTX)**

**NETDEV\_TX\_BUSY** and **NETDEV\_TX\_LOCKED** require buffers being **reenqued** into qdisc queues.

### driver queues {#driver queues}

As seen on the RX paths, the driver keeps queues for buffering skb instances before actioning those. That's because the device is working asynchronously from the rest of the stack and by buffering assigned work the rest of the stack further up does not have to block for awaiting the device to finish its work.

#### multiple egress queues {#multiple egress queues}

There is held at least one queue per device by the drivers in case it's a queueful device.

#### **locking**

It is important to understand that there has to be some form of locking implemented for accessing a queue in case there are more CPUs than queues to prevent races for the then shared resource.

Many CPUs accessing fewer queues may lead to a egress performance degrading high **cpu contention**.

For **kernels &lt;4.9** contention is visible in the procFS as dump of the per CPU `struct softnet_data` as outlined in [RX blog](https://blog.packagecloud.io/eng/2016/06/22/monitoring-tuning-linux-networking-stack-receiving-data/#monitoring-network-data-processing). It's the ninth value represented,`sd->cpu_collision.`{.language-c}This counter shows the number of CPU collisions having occurred up to now, but only if the driver supports its own locking. The driver indicates that by the feature flag **NETIF\_F\_LLTX**. Collisions in the sense of how often CPUs have tried and failed send via a device while the device was already held busy by another transmitting CPU. For later kernels, this counter has been made unused and always shows zero, since **NETIF\_F\_LLTX** has been declared as a deprecated driver feature. You can also infer the frequency of collisions from the number of reenqueuing occurrences further up in the stack in the qdisc statistics - but it's rather hidden, since reenqueuing does not only occurr since of lock contentions.

Noteworthy is, there are two main locks related to transmitting. First the qdisc lock which does not lead to a collision, since it's implemented as a spin lock. If the qdisc is being locked at the moment by a CPU, further CPUs wait actively until the holder releases the lock.

-   **spin\_lock(root\_lock)** is noticeable in \_\_dev\_xmit\_skb and qdisc\_restart introced further up
-   it's released as soon as egress code paths are approaching the driver lock, e.g. ****sch\_direct\_xmit as** spin\_unlock(root\_lock)**, so to confine locking for qdisc to a absolutely needed minimum until driver lock is held: interleaved locking so to speak

In former kernels, if the driver supports **NETIF\_F\_LLTX** and the driver is locked by a CPU, further contending for it leads to a collision by returning **NETDEV\_TX\_LOCKED**, requeuing the colliding CPUs outgoing skbs in the qdisc queue an retrying it in a future rescheduled TX softIRQ loop.

In **sch\_direct\_xmit** you can investigate the driver locking macros:

-   **HARD\_TX\_LOCK**
-   **HARD\_TX\_UNLOCK**

Those are setting a spinlock protected per tx queue cpu reservation flag, or leave locking work to the driver in case **NETIF\_F\_LLTX** supported

That says: for drivers not supporting **NETIF\_F\_LLTX**, all driver locking is done by the kernel by active locking.

Collisions in whatever form or interpretation are worthwile to alleviate. A perfect means is to fully do away with collision in whatever form since of driver contention is giving each CPU it's own egress queue(s) - see next section.

#### Transmit Packet Steering - XPS {#xps}

A means to tackle high **cpu contention** is a kernel mechanism called **XPS**. It can reduce the contention occurrences by allocating certain CPUs to certain queues. In the ideal case, when there are at least as many queues as CPUs present, every CPU thereby does get its own queue(s) allocated and sufferings from contention overhead is cut down to zero. There are quite some drivers around, which handle their own egress queue picking and thereby overrule XPS.  Equally important is the feature of XPS to increase the cache locality of packets to be sent to the cache hierachary of the actually sending CPU. In case there are several CPUs with different cache hierarchies available in your system, it goes without saying that it makes the most sense to share queues amongst CPUs which are also sharing the same cache hierarchy.

**netdev\_pick\_tx** consulted in \_\_**dev\_queue\_xmit**, deals with the actual TX queue selection: [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#netdev_pick_tx)

> ``` {style="color:#000000;background:#ffffff none repeat scroll 0 0;"}
> int queue_index = 0;
>
> /*...*/
>
>         if (dev->real_num_tx_queues != 1) {
>                 const struct net_device_ops *ops = dev->netdev_ops;
>                 if (ops->ndo_select_queue)
>                         queue_index = ops->ndo_select_queue(dev, skb, accel_priv,
>                                                             __netdev_pick_tx);
>                 else
>                         queue_index = __netdev_pick_tx(dev, skb);
> /*...*/
>         }
>
>         skb_set_queue_mapping(skb, queue_index);
>         return netdev_get_tx_queue(dev, queue_index);
> ```

Quite a few steps:

-   only act if real multiqueueing available
-   **XPS** won't pick a TX queue if the **driver** supports its **own picking mechanism** with **ndo\_select\_queue**
-   let **\_\_netdev\_pick\_tx** do the grunt picking work - details in following**  
   **
-   **skb\_set\_queue\_mapping** associates the choice with the current skb - quite astounding, I thought first, but via this channel, XPS communicates it's choice down to the driver, if it does not support **ndo\_select\_queue**
-   hand back to \_\_**dev\_queue\_xmit** the chosen txq context

**\_\_netdev\_pick\_tx** is too simplistic and mundane to show it, since it's name is quite descriptive enough:

-   it determines current queue\_index
-   if the current index has not been set yet or the queue number changed or out of order packets are acceptable, then determine a new index with **get\_xps\_queue**
-   return the outcome

Quite of intereset though, is **get\_xps\_queue**. Having a look at it answers the question if a CPU to TX queue mapping is necessarly confined to a 1:1 relationship - the rest shows up as expected: [/net/core/dev.c](http://lxr.free-electrons.com/source/net/core/dev.c#L3208)

> ``` {style="color:#000000;background:#ffffff;"}
>         dev_maps = rcu_dereference(dev->xps_maps);
>         if (dev_maps) {
>                 map = rcu_dereference(
>                     dev_maps->cpu_map[skb->sender_cpu - 1]);
>                 if (map) {
>                         if (map->len == 1)
>                                 queue_index = map->queues[0];
>                         else
>                                 queue_index = map->queues[reciprocal_scale(skb_get_hash(skb),
>                                                                            map->len)];
>                         if (unlikely(queue_index >= dev->real_num_tx_queues))
>                                 queue_index = -1;
>                 }
>         }
>         rcu_read_unlock();
>
>         return queue_index;
> ```

-   it determines the configures per CPU to TX queue map
-   trivially fetch the mapping value if it's 1:1 association
-   but if the queue is longer than a 1:1 relationship, **reciprocal\_scale(skb\_get\_hash(skb),** **map-&gt;len)** distributes the packets based on their **flow hash** - so the packets are steered to TX queues based on which flow they belong to - astounding!

### egress driver ring length

It might be better to rely on [BQL](https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/) ever since kernel 3.13 than adjust the driver queue length size manually to find a reasonable balance between  [latency an ](https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/)[throughput](https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/)[(starvation)](https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/).

#### Tuning {#Tuning}

#### apply XPS {#apply XPS}

Prerequisites:

-   kernel with **CONFIG\_XPS** enabled
-   multiple egress TX queues driver capability - XPS has no effect for a TX single queue

Kernels with XPS configured offer a bitmap per TX queue via **SysFs**:

>     /sys/class/net//queues/tx-/xps_cpus

E.g. to allocate **CPU1** to **tx\_queue 2** for driver behind **iface enp2s0**:

> echo **1** &gt; /sys/class/net/**enp2s0**/queues/**tx-2**/xps\_cpus

### **multi queuing**

The by the driver as a default offered TX queue number and outline are usually not the optimal one for your current workload and environment.

Adjustments are being done symmetrically to the approach on [RX side](https://blog.packagecloud.io/eng/2016/06/22/monitoring-tuning-linux-networking-stack-receiving-data/#adjusting-the-number-of-rx-queues). Nevertheless, for completeness sake, I'll repeat the essentials.

#### adjust queue count

Check for the current and max queues number supported by the NIC driver first.

> \# ethtool -l **ens3**
>
> Channel parameters for **ens3**:  
> Pre-set maximums:  
> RX:        0  
> **TX:        0**  
> Other:        0  
> **Combined:    8**  
> Current hardware settings:  
> RX:        0  
> **TX:        0**  
> Other:        0  
> **Combined:    1**

Again, you can adjust the egress number in two equally effective ways. Remember that setting it in a combined manner, though, scales both - the RX and TX  queue number.

> \# ethtool -L combined 8

Or to set egress only:

> \# ethtool -L  tx 8

Now, you can recheck your settings with **ethtool -l** .

#### adjust queue length {#adjust queue length}

If [BQL](https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/) is ready in your kernel,  adapting the the driver queues might become an unecessary or redundant step to take.

First, you should check the maximal and currently applied length.

>     # ethtool -g ens3
>     Ring parameters for eth0:
>     Pre-set maximums:
>     RX:   4096
>     RX Mini:  0
>     RX Jumbo: 0
>     TX:   4096
>     Current hardware settings:
>     RX:   512
>     RX Mini:  0
>     RX Jumbo: 0
>     TX:   512

Then, you can increase it to the whatever length you see fit - here the maximum.

> \# ethtool -G **ens3** ***tx*** **4096**

### Hard-IRQs {#Hard-IRQs}

You might have noticed that for the egress paths, no Hard-IRQ handling for any interrupt technology are registered. It has been pointed out [further up](#__netif_schedule)  that the egress stack code parts have a self triggering nature based on driver feedback of current transmission capabilities. The NIC is not interrupting the kernel as you've seen for the RX stack world, at least not to form feedback to it.

Nevertheless, the driver has to do some internal housekeeping, which it's triggering with TX hard irqs. See as a reference [transmit-completions section](https://blog.packagecloud.io/eng/2017/02/06/monitoring-tuning-linux-networking-stack-sending-data/#transmit-completions) of a similar article to that by now

### CPU egress election {#election}

What is determing which CPU is used for the egress processing if not the IRQ as on RX side? In case you've read this article completely, you can tell by now, it's as simple as on which CPU the user land processing that is transmitting has been scheduled in.

Conclusion
==========

Enjoy the first draft. I've still to refine some parts. Comments for improvement or wishes/suggestions for content extensions are quite welcome.

Appendix {#Appendix}
========

### Illustrations

### Driver Queue Based Scaling {#Driver Queue Based Scaling}

\[caption id="attachment\_2321" align="alignnone" width="11871"\]![ns\_tx\_driv\_qu\_scale.svg]({static}2016/12/ns_tx_driv_qu_scale-svg.png){.alignnone .size-full .wp-image-2321 width="11871" height="7540"} [To SVG](https://github.com/cherusk/kannjan/blob/master/ns_tx_driv_qu_scale.svg)\[/caption\]
