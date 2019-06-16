Title: Light as Air - Towards an Airborne, Speed of Light Internet backbone
Date: 2017-12-26 22:52
Author: cherusk
Category: Visions 
Tags: airborne internet backbone, airborne networking, airship, atmospheric mitigation techniques, backbone internet, c-ISP, cable to sky, fibre backbone, FSO links, future backbones, global backbone network, HAP, high altitude platform, internet engineering, laser communication, optics, radio links, research, satellites, space-to-earth-link, speed of light, theory, up/down link, wan networks, wireless
Slug: speed-of-light-in-the-air-towards-an-airborne-internet-backbone
Status: published
Attachments: 2017/12/atm_fso_princip1.png, 2017/12/steer_mitig.png, 2017/12/fibre_mitig.png, 2017/12/glob_top_zoom.png, 2017/12/glob_top_zoom1.png

Abstract
========

There is increasing movement in the Internet backbone siblings creation movement globally. That's foremost the case for special domains like the armament sector or the space flight industries, because those are in pressing need for such facilities in order to fulfill their missions. In line with that, airships have regained significant attention, not only for their superior cargo long-haul capabilities to hardly accessible sites as raw material gaining areas for instance. Commonly accepted is even more that airships are an adequate fit for long-term aerial endeavors like research or surveillance tasks in contrast to other aircraft categories, because of their superior traits in respect to long-time flight endurance, high degree of dirigibility, energy efficiency, flexibility in altitude transitioning, higher landing  site agnosticism. As a consequence, many private and public corporations have therefore embraced airships - in the form a aerial aloft platforms - as an options to merely base themselves on traditional physical forms as cabling or terrestrial micro-wave long-distance network to extend the global Internet. The prevailing physical channel for up-linking to airship-platforms is a ground operated radio-technologies based transceiver system, although FSO technologies are on the verge of maturing even in harsh weather conditions or other detrimental scenarios for  wireless connectivity. FSO links have recently gained reasonable attention in research and engineering for inter space\[4\]\[5\]\[6\] and space-to-earth communications\[3\] - although mostly for extending the terrestrial network coverage, but not for forming a fully parallel infrastructure. With respecting, extending and melding the ongoing approaches in the field of an airborne internet, by proposing an FSO oriented airborne Internet backbone this article aims at documenting a communication basis in order to spur up advances in bringing about a Speed of Light capable backbone internet on a broader scope.

Architectural Principle
=======================

In the illustrations of this section one can see the most basic principle of an FSO based airborne backbone internet. A set of core airborne platforms that form the basis for wide area networks. Whereby the most probable approach would be to let these core airships be equipped comparably to a routing device in a terrestrial equivalently formed network. The core airships shall reside in the lowest density compartments of earth near atmoshpere in order to not suffer from too many detrimental atmospheric random influences on the inter-backhaul-links - see further down for mitigations. As illustrated in \[Fig1\], most of the atmospheric randomness - roughly 90 % - would reside beneath this flight altitude of the core\[3\]. Recent FSO developments shall be able to easily cope with this degree of atmospheric dilution\[2\]. One of the key posits of this article is the statement that FSO can operate in this subrange of the atmosphere with an even better network link performance effectiveness (for latency and bandwidth) than terrestrial fibre based networks.

> ### <span style="text-decoration:underline;"> Theoretical lower layer path technologies comparison:</span>
>
> ### expectable **c** approximation  by
>
> 1\. **Terrestrial Fibre**
>
> Refractive index of widely deployed optical fibre\[8\] **r\_o** \~ **1.4**
>
> 2\. **High altitude operated FSO**
>
> Refractive index of photons in clean atmospheric air **r\_ca**  \~ **1.0003**
>
> In perspective:
>
> The improvement factor can be in the extreme ideal case at around the following improvent factor:
>
> factor\_impr = **r\_o / r\_ca = 1,39**

Further, in the core network airships the most sophisticated laser aggregate will have to placed as well. It must be able to cater for different FSO types, e.g. ground and inter-back-haul link ones in the trivial case. It must support superior laser core peer platform targeting and influxing laser beam pointing auxiliary appliances to allow forming connections in the first place.


![Global Topology]({static}2017/12/atm_distr_globe.png)![Global Topology Magnified]({static}2017/12/glob_top_zoom1.png)

Ground located FSO transceivers are then relaying the core ground based internet traffic via multipathed optical channels to the core airborne forwarding platforms. Thereby, easily technical difficulties are perceivable that are mostly down to physical random phenomena which interfere with and degrade optical links. These are mostly connected to weather and geographical location.\[3\] To name a few, storm clouds, rain, snow or atmospheric turbulences.  Multipathing acts as a mitigation mechanism and a bandwidth scaling lever\[3\]. At the time of writing this,  10  FSO links with a maximum of 10 Gbit/s are feasible\[2\]. Nominally, therefore, to come into competition range of terrestrially based solutions, multipathing for at least the multipathing factor (***terrestrial bandwith)/(max FSO link bw)*** would have to be procured for. For a modestly scaled terrestrial link, this would juxtapose to a FSO multipathing factor of roughly **10**.

 

---
![FSO Airborne Backbone Principle in Atmospheric Layering]({static}2017/12/atm_fso_princip1.png){.alignnone .size-full .wp-image-2761 width="3964" height="3055"} Fig1.: FSO Airborne Backbone Principle in Atmospheric Layering}

