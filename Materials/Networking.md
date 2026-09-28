# Computer Networking Fundamentals for Google Interviews

> Goal: Build a precise mental model from packets and sockets through DNS, TCP,
> TLS, HTTP, load balancing, performance, security, and production debugging.
> Examples use Python where code clarifies the protocol behavior.

## Table of Contents

* [1. The Network Mental Model](#1-the-network-mental-model)
* [2. Layered Network Models](#2-layered-network-models)
* [3. Link Layer: Ethernet, MAC, and Switching](#3-link-layer-ethernet-mac-and-switching)
* [4. Internet Layer: IP, Subnets, and Routing](#4-internet-layer-ip-subnets-and-routing)
* [5. Transport Layer: UDP and TCP](#5-transport-layer-udp-and-tcp)
* [6. DNS and Service Discovery](#6-dns-and-service-discovery)
* [7. HTTP and Application Protocols](#7-http-and-application-protocols)
* [8. TLS and Secure Communication](#8-tls-and-secure-communication)
* [9. Proxies, Load Balancers, and CDNs](#9-proxies-load-balancers-and-cdns)
* [10. Sockets and Network Programming](#10-sockets-and-network-programming)
* [11. Performance and Capacity](#11-performance-and-capacity)
* [12. Reliability and Distributed-System Semantics](#12-reliability-and-distributed-system-semantics)
* [13. Network Security Fundamentals](#13-network-security-fundamentals)
* [14. Debugging and Observability](#14-debugging-and-observability)
* [15. End-to-End Packet Walkthroughs](#15-end-to-end-packet-walkthroughs)
* [16. Google Interview Questions](#16-google-interview-questions)
* [17. Quick Reference](#17-quick-reference)

## 1. The Network Mental Model

A network lets processes on different machines exchange bytes. Applications do
not normally construct electrical or radio signals themselves. They write bytes
to a socket, and the operating system plus network devices move those bytes.

```text
Application
    |
    v
Socket API
    |
    v
Operating-system network stack
    |
    v
Network interface -> switches -> routers -> remote network interface
    |
    v
Remote operating-system network stack
    |
    v
Remote socket -> remote application
```

Every layer solves a narrower problem:

* The link layer moves frames across one local link
* IP moves packets across interconnected networks
* TCP or UDP delivers data between processes identified by ports
* TLS can add confidentiality, integrity, and peer authentication
* Application protocols such as HTTP define what the bytes mean

### Core Vocabulary

| Term | Meaning |
|------|---------|
| Host | A machine or network namespace participating in a network |
| Node | Any communicating endpoint or forwarding device |
| Link | A direct network segment, physical or virtual |
| Frame | Link-layer unit, such as an Ethernet frame |
| Packet | Internet-layer unit, usually an IP packet |
| Segment | TCP transport-layer unit |
| Datagram | Self-contained message, commonly an IP or UDP unit |
| Protocol | Rules defining message format and interaction |
| Interface | A host's attachment to a network |
| Address | Identifier used at a particular layer |
| Port | 16-bit transport-layer identifier for an endpoint on a host |
| Socket | OS abstraction for a communication endpoint |
| Connection | Logical communication relationship between endpoints |
| Flow | Related packets identified by endpoint and protocol fields |
| Hop | One router traversal along a path |
| MTU | Largest network-layer packet carried by a link without fragmentation |
| RTT | Round-trip time between endpoints |
| Bandwidth | Maximum data-transfer capacity per unit time |
| Throughput | Data actually transferred per unit time |
| Goodput | Useful application data transferred per unit time |

### The Five-Tuple

A transport flow is commonly identified by:

```text
(source IP, source port, destination IP, destination port, protocol)
```

For example:

```text
(10.0.0.8, 53144, 142.250.77.14, 443, TCP)
```

The source port allows one client to maintain many simultaneous connections to
the same server. The OS uses the complete tuple, not the destination port alone,
to deliver incoming segments to the correct socket.

### Control Plane and Data Plane

The data plane forwards actual traffic. The control plane decides how traffic
should be forwarded.

| Plane | Examples |
|-------|----------|
| Data plane | Switching frames, routing packets, applying firewall rules |
| Control plane | Learning MAC addresses, exchanging routes, computing paths |

This distinction appears in routers, software-defined networks, service meshes,
and load balancers.

## 2. Layered Network Models

Layering lets each protocol depend on a stable service from the layer beneath
it. A web request can use HTTP over TLS over TCP over IP over Ethernet without
HTTP understanding Ethernet details.

### OSI and TCP/IP Models

| OSI Layer | Purpose | Examples | TCP/IP Group |
|-----------|---------|----------|--------------|
| 7 Application | Application semantics | HTTP, DNS, SMTP, gRPC | Application |
| 6 Presentation | Representation, encoding, encryption | TLS, JSON, UTF-8 | Application |
| 5 Session | Dialog and session management | RPC session concepts | Application |
| 4 Transport | Process-to-process delivery | TCP, UDP, QUIC | Transport |
| 3 Network | Host addressing and routing | IPv4, IPv6, ICMP | Internet |
| 2 Data link | Delivery on one link | Ethernet, Wi-Fi, ARP | Link |
| 1 Physical | Bits as signals | Copper, fiber, radio | Link |

The OSI model is valuable for reasoning, but the Internet protocol suite does
not follow all seven layers literally. For example, TLS is commonly discussed
between transport and application even though OSI associates encryption with
the presentation layer.

### Encapsulation

As data moves downward, each layer adds a header and sometimes a trailer.

```text
HTTP message
  -> [TLS header | encrypted application data]
  -> [TCP header | TLS record]
  -> [IP header | TCP segment]
  -> [Ethernet header | IP packet | frame check sequence]
  -> bits on a link
```

The receiver removes these wrappers in reverse order. A router usually examines
the link and IP headers, not the application data. A layer-7 proxy terminates
the transport connection and understands HTTP.

### Addresses at Different Layers

| Layer | Identifier | Scope |
|-------|------------|-------|
| Link | MAC address | One local broadcast domain |
| Internet | IP address | Routable across networks |
| Transport | Port | Process or service endpoint on a host |
| Application | Name or resource | Domain, URL, RPC method, user identity |

Do not say that a MAC address routes traffic across the Internet. MAC addresses
change hop by hop; source and destination IP addresses normally remain stable
end to end unless NAT rewrites them.

### Devices by Layer

| Device | Primary Layer | Main Decision |
|--------|---------------|---------------|
| Repeater or hub | 1 | Repeat signals or bits |
| Switch or bridge | 2 | Forward by destination MAC address |
| Router | 3 | Forward by destination IP prefix |
| L4 load balancer | 4 | Route by IP, port, and transport state |
| L7 proxy | 7 | Route by host, path, headers, or application data |

Real devices often operate at several layers, but this classification identifies
the decision that matters for an interview answer.

## 3. Link Layer: Ethernet, MAC, and Switching

The link layer moves data across one local network segment. Ethernet and Wi-Fi
are common link technologies.

### Ethernet Frames

A simplified Ethernet frame contains:

```text
[destination MAC | source MAC | EtherType | payload | frame check sequence]
```

EtherType identifies the payload protocol, such as IPv4 or IPv6. The frame check
sequence detects corruption on the link. A corrupted frame is normally dropped;
Ethernet itself does not provide end-to-end retransmission.

### MAC Addresses

A MAC address is typically a 48-bit link-layer identifier:

```text
3c:52:82:ab:19:f0
```

Important address types include:

* Unicast for one interface
* Broadcast (`ff:ff:ff:ff:ff:ff`) for every node in a broadcast domain
* Multicast for a subscribed group

A host needs the next hop's MAC address to send an Ethernet frame. The next hop
may be the final destination on the same subnet or the default gateway for a
remote destination.

### Switch Learning

An Ethernet switch builds a MAC address table by observing the source MAC on
incoming frames:

```text
MAC A learned on port 1
MAC B learned on port 4
```

For a known destination, it forwards only to the learned port. For an unknown
unicast destination, it floods the frame to other ports in the same VLAN. Table
entries age out because hosts can move.

### ARP and Neighbor Discovery

IPv4 Address Resolution Protocol (ARP) maps a local IPv4 address to a MAC
address.

```text
Host: Who has 192.168.1.1? Tell 192.168.1.20.
Gateway: 192.168.1.1 is at 9c:3d:cf:12:34:56.
```

The request is broadcast and the reply is normally unicast. Results are cached
for a limited time. IPv6 uses Neighbor Discovery Protocol over ICMPv6 instead
of ARP.

ARP resolves only local next hops. A host does not ARP for a server on another
network; it ARPs for the default gateway and sends the remote IP packet inside
a frame addressed to the gateway's MAC.

### VLANs

A virtual LAN creates separate layer-2 broadcast domains on shared switching
hardware. Devices in different VLANs need a router or layer-3 switch to
communicate.

VLANs provide segmentation and operational isolation. They are not encryption
and should not be treated as the sole security boundary.

### MTU and Fragmentation

Ethernet commonly uses an MTU of 1500 bytes for its IP payload. Headers consume
part of that budget. With typical IPv4 and TCP headers:

$$
MSS = MTU - 20_{IPv4} - 20_{TCP} = 1460\text{ bytes}
$$

The TCP Maximum Segment Size (MSS) is the largest TCP payload a peer advertises
for one segment under normal header assumptions.

IPv4 routers can fragment packets unless the Don't Fragment bit is set. IPv6
routers do not fragment transit packets. Endpoints use Path MTU Discovery to
learn a safe packet size. Blocking required ICMP messages can cause a path MTU
black hole: small traffic works while large transfers stall.

## 4. Internet Layer: IP, Subnets, and Routing

IP provides best-effort delivery across networks. Best effort means packets can
be lost, duplicated, delayed, corrupted before detection, or delivered out of
order. Higher layers handle stronger guarantees when required.

### IPv4 and IPv6

| Property | IPv4 | IPv6 |
|----------|------|------|
| Address size | 32 bits | 128 bits |
| Example | `192.0.2.10` | `2001:db8::10` |
| Address space | About $2^{32}$ | $2^{128}$ |
| Broadcast | Supported | Replaced by multicast patterns |
| Router fragmentation | Possible | Not performed by routers |
| Address resolution | ARP | Neighbor Discovery |

IPv6 compresses consecutive zero groups once with `::`. Leading zeros within a
group can be omitted.

### Important Address Ranges

| Purpose | IPv4 | IPv6 |
|---------|------|------|
| Loopback | `127.0.0.0/8`, commonly `127.0.0.1` | `::1/128` |
| Private | `10.0.0.0/8` | Unique local `fc00::/7` |
| Private | `172.16.0.0/12` | |
| Private | `192.168.0.0/16` | |
| Link-local | `169.254.0.0/16` | `fe80::/10` |
| Documentation | `192.0.2.0/24` and other reserved blocks | `2001:db8::/32` |

`localhost` is a hostname commonly resolving to a loopback address. Binding a
server to `127.0.0.1` exposes it only locally. Binding to `0.0.0.0` means all
local IPv4 interfaces, subject to firewall and network policy.

### CIDR and Subnetting

Classless Inter-Domain Routing (CIDR) writes a network prefix as an address and
prefix length:

```text
192.168.10.0/24
```

`/24` means the first 24 bits identify the network and 8 bits identify addresses
inside it. The number of addresses is:

$$
2^{address\ bits - prefix\ length}
$$

For IPv4 `/24`:

$$
2^{32-24} = 256\text{ addresses}
$$

Traditional IPv4 subnets reserve the all-zero host value as the network address
and the all-one value as the broadcast address, leaving 254 conventional host
addresses in a `/24`. Point-to-point and provider-specific rules can differ.

Common IPv4 sizes:

| Prefix | Addresses | Conventional Usable Hosts | Netmask |
|--------|-----------|---------------------------|---------|
| `/8` | 16,777,216 | 16,777,214 | `255.0.0.0` |
| `/16` | 65,536 | 65,534 | `255.255.0.0` |
| `/24` | 256 | 254 | `255.255.255.0` |
| `/25` | 128 | 126 | `255.255.255.128` |
| `/26` | 64 | 62 | `255.255.255.192` |
| `/30` | 4 | 2 | `255.255.255.252` |
| `/32` | 1 | One exact address | `255.255.255.255` |

To test membership, bitwise-AND the address with the netmask:

```text
IP:       192.168.10.77
Mask:     255.255.255.0
Network:  192.168.10.0
```

### Routing Tables

A host or router chooses a route using the most specific matching prefix, called
longest-prefix match.

```text
Destination          Next hop       Interface
10.20.0.0/16         192.168.1.2    eth0
10.20.30.0/24        192.168.1.3    eth0
0.0.0.0/0            192.168.1.1    eth0
```

Traffic for `10.20.30.8` uses the `/24` route because it is more specific than
the `/16`. The default route `/0` matches when no specific route does.

A router performs roughly these steps:

1. Remove the incoming link-layer frame.
2. Validate and inspect the IP packet.
3. Decrement TTL or Hop Limit.
4. Select a route by longest-prefix match.
5. Resolve the next hop on the outgoing link if needed.
6. Place the packet in a new link-layer frame and transmit it.

The Ethernet header changes at every routed hop. The IP source and destination
normally do not, except when NAT or another middlebox rewrites them.

### TTL, ICMP, Ping, and Traceroute

IPv4 Time To Live and IPv6 Hop Limit prevent routing loops from circulating
packets forever. Every router decrements the value. At zero, the router drops
the packet and commonly returns an ICMP Time Exceeded message.

`ping` commonly uses ICMP Echo Request and Echo Reply to test reachability and
measure RTT. Failure to receive a reply does not prove the host is down because
firewalls may block ICMP.

Traceroute sends probes with increasing TTL values. Each router that expires a
probe reveals one hop through an ICMP response. Paths can be asymmetric, load
balanced, hidden, or filtered, so output is evidence rather than a perfect map.

### DHCP

Dynamic Host Configuration Protocol assigns configuration such as an IP
address, subnet mask, default gateway, and DNS servers. A simplified IPv4 flow
is DORA:

```text
Discover -> Offer -> Request -> Acknowledge
```

The initial client lacks an address, so DHCP relies on broadcast and relay
mechanisms. Leases expire and must be renewed.

### NAT and PAT

Network Address Translation rewrites addresses. Port Address Translation (PAT),
often called NAT overload, lets many private endpoints share one public IPv4
address by translating source ports.

```text
10.0.0.5:51000 ----\
10.0.0.6:51000 ----- NAT gateway ---> 203.0.113.8:62001/62002
10.0.0.7:53000 ----/
```

The gateway keeps translation state so replies return to the correct private
endpoint. NAT complicates inbound connections, peer-to-peer communication, and
protocols that embed addresses in payloads. NAT is not a substitute for a
firewall, although stateful NAT often blocks unsolicited inbound flows as a
side effect.

### Routing Within and Between Networks

Interior gateway protocols, such as OSPF and IS-IS, distribute routes within an
administrative domain. Border Gateway Protocol (BGP) exchanges reachability
between autonomous systems on the Internet.

BGP selects policy-compliant paths, not necessarily the physically shortest or
lowest-latency path. Operators consider attributes, business relationships, and
route policy. Route aggregation reduces routing-table size by advertising a
larger prefix that represents smaller networks.

### Unicast, Broadcast, Multicast, and Anycast

| Mode | Meaning | Example |
|------|---------|---------|
| Unicast | One sender to one destination | Typical TCP connection |
| Broadcast | One sender to all nodes on a local domain | IPv4 ARP request |
| Multicast | One sender to an interested group | Streaming or routing protocols |
| Anycast | Same IP announced from multiple locations | DNS or CDN edge service |

Anycast routing generally sends a client to a topologically preferred site. It
does not guarantee the geographically nearest or permanently stable endpoint.

## 5. Transport Layer: UDP and TCP

The transport layer delivers data between application endpoints. Ports provide
multiplexing within a host.

### Ports and Sockets

Ports range from 0 to 65535:

* 0 through 1023 are well-known ports
* 1024 through 49151 are registered ports
* 49152 through 65535 are the IANA dynamic or private range

Operating systems choose ephemeral client ports from a configurable range that
may differ from the IANA range.

Common ports include:

| Port | Typical Protocol |
|------|------------------|
| 22/TCP | SSH |
| 53/UDP and TCP | DNS |
| 80/TCP | HTTP |
| 443/TCP and UDP | HTTPS over TCP; HTTP/3 over QUIC/UDP |
| 123/UDP | NTP |
| 25/TCP | SMTP |

Ports are conventions, not proof of protocol. A program can serve HTTP on port
8080 or arbitrary bytes on port 443.

### UDP

User Datagram Protocol is message-oriented and connectionless at the protocol
level. It adds source port, destination port, length, and checksum around an
application datagram.

UDP provides:

* Process multiplexing through ports
* Datagram boundaries
* Checksum-based corruption detection

UDP does not provide:

* Guaranteed delivery
* Ordering
* Duplicate suppression
* Retransmission
* Flow control
* Congestion control
* Connection establishment

Applications choose UDP when low overhead, message boundaries, multicast, or
custom reliability and timing policies matter. Examples include DNS, real-time
media, gaming, telemetry, and QUIC's transport substrate.

UDP is not inherently faster in every application. A reliable UDP-based system
must implement the missing mechanisms, and responsible Internet applications
still need congestion control.

### TCP as a Byte Stream

Transmission Control Protocol provides a reliable, ordered, full-duplex byte
stream between endpoints. It does not preserve application message boundaries.

If a sender calls:

```python
sock.sendall(b"hello")
sock.sendall(b"world")
```

the receiver might observe `helloworld`, `hello` then `world`, or smaller chunks.
Applications must define framing, such as:

* Fixed-size messages
* Delimiter termination
* Length-prefixed messages
* Self-describing formats with an explicit parser

This is the source of the interview phrase, "TCP is a stream, not a message
queue." One `send()` does not correspond to one `recv()`.

### TCP Connection Establishment

The three-way handshake synchronizes sequence-number spaces and confirms
bidirectional reachability:

```text
Client                                  Server
  | ------ SYN, seq=x ----------------> |
  | <----- SYN-ACK, seq=y, ack=x+1 -----|
  | ------ ACK, ack=y+1 --------------> |
  |          connection established     |
```

The handshake also negotiates options such as MSS, window scaling, timestamps,
and selective acknowledgments. A TCP connection is uniquely distinguished by
its endpoint tuple, allowing one listening port to serve many clients.

### Sequence Numbers and Acknowledgments

TCP numbers bytes, not packets. An acknowledgment value indicates the next byte
expected. If a receiver sends `ACK 5001`, it has received the contiguous byte
stream through byte 5000.

TCP retransmits data inferred to be lost. Detection can occur through a
retransmission timeout or acknowledgment patterns such as duplicate ACKs.
Selective Acknowledgment (SACK) lets a receiver report noncontiguous blocks it
already has, reducing unnecessary retransmission.

TCP reliability means the receiving application gets bytes in order or learns
that the connection failed. It does not guarantee that the remote application
completed a business operation.

### Flow Control

Flow control protects the receiver. The receiver advertises available buffer
space through its receive window. The sender limits unacknowledged data so it
does not overwhelm that receiver.

```text
Receiver capacity -> advertised receive window -> sender limit
```

A zero window pauses new data until the receiver advertises space. Flow control
is distinct from congestion control.

### Congestion Control

Congestion control protects the network. The sender maintains a congestion
window based on evidence of available path capacity and loss or delay.

The usable amount of in-flight data is approximately:

$$
send\ window = \min(receive\ window, congestion\ window)
$$

Core ideas include:

* Slow start increases the window rapidly from a conservative initial value
* Congestion avoidance probes capacity more cautiously
* Loss or explicit congestion signals cause the sender to reduce its rate
* Fast retransmit can repair inferred loss before a timeout

Algorithms such as CUBIC and BBR use different signals and growth policies. In
an interview, explain the goal and feedback loop before naming an algorithm.

### Head-of-Line Blocking

TCP delivers bytes in order. If an earlier segment is missing, later bytes may
already be buffered but cannot be delivered to the application. This is
transport-level head-of-line blocking.

HTTP/2 multiplexes streams within one TCP connection, but packet loss can still
delay all streams because TCP must restore the common byte stream. QUIC gives
streams independent delivery order, reducing cross-stream transport blocking.

### Connection Teardown

TCP directions close independently. A normal full close commonly uses four
segments:

```text
Client                                  Server
  | ------ FIN ------------------------> |
  | <----- ACK --------------------------|
  | <----- FIN --------------------------|
  | ------ ACK ------------------------> |
```

A FIN means "I will send no more bytes," but the peer may continue sending. A
reset (RST) aborts a connection and can discard pending data.

The active closer commonly enters `TIME_WAIT` so delayed segments from the old
connection cannot corrupt a new incarnation and so the final ACK can be
retransmitted. Large numbers of short-lived connections can exhaust ephemeral
ports or create excessive handshake overhead, which motivates connection reuse.

### TCP States Worth Knowing

| State | Meaning |
|-------|---------|
| `LISTEN` | Server awaits connection requests |
| `SYN-SENT` | Client sent SYN |
| `SYN-RECEIVED` | SYN received and SYN-ACK sent |
| `ESTABLISHED` | Bidirectional connection is open |
| `FIN-WAIT-1/2` | Active closer is progressing through shutdown |
| `CLOSE-WAIT` | Peer closed; local application has not closed yet |
| `LAST-ACK` | Local endpoint sent its FIN after peer closure |
| `TIME-WAIT` | Active closer retains state temporarily |

Many `CLOSE-WAIT` sockets often indicate an application that failed to close
connections after peer shutdown. Many `TIME-WAIT` sockets can be normal, but
may expose excessive connection churn.

### TCP Options and Operational Details

* TCP keepalive can probe an idle connection, but default intervals are often
  too long for application failure detection
* Application heartbeats express service-level liveness and can use tighter
  deadlines
* Nagle's algorithm batches small writes to reduce tiny packets
* Delayed ACKs postpone some acknowledgments to reduce overhead
* The interaction of small writes, Nagle, and delayed ACKs can add latency
* `TCP_NODELAY` disables Nagle when latency matters more than packet efficiency
* A half-open connection exists when one side believes a connection is alive
  after the other side or path has failed silently

### TCP vs UDP

| Property | TCP | UDP |
|----------|-----|-----|
| Service | Ordered byte stream | Independent datagrams |
| Setup | Handshake | No transport handshake |
| Reliability | Retransmission and ordered delivery | Application-defined |
| Flow control | Yes | No |
| Congestion control | Yes | Application-defined |
| Message boundaries | No | Yes |
| Multicast | No | Yes |
| Typical use | HTTP/1.1, HTTP/2, SSH, databases | DNS, media, games, QUIC |

### QUIC

QUIC is a secure, reliable transport implemented over UDP, commonly in user
space. It integrates TLS 1.3, congestion control, connection migration, and
multiple independent streams.

QUIC can reduce setup latency and avoids cross-stream TCP head-of-line blocking.
It still retransmits lost stream data and performs congestion control. HTTP/3
runs over QUIC.

## 6. DNS and Service Discovery

The Domain Name System maps hierarchical names to records. It is a distributed,
cached database, not merely a single name-to-address table.

### DNS Hierarchy

For `api.example.com.`:

```text
.              root
com.           top-level domain
example.com.   registered domain
api.example.com. host or service name
```

The trailing dot denotes an absolute fully qualified domain name. It is usually
omitted in user-facing text.

### Recursive Resolution

A typical lookup proceeds as follows:

1. The application checks its own or runtime cache.
2. The OS stub resolver checks local configuration and hosts data.
3. A recursive resolver receives the query.
4. If uncached, it asks a root server where to find `.com`.
5. It asks a `.com` server where to find `example.com`.
6. It asks the authoritative server for `api.example.com`.
7. It caches the answer according to TTL and returns it.

```text
Client -> recursive resolver -> root -> TLD -> authoritative server
              ^                                      |
              `-------------- answer ----------------'
```

The recursive resolver performs work for the client. Root, TLD, and typical
authoritative servers provide referrals or authoritative answers rather than
recursively traversing the hierarchy for that client.

### Common DNS Records

| Record | Purpose |
|--------|---------|
| `A` | Name to IPv4 address |
| `AAAA` | Name to IPv6 address |
| `CNAME` | Alias one name to another canonical name |
| `MX` | Mail exchanger and preference |
| `NS` | Authoritative name server for a zone |
| `TXT` | Text data, often verification or email policy |
| `PTR` | Reverse address-to-name lookup |
| `SOA` | Zone authority and timing metadata |
| `SRV` | Service location with port, priority, and weight |
| `CAA` | Which certificate authorities may issue certificates |

A DNS response can contain several addresses for redundancy or distribution.
DNS does not guarantee that clients use them uniformly or immediately react to
changes.

### Caching, TTL, and Negative Answers

TTL controls how long a resolver may cache a record. Low TTLs allow faster
changes but increase query load and do not guarantee instant propagation.
Resolvers, applications, and intermediaries may all cache.

Negative responses, such as a name not existing (`NXDOMAIN`), can also be
cached. Creating a record immediately after a failed lookup may still appear
broken until negative cache entries expire.

### DNS Transport and Reliability

Traditional DNS commonly uses UDP for ordinary queries and TCP for larger
responses, retries after truncation, and zone transfers. Modern encrypted forms
include DNS over TLS and DNS over HTTPS.

DNS failures include:

* Timeout or unreachable resolver
* `NXDOMAIN` for a nonexistent name
* `SERVFAIL` when resolution cannot be completed
* Stale or inconsistent cached answers
* Missing records or delegation errors
* Responses too large for a path or blocked TCP fallback
* Split-horizon answers that differ inside and outside a network

### Service Discovery

Dynamic systems need to find healthy service instances. Common approaches are:

* DNS records managed by an orchestrator
* A service registry queried by clients or proxies
* Client-side discovery and load balancing
* Server-side discovery through a load balancer
* Service-mesh sidecars or node proxies

Discovery answers "where are instances?" Health checking answers "which
instances should currently receive traffic?" They interact but are not the same
problem.

## 7. HTTP and Application Protocols

HTTP is a stateless request-response application protocol. "Stateless" means
the protocol does not require a server to retain conversational state between
requests. Applications can still maintain sessions through cookies, tokens, or
server-side data.

### URLs

A URL can contain:

```text
https://user@example.com:8443/orders/42?view=full#items
|scheme|     host       |port| path    | query   |fragment
```

The fragment is interpreted by the client and is not normally sent in an HTTP
request. The host identifies the authority; DNS then resolves the hostname.

### HTTP Message Shape

A simplified HTTP/1.1 request:

```http
GET /orders/42?view=full HTTP/1.1
Host: api.example.com
Accept: application/json
Authorization: Bearer token

```

A response:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 27
Cache-Control: private, max-age=60

{"id":42,"status":"ready"}
```

Headers carry metadata. The body carries a representation or command payload.
HTTP/2 and HTTP/3 encode messages differently on the wire but preserve the
request, response, method, status, and header semantics.

### Methods and Semantics

| Method | Typical Meaning | Safe | Idempotent |
|--------|-----------------|------|------------|
| `GET` | Retrieve a representation | Yes | Yes |
| `HEAD` | Retrieve headers without response body | Yes | Yes |
| `POST` | Submit or create according to resource semantics | No | Not inherently |
| `PUT` | Replace resource at a known URI | No | Yes |
| `PATCH` | Partially modify a resource | No | Not inherently |
| `DELETE` | Remove a resource | No | Yes by intended effect |
| `OPTIONS` | Describe communication options | Yes | Yes |

Safe means the client does not request a state change. Idempotent means repeated
identical requests have the same intended server effect as one request. A
response can differ between repeats, and logging or metrics can still change.

Retries should follow operation semantics, not method names alone. A payment
`POST` can be made safely retryable with an idempotency key and durable server
deduplication.

### Status Codes

| Class | Meaning | Examples |
|-------|---------|----------|
| `1xx` | Informational | `100 Continue` |
| `2xx` | Successful | `200 OK`, `201 Created`, `204 No Content` |
| `3xx` | Redirection or cache validation | `301`, `302`, `304`, `307`, `308` |
| `4xx` | Client-side request problem | `400`, `401`, `403`, `404`, `409`, `429` |
| `5xx` | Server or upstream failure | `500`, `502`, `503`, `504` |

Distinctions interviewers often ask about:

* `401 Unauthorized` usually means missing or invalid authentication
* `403 Forbidden` means identity is known but access is denied
* `502 Bad Gateway` means a proxy received an invalid or failed upstream response
* `503 Service Unavailable` indicates temporary inability to serve
* `504 Gateway Timeout` means a gateway timed out waiting for an upstream

### Headers, Cookies, and Sessions

HTTP cookies are name-value data stored by a user agent and sent according to
domain, path, lifetime, security, and same-site rules.

Important attributes include:

* `Secure` restricts transmission to secure contexts
* `HttpOnly` prevents JavaScript access, reducing token theft through XSS
* `SameSite` controls cross-site sending and helps mitigate CSRF
* `Expires` or `Max-Age` controls persistence

Cookies often carry an opaque session identifier. Storing sensitive mutable
session state only inside an unsigned client cookie permits tampering. Signed or
encrypted tokens have different revocation and size trade-offs.

### HTTP Caching

Caching reduces latency, bandwidth, and origin load. Key directives include:

* `Cache-Control: max-age=N` defines freshness lifetime
* `public` permits shared caches; `private` restricts shared caching
* `no-store` requests no storage
* `no-cache` permits storage but requires revalidation before reuse
* `ETag` provides an opaque validator
* `Last-Modified` provides a time validator
* `Vary` identifies request headers that affect the representation

Conditional requests use `If-None-Match` or `If-Modified-Since`. A `304 Not
Modified` response reuses the cached body.

Cache correctness depends on the key. Omitting authentication, language, content
encoding, or other representation dimensions can leak or serve incorrect data.

### HTTP Versions

| Version | Transport | Main Characteristics |
|---------|-----------|----------------------|
| HTTP/1.0 | TCP | Commonly one request per connection |
| HTTP/1.1 | TCP | Persistent connections, chunking, pipelining defined but rarely used |
| HTTP/2 | TCP | Binary framing, multiplexed streams, header compression |
| HTTP/3 | QUIC over UDP | Multiplexed streams without cross-stream TCP blocking |

HTTP/1.1 often uses several parallel connections because one connection cannot
practically multiplex arbitrary responses. HTTP/2 multiplexes streams over one
TCP connection, although TCP packet loss can delay every stream. HTTP/3 uses
QUIC streams with independent ordered delivery.

### Persistent Connections and Connection Pools

Reusing a connection avoids repeated TCP and TLS setup. A client pool limits
concurrent connections and amortizes handshakes.

Pools require limits and timeouts:

* Maximum total and per-host connections
* Acquisition timeout
* Idle timeout
* Maximum connection lifetime
* Validation or eviction of stale connections

Pool exhaustion often appears as application latency before any network call is
made because callers wait for a connection slot.

### REST, RPC, and gRPC

REST is an architectural style centered on resources, representations, uniform
interfaces, and stateless interactions. JSON over HTTP is common but not the
definition of REST.

RPC models calls to remote procedures. gRPC commonly uses Protocol Buffers over
HTTP/2 and supports unary and streaming interactions.

| Style | Strength | Trade-off |
|-------|----------|-----------|
| REST/JSON | Broad interoperability and debuggability | Larger payloads, weaker generated contracts |
| gRPC/Protobuf | Typed contracts, compact encoding, streaming | Browser and manual-debugging complexity |

A remote call is not a local function call. It has latency, partial failure,
timeouts, retries, serialization, compatibility, and duplicate-execution risks.

### WebSocket, Server-Sent Events, and Long Polling

| Mechanism | Direction | Good Fit |
|-----------|-----------|----------|
| WebSocket | Full duplex | Chat, collaborative editing, games |
| Server-Sent Events | Server to client | Notifications and live feeds |
| Long polling | Primarily server to client via repeated HTTP | Compatibility with simpler infrastructure |

WebSocket starts with an HTTP upgrade and then uses framed messages over the
connection. Long-lived connections require heartbeat, reconnection, load
balancer timeout, backpressure, and per-instance connection-state planning.

### Content Encoding and Serialization

Serialization turns application data into bytes. Text formats such as JSON are
readable and flexible. Binary formats such as Protocol Buffers can be smaller
and faster with explicit schemas.

Compression reduces bytes but consumes CPU and can increase latency for small
messages. Compressing secrets together with attacker-controlled text can also
create side channels. Choose compression based on payload size, content type,
CPU budget, and threat model.

## 8. TLS and Secure Communication

Transport Layer Security protects application data in transit. It provides:

* Confidentiality through encryption
* Integrity through authenticated encryption
* Server authentication through certificates
* Optional client authentication

TLS does not prove that an application is trustworthy, prevent endpoint
compromise, or authorize a user by itself.

### Certificates and Trust

An X.509 certificate binds a public key to names and other identity information.
It is signed by an issuer. A client validates a chain from the leaf certificate
through intermediate certificate authorities to a trusted root.

Validation includes:

* Signature chain to a trusted root
* Current time within certificate validity
* Requested hostname in the Subject Alternative Name extension
* Appropriate key usage and constraints
* Revocation policy where applicable

Encrypting traffic while skipping certificate and hostname verification is
vulnerable to man-in-the-middle attacks.

### Simplified TLS 1.3 Handshake

```text
Client                                              Server
  | -- ClientHello: versions, key share, SNI, ALPN --> |
  | <-- ServerHello: selected version and key share -- |
  | <-- encrypted certificate and proof -------------- |
  | -- validates identity, derives session keys ------- |
  | -- Finished --------------------------------------> |
  | <---------------- Finished -------------------------|
  | <========= encrypted application data =============>|
```

Ephemeral Diffie-Hellman key exchange allows both sides to derive the same
session secret without sending it directly. Forward secrecy means later theft
of the certificate private key does not reveal previously recorded sessions
that used ephemeral keys.

### SNI and ALPN

Server Name Indication (SNI) tells a server which hostname the client wants,
allowing many certificates and sites on one IP address. In conventional TLS,
SNI may be visible to network observers unless newer encrypted mechanisms are
used.

Application-Layer Protocol Negotiation (ALPN) selects a protocol such as
HTTP/1.1 or HTTP/2 during the TLS handshake.

### TLS Termination and End-to-End Encryption

A load balancer can terminate client TLS, inspect HTTP, and create a separate
connection to the backend.

```text
Client == TLS A ==> load balancer == TLS B ==> backend
```

This protects both network legs when TLS is used on both, but the load balancer
can see plaintext between termination contexts. "End to end" must identify the
actual cryptographic endpoints.

Mutual TLS (mTLS) requires both peers to present certificates. It can establish
service identity but still needs authorization policy, certificate rotation,
and revocation handling.

### TLS Operational Failures

Common causes include:

* Expired or not-yet-valid certificate
* Hostname mismatch
* Missing intermediate certificate
* Untrusted private certificate authority
* Incompatible versions or cipher suites
* SNI or ALPN mismatch
* Clock skew
* Proxy interception
* Certificate rotation not propagated to every endpoint

## 9. Proxies, Load Balancers, and CDNs

Intermediaries shape how clients reach services.

### Forward and Reverse Proxies

A forward proxy acts on behalf of clients:

```text
clients -> forward proxy -> Internet services
```

It can enforce egress policy, filter content, provide privacy boundaries, or
cache responses.

A reverse proxy acts on behalf of servers:

```text
clients -> reverse proxy -> backend services
```

It can terminate TLS, route requests, authenticate, compress, cache, limit
traffic, and hide backend topology.

### Layer-4 and Layer-7 Load Balancing

| Property | L4 Load Balancer | L7 Load Balancer |
|----------|------------------|------------------|
| Understands | TCP/UDP endpoints | HTTP or application semantics |
| Routes by | IP, port, connection | Host, path, header, cookie, method |
| Overhead | Usually lower | Usually higher |
| Features | Connection distribution | Rewrites, auth, routing, caching |

Algorithms include round robin, weighted round robin, least connections, least
latency, random choice, hashing, and consistent hashing. The right algorithm
depends on task duration, instance capacity, locality, and state.

### Health Checks

Liveness asks whether a process should be restarted. Readiness asks whether it
should receive traffic. A process can be alive but unready because startup is
incomplete or a critical resource is unavailable.

Health checks must be cheap and meaningful. A shallow check can route traffic to
a broken instance. A check that synchronously queries every dependency can cause
cascading failure and remove the whole fleet during a shared dependency outage.

### Session Affinity

Sticky sessions route a client repeatedly to one backend, often by cookie or
source hashing. They can simplify in-memory session state but create imbalance,
complicate failure recovery, and weaken elasticity. Externalizing durable state
usually gives more flexible routing.

### Consistent Hashing

Consistent hashing assigns keys and servers around a logical ring. Adding or
removing a server moves a fraction of keys rather than nearly all keys. Virtual
nodes improve balance.

It is useful for caches and sharded services, but replication, hot keys, uneven
capacity, and rebalancing still need explicit design.

### CDNs

A content delivery network serves cacheable data from edge locations near
clients.

```text
Client -> DNS/anycast -> edge cache -> origin on cache miss
```

Benefits include lower latency, reduced origin bandwidth, traffic absorption,
and global reach. Challenges include invalidation, cache-key correctness, stale
content, personalized data, origin shielding, and consistency across edges.

### Firewalls and Network Policy

A stateless packet filter evaluates each packet independently. A stateful
firewall tracks flows and commonly permits return traffic for established
connections. Application firewalls inspect higher-level content.

Security groups, access control lists, host firewalls, Kubernetes network
policies, and service-mesh authorization operate at different points. Debugging
requires identifying every policy layer on the path.

### Tunnels and VPNs

Tunneling encapsulates one protocol inside another. A VPN commonly creates an
encrypted tunnel between an endpoint and a gateway or between networks.

Encapsulation adds headers and reduces effective MTU. Incorrect MTU handling is
a common reason a tunnel accepts small packets but fails on larger transfers.

## 10. Sockets and Network Programming

A socket is an operating-system communication endpoint. The main socket types
are stream sockets (`SOCK_STREAM`, usually TCP) and datagram sockets
(`SOCK_DGRAM`, usually UDP).

### TCP Server Lifecycle

```text
socket -> bind -> listen -> accept -> recv/send -> close
```

* `socket()` creates an endpoint
* `bind()` assigns a local address and port
* `listen()` marks a TCP socket as passive and establishes a pending queue
* `accept()` returns a new connected socket while the listening socket remains
  available for more clients
* `recv()` and `send()` transfer stream bytes
* `close()` releases the descriptor and initiates connection closure

### Minimal Length-Prefixed TCP Server

The example handles TCP framing correctly. It is intentionally single-client-at-
a-time so the transport mechanics remain visible.

```python
import socket
import struct


def receive_exactly(sock: socket.socket, byte_count: int) -> bytes:
    chunks = []
    remaining = byte_count

    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("peer closed before the message completed")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def receive_message(sock: socket.socket) -> bytes:
    header = receive_exactly(sock, 4)
    (message_length,) = struct.unpack("!I", header)
    if message_length > 1_000_000:
        raise ValueError("message exceeds size limit")
    return receive_exactly(sock, message_length)


def send_message(sock: socket.socket, message: bytes) -> None:
    header = struct.pack("!I", len(message))
    sock.sendall(header + message)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 9000))
    server.listen()

    connection, address = server.accept()
    with connection:
        request = receive_message(connection)
        send_message(connection, request.upper())
```

Network byte order is big-endian. The `!I` format encodes an unsigned 32-bit
length consistently across machine architectures.

### Matching TCP Client

```python
import socket
import struct


def receive_exactly(sock: socket.socket, byte_count: int) -> bytes:
    result = bytearray()
    while len(result) < byte_count:
        chunk = sock.recv(byte_count - len(result))
        if not chunk:
            raise ConnectionError("peer closed unexpectedly")
        result.extend(chunk)
    return bytes(result)


with socket.create_connection(("127.0.0.1", 9000), timeout=3) as sock:
    payload = b"hello network"
    sock.sendall(struct.pack("!I", len(payload)) + payload)

    (response_length,) = struct.unpack("!I", receive_exactly(sock, 4))
    response = receive_exactly(sock, response_length)
    print(response.decode("utf-8"))
```

### Partial Reads and Writes

`recv(n)` returns up to `n` bytes, not necessarily exactly `n`. It can return
less because only part of the stream is currently available. An empty result
means orderly end-of-stream after pending data is consumed.

`send(data)` can write fewer bytes than requested. `sendall(data)` loops until
all bytes are handed to the socket layer or an error occurs. Successful local
send completion does not prove the remote application processed the bytes.

### Datagram Programming

UDP uses `sendto()` and `recvfrom()` without a required handshake:

```python
import socket


with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
    server.bind(("127.0.0.1", 9001))
    data, client_address = server.recvfrom(65_507)
    server.sendto(data.upper(), client_address)
```

Each receive obtains one datagram, up to the supplied buffer size. If the buffer
is too small, the remainder may be discarded depending on the API. Large UDP
datagrams are more likely to fragment and be lost; applications commonly stay
within a conservative path MTU.

### Blocking, Nonblocking, and Asynchronous I/O

With blocking I/O, a call waits until it can make progress or fails. A thread-
per-connection server is conceptually straightforward but incurs thread stacks,
scheduling, and synchronization costs.

Nonblocking sockets return immediately when an operation would wait. Readiness
APIs such as `select`, `poll`, `epoll`, `kqueue`, and IOCP let a program react to
many sockets with fewer threads. Python's `selectors` and `asyncio` provide
higher-level abstractions.

Readiness means an operation is likely to make progress, not that a complete
application message is available. Code still needs incremental parsing, output
buffering, error handling, and backpressure.

### Backlog and Queueing

A TCP server has queues for connection establishment and accepted connections
awaiting the application. Exact implementation details differ by OS. If the
application accepts too slowly or queues fill, clients may experience refused,
dropped, or timed-out connections.

The `listen(backlog)` value is a request interpreted and capped by the OS. It is
not the maximum number of established client connections the server can hold.

### Timeouts and Deadlines

Useful timeout categories include:

* DNS resolution timeout
* Connection timeout
* TLS handshake timeout
* Request write timeout
* Response-header timeout
* Idle read timeout
* Whole-operation deadline
* Connection-pool acquisition timeout

A deadline is an absolute budget for the overall operation. Passing the full
timeout independently to every retry or subcall can multiply latency far beyond
the caller's intended budget. Propagate remaining time.

### Resource Limits

Network services are constrained by:

* File descriptor or handle limits
* Ephemeral ports
* Socket memory
* Connection tracking and NAT tables
* Worker threads or event-loop capacity
* Accept and application queues
* Downstream connection pools
* CPU for encryption and serialization

Capacity planning must follow the entire request path, not only the listening
server.

## 11. Performance and Capacity

Networking performance combines propagation, transmission, queueing, protocol,
and application costs.

### Latency Components

Approximate one-way latency is:

$$
L = L_{propagation} + L_{transmission} + L_{queueing} + L_{processing}
$$

* Propagation delay is signal travel time through the medium
* Transmission delay is packet size divided by link rate
* Queueing delay occurs while waiting behind other traffic
* Processing delay includes protocol, proxy, encryption, and application work

For a packet of $S$ bits on a link of rate $R$ bits per second:

$$
L_{transmission} = \frac{S}{R}
$$

A 1 MiB payload takes at least about 84 ms to serialize onto a 100 Mbps link,
ignoring headers and all other delays.

### Bandwidth, Throughput, and Goodput

Bandwidth is capacity. Throughput is observed transfer rate. Goodput excludes
headers, retransmissions, and unusable data.

A high-bandwidth path can still have poor latency. A low-latency path can still
have low bandwidth. Optimize the metric tied to the workload.

### Bandwidth-Delay Product

The bandwidth-delay product is the amount of data needed in flight to fully use
a path:

$$
BDP = bandwidth \times RTT
$$

For 1 Gbps and 100 ms RTT:

$$
BDP = 1,000,000,000\frac{bits}{s} \times 0.1s
    = 100,000,000\ bits \approx 12.5\ MB
$$

If transport windows permit only 1 MB in flight, the connection cannot fill that
path regardless of the nominal 1 Gbps link rate.

### Round Trips and Protocol Setup

Sequential round trips dominate short operations over distant networks. A cold
HTTPS request may require DNS work, a TCP handshake, a TLS handshake, and the
HTTP request-response. Caching, connection reuse, TLS resumption, multiplexing,
and protocols with fewer setup round trips reduce this cost.

### Queueing and Little's Law

For a stable system:

$$
L = \lambda W
$$

where $L$ is average items in the system, $\lambda$ is average arrival rate, and
$W$ is average time in the system.

At 2,000 concurrent requests and 1,000 requests per second:

$$
W = \frac{L}{\lambda} = \frac{2000}{1000} = 2\ seconds
$$

Queue growth is not free capacity. It converts overload into latency and memory
use. Bounded queues, admission control, and load shedding keep failure explicit.

### Tail Latency

Average latency hides slow outliers. Services track percentiles such as p50,
p95, p99, and p99.9. A request that fans out to many dependencies becomes more
likely to encounter at least one slow response.

If independent calls each meet a latency target with probability $p$, all $n$
meet it with probability:

$$
P(all\ fast) = p^n
$$

If each of 100 calls is fast 99% of the time, only about $0.99^{100} \approx
36.6\%$ of aggregate requests see every call fast.

### Throughput Optimization Checklist

* Reduce unnecessary round trips
* Reuse connections
* Batch work when latency permits
* Compress sufficiently large compressible payloads
* Avoid tiny writes
* Use streaming to limit buffering and time to first byte
* Apply backpressure before queues grow without bound
* Place data and computation closer to users
* Measure packet loss, retransmissions, saturation, and downstream limits

## 12. Reliability and Distributed-System Semantics

Networks introduce partial failure. A caller can be healthy while the server,
an intermediary, or one direction of the path is unhealthy.

### The Ambiguous Outcome Problem

After a timeout, a client often cannot know which event occurred:

```text
1. Request never reached server
2. Request reached server but was not processed
3. Server processed request but response was lost
4. Response is merely delayed and may still arrive
```

Therefore, transport success and application success are separate. TCP ACKs
confirm receipt by a peer's TCP stack, not database commit or business success.

### Timeouts

Every remote dependency needs a finite budget. A timeout that is too short causes
false failures and retries. One that is too long ties up resources and delays
recovery.

Choose timeouts from latency distributions, caller deadlines, retry policy, and
the cost of holding resources. Distinguish queueing time from network and server
time when diagnosing.

### Retries

Retries can mask transient failure but also amplify overload. A sound policy has:

* A retryable error classification
* Idempotent or deduplicated operations
* Exponential backoff
* Random jitter to avoid synchronized retry waves
* A maximum attempt count and total deadline
* A retry budget limiting aggregate amplification

Retry at one well-chosen layer. Independent retries at the client, proxy, and
service can multiply attempts.

### Delivery Semantics

| Semantic | Meaning |
|----------|---------|
| At-most-once | Operation is attempted zero or one time; loss is possible |
| At-least-once | Operation is retried until accepted; duplicates are possible |
| Exactly-once effect | Duplicates are prevented or made harmless at the state boundary |

Exactly-once delivery across arbitrary failures is not obtained by setting a
flag on TCP. Systems commonly implement an exactly-once business effect with an
idempotency key, transactional state, and durable result recording.

### Backpressure and Load Shedding

Backpressure tells producers to slow down when consumers cannot keep up. It can
appear as bounded queues, blocked writes, flow-control windows, concurrency
limits, or explicit rejection.

Load shedding rejects work before a saturated service collapses. Returning a
fast `429` or `503` can be healthier than accepting requests that will time out
after consuming scarce resources.

### Circuit Breakers

A circuit breaker stops sending normal traffic to a dependency after sufficient
failures, allows limited probes later, and closes after recovery.

It protects resources and shortens failures but does not repair the dependency.
Thresholds, fallback behavior, probe rate, and shared-state granularity determine
whether it helps or causes unnecessary outages.

### Connection Failure Modes

| Symptom | Possible Cause |
|---------|----------------|
| Connection refused | No listener, active firewall rejection, exhausted listener |
| Connection timeout | Dropped packets, routing failure, silent firewall, server overload |
| Connection reset | Peer or intermediary aborted the connection |
| Read timeout | Slow server, lost response, path issue, insufficient timeout |
| Broken pipe | Local write after peer closure became known |
| DNS failure | Resolver, delegation, record, or cache problem |
| TLS failure | Trust, hostname, version, certificate, SNI, or clock issue |
| Intermittent failure | Load-balanced bad instance, loss, race, stale connection |

## 13. Network Security Fundamentals

Security requires authentication, authorization, confidentiality, integrity,
availability, and careful trust boundaries.

### Common Threats

| Threat | Description | Typical Defense |
|--------|-------------|-----------------|
| Eavesdropping | Passive observation of traffic | TLS or another authenticated encryption layer |
| Tampering | Modification in transit | Authenticated encryption and signatures |
| Spoofing | Forged identity or source information | Authentication; do not trust source IP alone |
| Man in the middle | Interception between peers | Certificate and hostname validation |
| Replay | Reuse of a valid old message | Nonces, timestamps, sequence numbers, server state |
| SYN flood | Exhaustion through connection attempts | SYN cookies, rate limits, filtering, capacity |
| DDoS | Distributed resource exhaustion | Anycast, CDN, filtering, rate limits, load shedding |
| DNS poisoning | False cached name records | DNSSEC validation, secure resolvers, hardening |
| ARP spoofing | False local IP-to-MAC claims | Network controls, encryption, inspection |
| Port scanning | Discovery of exposed services | Minimize exposure, firewalling, monitoring |

### Authentication vs Authorization

Authentication answers "who is this?" Authorization answers "what may this
identity do?" TLS server authentication does not authorize a user to read an
account. mTLS service identity does not automatically define which RPC methods
the service may call.

### Defense in Depth

A production path can enforce controls at several layers:

```text
Internet edge -> DDoS protection -> firewall -> load balancer/WAF
              -> service identity -> application authorization -> data policy
```

Each layer has blind spots. Network location alone is a weak identity in dynamic
cloud environments. Zero-trust designs authenticate and authorize requests
without assuming an internal network is inherently safe.

### Input and Protocol Safety

Network parsers process untrusted bytes. Defenses include:

* Maximum header, message, and decompressed sizes
* Parsing deadlines and idle timeouts
* Strict length and integer-overflow validation
* Bounded nesting and recursion
* Schema validation
* Safe handling of malformed encodings
* Backpressure on request bodies and responses

Length-prefixed protocols must reject unreasonable lengths before allocating
memory. Compression limits must prevent small inputs from expanding without
bound.

### CORS and CSRF

Cross-Origin Resource Sharing (CORS) is a browser policy controlling whether
scripts can read responses from another origin. It is not server authentication
and does not prevent non-browser clients from sending requests.

Cross-Site Request Forgery (CSRF) tricks a browser into sending an authenticated
request. Defenses include SameSite cookies, anti-CSRF tokens, origin checks, and
avoiding state changes through safe methods.

## 14. Debugging and Observability

Debug one layer at a time. "The network is down" is too broad to guide action.

### Layered Troubleshooting Workflow

1. Confirm the application error, timestamp, destination, and timeout phase.
2. Resolve the hostname and inspect every returned address.
3. Check local interface configuration and routing.
4. Test basic reachability when ICMP is available.
5. Test the destination transport port.
6. Inspect TCP connection state and retransmission evidence.
7. Validate TLS with the intended hostname and trust store.
8. Send the application request with verbose timing.
9. Compare successful and failed instances, networks, and paths.
10. Correlate client, proxy, server, and dependency telemetry.

### Useful Commands

| Goal | Windows | Linux/macOS |
|------|---------|-------------|
| Interface configuration | `ipconfig /all` | `ip addr`, `ifconfig` |
| Routing table | `route print` | `ip route` |
| DNS lookup | `Resolve-DnsName`, `nslookup` | `dig`, `host`, `nslookup` |
| Reachability | `ping` | `ping` |
| Path discovery | `tracert` | `traceroute`, `tracepath` |
| Test TCP port | `Test-NetConnection host -Port 443` | `nc -vz host 443` |
| HTTP/TLS request | `curl.exe -v https://host` | `curl -v https://host` |
| Socket state | `Get-NetTCPConnection`, `netstat -ano` | `ss -tanp`, `netstat` |
| Neighbor cache | `arp -a`, `Get-NetNeighbor` | `ip neigh` |
| Packet capture | Wireshark, `pktmon` | Wireshark, `tcpdump` |

Use `curl.exe` explicitly in Windows PowerShell environments where `curl` may be
an alias in older versions.

### Reading Common Evidence

`ping` answers whether ICMP echo succeeds, not whether HTTPS works. A successful
TCP connection proves a listener or intermediary accepted the handshake, not
that TLS or the application is healthy.

`traceroute` identifies responding hops, but missing hops can be filtering rather
than failure. `nslookup` and `dig` reveal DNS answers but may not use the exact
same resolver path or cache as the application.

A packet capture can reveal:

* SYN retransmissions with no SYN-ACK
* Immediate RST responses
* Repeated TCP retransmissions or duplicate ACKs
* Zero-window flow control
* TLS alerts
* DNS timeouts or unexpected answers
* One side sending FIN or RST
* ICMP fragmentation-needed or unreachable messages

Capture only where authorized and protect payloads and credentials contained in
traces.

### Essential Metrics

* Request rate, error rate, and duration by operation
* DNS, connect, TLS, time-to-first-byte, and body-transfer timings
* Open, active, idle, and pending connections
* Connection-pool wait time and utilization
* TCP retransmissions and resets
* Packet loss and RTT
* Queue depth and oldest-item age
* Bytes sent and received
* Load balancer response codes and backend health
* Timeout and retry counts by reason

### Logs and Traces

Logs should include a correlation ID, destination, operation, timeout phase, and
error category without exposing secrets. Distributed traces show where time is
spent across DNS, connection acquisition, proxies, services, and dependencies.

Do not record authorization headers, session cookies, private keys, or full
sensitive payloads. Observability is part of the security boundary.

## 15. End-to-End Packet Walkthroughs

These walkthroughs connect the layers into one model.

### Two Hosts on the Same Subnet

Suppose `192.168.1.10/24` sends to `192.168.1.20`:

1. The sender applies `/24` and determines the destination is local.
2. It checks its ARP cache for `192.168.1.20`.
3. If missing, it broadcasts an ARP request.
4. The destination replies with its MAC address.
5. The sender builds an IP packet addressed to `192.168.1.20`.
6. It wraps the packet in an Ethernet frame addressed to the destination MAC.
7. The switch forwards the frame to the learned destination port.
8. The receiver validates and decapsulates the frame and delivers the packet up
   its stack.

No router is required.

### Two Hosts on Different Subnets

Suppose `192.168.1.10/24` sends to `10.0.0.20` through gateway
`192.168.1.1`:

1. The sender determines `10.0.0.20` is not in its local `/24`.
2. Its routing table selects the default gateway.
3. It resolves the gateway's MAC address, not the remote host's MAC.
4. It creates an IP packet with destination `10.0.0.20`.
5. It creates an Ethernet frame with destination MAC equal to the gateway MAC.
6. The router removes the frame, decrements TTL, selects the next route, and
   creates a new frame for the next link.
7. Routing continues until the final router resolves the destination on its
   local link.

The destination IP remains `10.0.0.20`; link-layer addresses change at each hop.

### Entering a URL in a Browser

For `https://www.example.com/products?id=7`:

1. The browser parses the URL into scheme, host, port, path, and query.
2. It checks policies and caches, then resolves `www.example.com` through DNS.
3. The OS chooses a route to one returned IP.
4. On Ethernet, the host resolves the next-hop MAC with ARP or IPv6 Neighbor
   Discovery.
5. For HTTP/1.1 or HTTP/2, the browser opens TCP port 443 with a three-way
   handshake. For HTTP/3, it establishes QUIC over UDP.
6. TLS negotiates keys and protocol, and the browser validates the certificate
   for `www.example.com`.
7. The browser sends an HTTP request, including the host, headers, and applicable
   cookies.
8. An edge, CDN, or load balancer may terminate TLS and serve from cache or route
   to a backend.
9. The server authenticates, authorizes, processes the request, and returns an
   HTTP response.
10. The browser validates framing, decompresses and decodes content, applies
    cache and cookie rules, and renders or executes resources.
11. Connections may remain pooled for later requests.

Every step can fail independently. A strong interview answer names caches,
round trips, security validation, intermediaries, and failure modes without
pretending every deployment uses exactly the same path.

### Sending Through NAT

When private host `10.0.0.5:51000` connects to `198.51.100.20:443`:

1. The host routes the packet to its NAT gateway.
2. The gateway rewrites source `10.0.0.5:51000` to a public endpoint such as
   `203.0.113.8:62001`.
3. It records the mapping and updates checksums.
4. The server sees the public translated endpoint.
5. The reply returns to `203.0.113.8:62001`.
6. The gateway looks up state, restores destination `10.0.0.5:51000`, and
   forwards internally.

If translation state expires during a long-idle flow, later packets may fail
even though both applications still believe the connection exists.

## 16. Google Interview Questions

Google interviews reward a correct model, explicit assumptions, and the ability
to reason from symptoms. Start at the relevant layer and connect it to the
application consequence.

### Fundamental Questions

#### What happens when you type a URL into a browser

Cover URL parsing, browser caches, DNS, route and next-hop resolution, transport
setup, TLS, HTTP, proxies or CDN, backend processing, response decoding, and
connection reuse. Mention HTTP/3 as an alternative without derailing the main
flow.

#### Why do we need both MAC and IP addresses

IP addresses provide hierarchical routing across networks. MAC addresses deliver
frames on a local link. Routers connect those scopes and replace link headers at
each hop.

#### What is the difference between a switch and a router

A switch primarily forwards frames within a broadcast domain using MAC learning.
A router forwards packets between IP networks using longest-prefix matching and
separates broadcast domains.

#### Why does TCP need a three-way handshake

Both peers must synchronize initial sequence spaces and prove bidirectional
reachability. Two messages would not let the initiator know that its response to
the peer's sequence number was received.

#### Is TCP message-oriented

No. TCP is an ordered byte stream. Applications must implement framing and loop
over partial reads and writes.

#### Does a successful TCP send mean the server processed the request

No. It can mean only that the local stack accepted bytes. Even acknowledgments
confirm transport receipt, not application completion or durable commit.

#### Flow control vs congestion control

Flow control prevents overwhelming the receiver and uses the receive window.
Congestion control prevents overwhelming the network and uses path feedback to
adjust the congestion window.

#### Why can UDP be useful if it is unreliable

It avoids mandatory connection and ordering semantics, preserves datagram
boundaries, supports multicast, and lets applications choose timing and
reliability behavior. QUIC demonstrates that sophisticated reliable transport
can be built over UDP.

#### What is `TIME_WAIT`

The active TCP closer retains state so delayed old segments cannot collide with
a new connection incarnation and the final ACK can be retransmitted if needed.

#### Why can HTTP/2 still suffer head-of-line blocking

Its streams share one ordered TCP byte stream. Loss of an earlier TCP segment
can delay delivery for every HTTP/2 stream on that connection.

#### How does DNS resolution work

Explain stub and recursive resolvers, root, TLD, authoritative servers, caching,
TTL, and record types. Distinguish recursive queries from iterative referrals.

#### What does a `/24` mean

The first 24 IPv4 bits form the network prefix, leaving 8 address bits and 256
total addresses. Explain conventional network and broadcast reservations rather
than blindly saying 254 in every context.

#### How does a router choose between matching routes

It uses the longest matching prefix, then applies route preference and metric
rules when routes have comparable specificity.

#### What is the difference between `401` and `403`

`401` normally indicates missing or invalid authentication. `403` indicates the
request is understood but the identity is not permitted to perform it.

#### What is the difference between `502`, `503`, and `504`

`502` means a gateway received a failed or invalid upstream response. `503`
means the service is temporarily unavailable. `504` means a gateway timed out
waiting for an upstream.

#### How does TLS authenticate a server

The server proves possession of the private key associated with a certificate.
The client validates the signature chain, trust root, hostname, validity period,
constraints, and applicable policy.

#### Reverse proxy vs load balancer

A reverse proxy represents servers and provides application mediation. Load
balancing is one function it may perform. An L4 load balancer need not act as an
HTTP reverse proxy.

### Scenario Questions

#### Ping succeeds but HTTPS fails

Possible causes include no listener on 443, firewall policy specific to TCP,
TLS certificate or protocol failure, proxy routing, virtual-host mismatch, or
application failure. Test DNS, TCP connection, TLS, and HTTP separately.

#### The service works by IP but not hostname

Investigate DNS records, search suffixes, resolver caches, split-horizon DNS,
SNI, certificate hostname validation, and HTTP host routing. Replacing the host
with an IP changes more than DNS.

#### Small responses work but large responses hang

Suspect path MTU discovery failure, blocked ICMP, tunnel overhead, packet loss,
flow-control issues, proxy limits, or application buffering. A path MTU black
hole is a classic explanation.

#### One backend fails intermittently behind a load balancer

Break down metrics and logs by backend instance, zone, resolved address, and
connection reuse. Verify health-check depth, stale pooled connections, readiness,
configuration drift, and retry masking.

#### Latency rises while CPU remains low

Inspect queueing, connection-pool waits, lock contention, DNS, packet loss,
retransmissions, downstream saturation, and long timeouts. Low CPU often means
workers are waiting rather than that capacity is available.

#### Clients retry and duplicate payments occur

The server may commit before the response is lost. Use a client-generated
idempotency key, a durable uniqueness constraint, transactional result storage,
and return the recorded result for duplicates.

#### A server supports 100,000 mostly idle connections

Prefer event-driven I/O or another lightweight concurrency model, tune file
descriptor and socket limits, bound per-connection memory, implement idle
timeouts and heartbeats, account for load-balancer and NAT timeouts, and plan
reconnection waves.

### Coding Questions

Be prepared to implement or discuss:

* A length-prefixed protocol with partial reads
* A concurrent TCP echo or chat server
* URL parsing and normalization
* IPv4/CIDR membership
* An LRU DNS cache with TTL
* A rate limiter at an API gateway
* Consistent hashing for backend selection
* A retry policy with deadline, backoff, and jitter
* A crawler with URL deduplication and host limits
* A basic HTTP parser with strict size limits

### CIDR Membership Example

Python's standard library avoids error-prone manual bit manipulation:

```python
from ipaddress import ip_address, ip_network


network = ip_network("192.168.10.0/24")
assert ip_address("192.168.10.77") in network
assert ip_address("192.168.11.1") not in network
```

If asked to implement it manually, convert both IPv4 addresses to 32-bit
integers and compare masked prefixes:

$$
(address \mathbin{\&} mask) = (network \mathbin{\&} mask)
$$

### How to Structure an Interview Answer

1. Clarify endpoints, scale, protocol, and failure assumptions.
2. Identify the layer that owns the requested guarantee.
3. Walk the normal path before edge cases.
4. Separate transport delivery from application semantics.
5. State timeout, retry, idempotency, and backpressure behavior.
6. Discuss security and observability.
7. Quantify capacity with connections, bytes, rates, RTT, and percentiles.
8. Name trade-offs and how measurements would validate the choice.

## 17. Quick Reference

### Layer Summary

```text
Application:  HTTP, DNS, gRPC, WebSocket
Security:     TLS
Transport:    TCP, UDP, QUIC
Internet:     IPv4, IPv6, ICMP, routing
Link:         Ethernet, Wi-Fi, ARP/NDP, switching
Physical:     copper, fiber, radio
```

### Addressing Summary

```text
Domain name -> resolved by DNS -> IP address
IP address  -> routed between networks
MAC address -> delivers frame to next hop on local link
Port        -> selects transport endpoint on a host
Socket      -> application handle for the endpoint
```

### Reliability Summary

```text
Ethernet checksum: detects link corruption
IP:                best-effort packet delivery
UDP:               ports plus datagram boundaries
TCP:               reliable ordered byte stream
TLS:               encrypted, integrity-protected channel and peer identity
HTTP:              application request-response semantics
Application:       business idempotency and durable outcome
```

### Performance Equations

$$
transmission\ delay = \frac{packet\ size\ in\ bits}{link\ rate\ in\ bits/s}
$$

$$
bandwidth\text{-}delay\ product = bandwidth \times RTT
$$

$$
Little's\ Law: L = \lambda W
$$

$$
CIDR\ address\ count = 2^{address\ bits-prefix\ length}
$$

### Interview Checklist

* Can you explain every step after entering a URL?
* Can you distinguish frames, packets, segments, datagrams, and streams?
* Can you subnet IPv4 addresses and apply longest-prefix matching?
* Can you explain ARP, NAT, DNS recursion, and routing?
* Can you draw TCP setup, reliability, flow control, and teardown?
* Can you explain why application framing is required over TCP?
* Can you compare HTTP/1.1, HTTP/2, HTTP/3, REST, and gRPC?
* Can you explain TLS identity validation and termination boundaries?
* Can you compare L4/L7 balancing, forward/reverse proxies, and CDNs?
* Can you reason about timeouts, retries, idempotency, and overload?
* Can you calculate transmission delay, BDP, CIDR size, and Little's Law?
* Can you debug DNS, connect, TLS, and HTTP failures independently?

The central rule is to preserve layer boundaries while reasoning end to end. IP
gets a packet toward a host, TCP can deliver an ordered byte stream to a socket,
TLS can protect that stream, and HTTP can carry a request. None of those alone
proves that the intended business operation completed exactly once.