Since as covered further down in this article, an overall controlling/steering concept for such a large scale network system is needed, the best might be to also have the network decision taking computations steering happen in a centric manner, in the form of a ground operated SDN.

The channel for the steering signaling can be implemented over the existing FSO links if the resiliency of those is reliable enough, elsewise a degradation approach is thinkable whereby one is falling back to redundantly operated radio- based links

Advantages and Technical Gain
=============================

This article is mainly driven by intelligence gained from \[1\], specifically the fact that lower layer RTT path inflation plays a multiplicative role and therefore is the more decisive knob when trying to go about overall network performance. Higher layer optimizations - e.g. in the networking stack - rather play only a linear role depending on where optimization engineering is being seized. To tap into this fact, the authors propose a speed of light capable terrestrial microwave network in parallel the in bulk existing  fibre core backbone - they call it a c-ISP. Microwave transmissions is closer to the actual speed of light performance for network latency than most recently available fibre fabrics. This article here proposes as an alternative to a terrestrial c-capable ISP - the atmospheric airborne variant based on optics which in addition to the low latency of microwave channels offers a far higher bandwidth per link, thereby covering both degrees of freedom of network performance optimization.

-   Abundant bandwidth in addition to improved c-capable latencies.
    -   Expected quicker implementation than a large scope terrestrial c-capable backbone sibling for long-haul links that have cross huge distance or natural obstacles like oceanas. With large scope it meant that the implementation is not confined to specific domains but the common, public internet.
    -   Quicker feasibility of services\[1\] that are highly depending not only on the latency offered by a c-ISP, but also on current backbone comparative high bandwidth features which optics can deliver at this speeds.
-   Shorter link paths and therefore less path inflation than optics backbone long-haul networks between HAP and orbital satellites\[3\].
-   Superior maintenance characteristics\[3\] than HAP to satellites systems.
-   Solid concept for non-earth, atmospheric planets backbone networks yet to be deceived and engineered.

Enhanced Mitigation Approaches to Communication Channel degradations
====================================================================

The most obvious, quite effective and already scientifically covered\[3\] approach to mitigating optics disturbances would be to form a flock of interconnectable relaying agent airships operating pervasively on lower altitudes operating in order to make disturbances highly reactively circumventable. You can see this way of mitigating in \[Fig2\]. Relaying entities and grounds station operations again would need precise synchronization. By increasing the density, this would become less burdensome.

![Mitigation by steering]({static}2017/12/steer_mitig.png){.alignnone .size-full .wp-image-2762 width="3822" height="2913"} Fig2: Mitigation by steering

Novel, though, is the idea to actually bridge the lower atmospheric layers to the core airships by maintaining again some airborne utility platforms geared system. This time, those utility entities would be needed to support an optical fibre cable link to the backbone platforms. This can shield the terrestrial-to-air initial hop from atmospheric effects completely. The technically incurred performance cost can be held confined thereby as well - see \[Fig3\].

![Mitigation by fibre link to platform]({static}2017/12/fibre_mitig.png){.alignnone .size-full .wp-image-2763 width="3822" height="2913"} Fig,3: Mitigation by fibre link to platform

Airships are know to be able to carry high volumes of masses,  in the range of tons. When respecting technical clearance, a roughly 25 km long fibre fabrics containing cable is not able to put a properly sized airship carrier at it's technical limits.

Even for dense packed fibre cables \[2\], one can on average expect a mass of roughly

> cable\_mass = 25 km  \* 280kg/km = 7000 kg = 7 t

per cable. Apparently, there's enough room for scaling the cable up.

Future Work
===========

-   Sophistication and prototyping of a central control system for the large scale orchestration of afloat entities and ground operated up/down-link-mechanisms.
-   More research into FSO long distance transmission at the proposed high altitudes\[3\]\[7\].
-   Validating feasibility of procuring a large scale cable to the core backbone airships as a mitigation approach.

References
==========

\[1\] [Towards a Speed of Light Internet](https://arxiv.org/pdf/1505.03449.pdf)

\[2\] <https://phys.org/news/2017-08-high-bandwidth-capability-ships.html>

\[3\] [Optical Communication in Space: Challenges and Mitigation Techniques](https://arxiv.org/pdf/1705.10630.pdf)

\[4\] <https://www.nasa.gov/feature/goddard/2017/nasa-taking-first-steps-toward-high-speed-space-internet>

\[5\] <https://www.nasa.gov/feature/new-solar-system-internet-technology-debuts-on-the-international-space-station>

\[6\] <https://www.nasa.gov/feature/goddard/2017/tdrs-an-era-of-continuous-space-communications>

\[7\] [Channel Modelling for Free-Space Optical Inter-HAP Links Using Adaptive ARQ Transmission](https://pdfs.semanticscholar.org/83b3/904ff55fadaf4825cc1771c3bbcf2f5edf52.pdf)

\[8\] <https://en.wikipedia.org/wiki/Optical_fiber#Index_of_refraction>

Acronyms
========

**FSO**: Free-Space-Optics

**FIB:** Forwarding Information Base**  
**

**SDN:** Software Defined Networking

**HAP:** High altitute platform

**RTT:** Round Trip Time**  
**

**c-ISP**: c as the physics symbol for speed of light and ISP for internet service provider

 
