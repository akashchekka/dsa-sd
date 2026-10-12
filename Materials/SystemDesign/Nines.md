---
title: Availability Nines (99% to 99.9999%)
description: Interview notes on achieving availability targets from two nines to six nines, covering dependency math, redundancy, recovery time, blast radius, per-level requirements, and active-active vs active-passive
---

## What each level allows

| Availability       | Downtime per year | Per month | Per day  |
|--------------------|-------------------|-----------|----------|
| 99% (2 nines)      | 3.65 days         | 7.2 hours | 14.4 min |
| 99.9% (3 nines)    | 8.8 hours         | 43 min    | 1.4 min  |
| 99.99% (4 nines)   | 53 min            | 4.3 min   | 8.6 sec  |
| 99.999% (5 nines)  | 5.3 min           | 26 sec    | 0.9 sec  |
| 99.9999% (6 nines) | 32 sec            | 2.6 sec   | 0.09 sec |

Each extra nine allows 10 times less downtime, and it usually costs about 10
times more in money, engineering, and process.

> [!IMPORTANT]
> Start with "which nine does this product actually need?", not "how do I get
> the most nines?"

## How availability is measured

* **SLI (service level indicator):** What you measure, for example the
  percentage of successful requests.
* **SLO (service level objective):** Your internal target, for example 99.99%.
* **SLA (service level agreement):** The contract with customers, with refunds
  if missed. Set it looser than the SLO so you have a safety margin.

Define what "down" means up front: errors only, or also requests slower than,
say, 1 second.

Google measures availability by **requests**, not by clock time:

```text
Availability = successful requests / total requests
```

This matches what users feel. An outage at 3 a.m. with little traffic hurts
fewer people than one at peak, and an outage that hits 5% of users costs less
than one that hits everyone.

## The four ideas behind every level

All four ideas answer one question: how often will users see a failure, and
for how long? Each idea gives you a different lever to pull.

### Idea 1: Dependencies multiply

A request often passes through several services, like a relay race. It
succeeds only if every one of them works, so the chances multiply.

```text
User -> API gateway -> Auth service -> Order service -> Database
         99.9%           99.9%           99.9%           99.9%

Chance all 4 work = 0.999 x 0.999 x 0.999 x 0.999 = 99.6%
```

Each service is three nines, but the whole request isn't. **A chain is weaker
than its weakest link.**

| Critical dependencies, each at 99.9% | Combined availability | Downtime per month |
|--------------------------------------|-----------------------|--------------------|
| 1                                    | 99.9%                 | 43 min             |
| 3                                    | 99.7%                 | 2.2 hours          |
| 5                                    | 99.5%                 | 3.6 hours          |
| 10                                   | 99.0%                 | 7.2 hours          |

An easier way to think about it: **the downtime of your dependencies adds
up.** If your budget is 4 minutes per month (four nines) and you have 3
dependencies that are each down 4 minutes per month, you're at 12 minutes,
three times over budget.

#### Hidden dependencies

Teams usually count only the obvious ones. Also count DNS, the login or token
service, the config service, secrets storage, the service mesh, and sometimes
logging (if logging blocks requests when it's slow).

#### What to do about it

1. Remove critical dependencies. Does this request really need that call?
2. Make dependencies "soft" with a fallback, so their failure doesn't fail the
   request:
   * Recommendations service down: show the product page without
     recommendations.
   * Pricing service slow: use a cached price from 1 minute ago.
   * Email service down: queue the email and send it later.
3. Make the remaining critical dependencies **one nine better** than your
   target. A four-nines service needs five-nines critical dependencies.

> [!TIP]
> "My service can't be more available than its critical dependencies combined,
> so I either remove dependencies, give them fallbacks, or require them to be a
> nine better than me."

### Idea 2: Redundancy adds nines, if copies fail independently

Flip it around. With **two copies where either one can serve**, the request
fails only if both are down at the same time. Like a plane with two engines,
it needs only one to fly.

```text
Each server is down 1% of the time.
Both down at the same time = 1% x 1% = 0.01%
Availability = 99.99%
```

| Independent copies, each 99% | Chance all are down | Availability |
|------------------------------|---------------------|--------------|
| 1                            | 1%                  | 99%          |
| 2                            | 0.01%               | 99.99%       |
| 3                            | 0.0001%             | 99.9999%     |

On paper, three cheap servers give six nines. In reality they don't, because
of one word: **independent.**

#### Why copies fail together

The math assumes one copy failing says nothing about the other. In real life,
copies often fail for the same reason at the same time.

| Shared cause            | Example                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| Same location           | Both servers are in one rack or zone, and its power or network fails    |
| Same bad change         | A bad deploy or config push reaches every copy within minutes           |
| Same bug                | A date-handling or leap-second bug crashes every server at once         |
| Same dependency         | Both copies rely on the same DNS or database                            |
| Overload chain reaction | One copy dies, the other gets double traffic and dies too               |

The last row is easy to miss. Two servers each running at 70% load aren't
redundant. When one dies, the other needs 140%, so it falls over too.

#### What to do about it

* Spread copies across racks, zones, and regions.
* Stagger changes. Never deploy to every copy at once.
* Keep spare capacity. For example, run 3 copies at under 66% each, so 2 can
  carry the full load.
* Use diversity for the highest nines: different software versions, vendors,
  or network providers.

> [!TIP]
> "Redundancy multiplies away failures only if they're independent, so most of
> the work at higher nines is removing shared causes: same zone, same deploy,
> same dependency, and not enough spare capacity."

#### How ideas 1 and 2 combine

Real systems are chains of redundant groups. Make each link redundant to raise
its availability (idea 2), then multiply the links (idea 1).

```text
[3 gateways] -> [3 app servers] -> [DB primary + standby]
  ~99.999%         ~99.999%           ~99.99%
Whole chain ~ 99.99%  (the weakest link still decides)
```

### Idea 3: Fail less often, or recover faster

```text
Availability = time working / (time working + time broken)
```

There are only two levers:

* Fail less often. Engineers call this MTBF, mean time between failures.
* Recover faster. Engineers call this MTTR, mean time to recovery.

#### Worked example

Assume one incident per month. A month has about 43,200 minutes.

| Time to recover | Availability |
|-----------------|--------------|
| 7 hours         | 99%          |
| 43 min          | 99.9%        |
| 4 min           | 99.99%       |
| 26 sec          | 99.999%      |

Same failure rate, but **recovery speed alone decides your nines.**

#### Why humans become too slow

```text
Errors start
 +2-5 min   Alert fires (it waits for a steady signal to avoid false alarms)
 +5 min     On-call engineer wakes up, acknowledges, opens a laptop
 +10-20 min Finds the cause ("it was the 2pm deploy")
 +5-10 min  Rolls back, waits for it to finish
 = 25-40 min total
```

One human-handled incident uses up a whole month of three-nines budget.

| Target  | Recovery must take | So recovery is done by                                                |
|---------|--------------------|-----------------------------------------------------------------------|
| 3 nines | Under ~40 min      | A human with good runbooks                                            |
| 4 nines | Under ~4 min       | Automation: health checks, automatic failover, automatic rollback     |
| 5 nines | Under ~26 sec      | Nothing to recover: spare copies are already serving traffic          |

With automation, a health check fails after 10 seconds and the load balancer
removes the server after 20 seconds, so users see under a minute of errors.
With active-active, there's no recovery step at all.

#### Which lever to pull

* Fail less often with good testing, code review, canary releases, and fewer
  risky changes.
* Recover faster with automated detection, automatic failover and rollback,
  and feature flags to switch things off.

At high nines, focus on fast recovery. You can't prevent every failure, but
you can make each one short.

> [!TIP]
> "Four nines leaves about 4 minutes per incident per month, and a human can't
> even acknowledge a page that fast, so recovery has to be automatic. At five
> nines, the system must survive failures without a recovery step."

### Idea 4: Limit how many users a failure hits (blast radius)

Most failures don't affect everyone, and an outage for 5% of users isn't the
same as one for 100%. With request-based measurement, smaller failures cost
proportionally less.

| Incident                                              | Users affected | Duration | Cost in full-outage minutes |
|-------------------------------------------------------|----------------|----------|-----------------------------|
| Whole system down                                     | 100%           | 10 min   | **10 min**                  |
| One of 20 cells down                                  | 5%             | 10 min   | **0.5 min**                 |
| Bad canary at 1% of traffic, rolled back automatically | 1%            | 5 min    | **3 sec**                   |

The same 10-minute failure costs 20 times less if it only hits one cell. That's
how teams reach five nines even though things break all the time: each failure
touches only a small slice of users.

#### How to make failures smaller

* **Cells:** Split users into many independent copies of the whole stack, each
  with its own servers and database. A bug or bad deploy hurts one cell.
* **Canary releases:** New code goes to 1% of traffic first.
* **Gradual rollouts:** One zone, then one region, then the rest, with waiting
  time between steps.
* **Shuffle sharding:** Give each customer a random small set of servers, so
  one bad customer rarely takes down anyone else completely.
* **Graceful degradation:** Turn off a broken feature instead of failing the
  whole page.

> [!TIP]
> "I measure availability as the request success rate, and I design so that
> any single failure, whether a bug, a bad deploy, or a dead database, only
> reaches a small fraction of users."

### Putting the four ideas together

```text
Downtime  ~  how often things fail  x  how long each lasts  x  how many users it hits
```

| Lever                          | Idea   | Main techniques                                                                     |
|--------------------------------|--------|-------------------------------------------------------------------------------------|
| Fewer failures reach users     | 1 and 2 | Fewer critical dependencies, fallbacks, independent redundant copies, safer changes |
| Shorter failures               | 3      | Automated detection, failover, and rollback, or active-active with no recovery step |
| Smaller failures               | 4      | Cells, canaries, gradual rollouts, graceful degradation                             |

Each extra nine means shrinking one or more of these factors by about 10 times.

## What each level requires

### 2 nines (99%): about 7 hours down per month

Fine for internal tools, batch jobs, and admin dashboards.

* A single region, possibly a single server, and one database with regular
  backups.
* Planned maintenance windows are acceptable.
* Manual deploys, with on-call during business hours.
* Recovery means a person restarts or restores from backup within a few hours.

### 3 nines (99.9%): about 43 minutes per month

Fine for most SaaS products and internal business-critical apps. The goal is
to remove single points of failure inside one region.

* Several app servers behind a load balancer, with health checks that remove
  bad servers automatically.
* A database with a standby in another zone (a separate building), with
  automatic failover.
* No maintenance windows: rolling deploys plus one-click rollback.
* 24/7 on-call with paging, alerts on user-facing errors, runbooks, and tested
  backups.

### 4 nines (99.99%): about 4 minutes per month

Fine for payments, large consumer apps, ride hailing, and e-commerce checkout.
One bad incident uses the whole month's budget, and about 70% of outages come
from changes (code deploys and config pushes). You need both safer
architecture and safer changes.

#### Architecture at four nines

* Active-active across 3 zones, with enough spare capacity to lose a zone
  without overload (N+1 or N+2).
* Automatic failover in under a minute for everything, including the database.
* Multi-region, at least a warm standby with regularly tested failover,
  because cloud regions do have rare outages.
* Every dependency treated as something that will fail: timeouts, retries with
  backoff and jitter, circuit breakers, and fallbacks that serve cached or
  degraded results instead of errors.
* Overload protection: rate limiting, load shedding (drop low-priority work
  first), and autoscaling.

#### Changes at four nines

* Canary releases: 1% of traffic, then 10%, then 100%, with automatic rollback
  if error rates rise.
* Feature flags to switch off a bad feature in seconds without a deploy.
* Config changes go through the same review and gradual rollout as code.

#### Process at four nines

* **Error budgets:** 4 minutes per month is the budget. If it's used up,
  feature launches freeze and the team works on reliability.
* Blameless postmortems with tracked fixes.

### 5 nines (99.999%): about 26 seconds per month

Fine for core infrastructure such as cloud storage, identity and login, DNS,
payment networks, telecom, and globally replicated databases like Spanner,
whose multi-region SLA is 99.999%.

Detecting a failure alone can take 30 seconds, so **failover is already too
slow.** The system must keep working through failures without any failover
step.

#### Architecture at five nines

* Active-active in 3 or more regions. Every region serves live traffic all the
  time.
* Data written by majority vote across regions (consensus, as in Spanner). If
  one of 3 regions dies, the other 2 still form a majority and keep going, and
  nothing needs to be promoted.
* Clients route around failures instantly: global anycast load balancing, plus
  client-side retries to another region. For important reads, send the request
  to two replicas and use whichever answers first (hedged requests).
* **Cell-based architecture:** Split users into many fully independent copies
  of the stack. A bug or bad deploy hits only one cell, for example 5% of
  users.
* **Static stability:** The serving path keeps working with its last-known
  config if the control plane (deploy system, config service, autoscaler) is
  down.
* No global single points of failure: no global database, global lock, or
  global config push.
* Remove critical dependencies instead of hardening them. If a dependency
  can't reach five nines, the system must work without it.

#### Changes at five nines

* Deploy one cell or one region at a time, with hours of bake time between
  steps, and never change two regions at once.
* Fully automated rollback with no human approval needed.

#### Process at five nines

* **Chaos engineering:** Deliberately kill servers, zones, and dependencies in
  production to prove the system survives. Google runs yearly DiRT
  disaster-recovery exercises.
* Regular region evacuation drills.

### 6 nines (99.9999%): about 2.6 seconds per month

Be honest in the interview: almost no full product achieves six nines as users
experience it. The user's own phone network and ISP are far less reliable than
that. Six nines is realistic only for narrow, simple components:

* DNS served by anycast (AWS Route 53 even offers a 100% SLA)
* Telecom switching, power grid control, and payment network cores
* The data path of storage systems

What it takes, on top of five nines:

* **Extreme simplicity:** Small code, few features, rarely changed. Every
  change is a risk, so the best change is no change.
* **Redundancy with no switchover:** Every request can be served by many
  independent locations at once (anycast), and lost requests are retried or
  hedged automatically within milliseconds.
* **Diversity to avoid shared bugs:** Run different software versions side by
  side, and use different hardware vendors, network providers, and power
  feeds.
* **Very slow, staged changes,** sometimes taking weeks to reach every
  location.
* **Formal verification or heavy testing** of critical logic.
* **Independent infrastructure:** Separate power, cooling, and network paths.

> [!NOTE]
> Don't confuse availability with durability. "Eleven nines" for cloud storage
> is the chance of **losing** an object, not the chance of being **unable to
> reach** it. Durability comes from copies plus checksums and repair.
> Availability comes from serving paths.

## Summary of levels

| Level    | Downtime per month | Redundancy                                              | Recovery                                     | Deploys                                     | Operations                          |
|----------|--------------------|---------------------------------------------------------|----------------------------------------------|---------------------------------------------|-------------------------------------|
| 99%      | 7 hours            | Single server or region                                 | Manual, hours                                | Manual, maintenance windows                 | Business-hours on-call              |
| 99.9%    | 43 min             | Multi-zone, database standby                            | Auto failover in a region, humans for the rest | Rolling deploys with rollback             | 24/7 paging, runbooks               |
| 99.99%   | 4 min              | Active-active zones, multi-region standby               | Fully automated, under a minute              | Canary, auto rollback, feature flags        | Error budgets, postmortems          |
| 99.999%  | 26 sec             | Active-active regions, majority-vote data, cells        | No failover needed, survives in place        | One cell or region at a time, long bake times | Chaos testing, evacuation drills  |
| 99.9999% | 2.6 sec            | Many independent locations, diverse software and vendors | Instant reroute with hedging and anycast    | Rare, weeks-long rollouts                   | Narrow scope, extreme simplicity    |

## Active-active vs active-passive

Both terms describe how redundant copies share the work. The difference is
whether the backup copy serves real traffic all the time or only after a
failure.

### Active-passive: one serves, one waits

```text
            Users
              |
              v
     +-----------------+
     |  Load balancer  |
     +-----------------+
         |          :
   all traffic      :  no traffic (until failover)
         v          :
   +----------+   copy    +-----------+
   |  ACTIVE  | --------> |  PASSIVE  |
   | (primary)|   data    | (standby) |
   +----------+           +-----------+
```

* Only the active copy serves users. The passive copy receives a copy of the
  data and waits.
* When the active copy fails: detect the failure, promote the passive copy,
  and point traffic at it. This sequence is **failover**.
* Example: a database primary with a standby in another zone.

#### How ready the passive side is

| Type             | What's running on the standby                                     | Recovery time                 | Cost          |
|------------------|-------------------------------------------------------------------|-------------------------------|---------------|
| **Cold standby** | Nothing. Only backups exist. Servers start after the failure.     | Hours                         | Lowest        |
| **Warm standby** | Small servers running, data copied continuously, no traffic       | Minutes: scale up, then switch | Medium       |
| **Hot standby**  | Fully sized, fully up to date, ready for traffic immediately      | Seconds to a minute           | Close to double |

#### Two numbers to state

* **RTO (recovery time objective):** How long until service is back. Cold is
  hours, hot is seconds.
* **RPO (recovery point objective):** How much recent data you can lose. Data
  is usually copied asynchronously, so the last few seconds of writes may be
  lost on failover. Synchronous copying makes the loss zero, but slows every
  write.

#### Pros and cons of active-passive

Pros:

* Simple data model. Only one copy accepts writes, so there are no write
  conflicts.
* Easy to reason about and operate.

Cons:

* You pay for idle capacity.
* Failover runs rarely, so it's poorly tested and often breaks when needed.
* Downtime during the switch, usually seconds to minutes.
* **Split brain risk:** If the active copy is cut off rather than dead, both
  may think they're the leader. Fencing (leases, epoch numbers, or cutting off
  the old copy's access) ensures only one accepts writes.
* A standby that hasn't served traffic in months may have the wrong config,
  too little capacity, or a cold cache.

### Active-active: all copies serve at the same time

```text
               Users
                 |
                 v
     +-----------------------+
     |  Global load balancer |
     +-----------------------+
        |        |        |
       1/3      1/3      1/3   of traffic
        v        v        v
   +--------+ +--------+ +--------+
   |Region A| |Region B| |Region C|    every copy serves real users
   +--------+ +--------+ +--------+
        \________|________/
          data kept in sync
```

* Every copy serves real traffic all the time.
* When one fails, the load balancer stops sending it traffic and the others
  absorb its share. No promotion step is needed.
* Example: stateless web servers in 3 zones, or a global service in 3 regions.

#### Capacity rule

Survivors must handle the extra load.

```text
Each of 3 regions runs at most ~66% of its capacity.
Lose 1 of 3 -> each survivor goes from 66% to ~100%.
```

With 2 regions, each must stay below 50%, so each region is sized for the full
peak load. That's 2 times the peak in total, the same hardware as active-passive
with a hot standby. Active-passive leaves one whole region idle, while 2-region
active-active leaves half of each region idle.

That's one reason 3 or more active copies is common. Even at the same cost,
2-region active-active is usually better than a hot standby, because failover
is exercised constantly and users are served from the closer region.

#### The hard part: writes

Stateless servers are easy to run active-active. Data is hard. If a record can
change in Region A and Region B at the same moment, which change wins?

| Approach                                 | How it works                                                                             | Trade-off                                                                                         | Examples                                  |
|------------------------------------------|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------|
| **Partition the writes**                 | Each user or record has one home region that accepts its writes                          | No conflicts, but far-away writes are slow, and moving a user's home needs care                   | Most large apps: users sharded by region  |
| **Majority vote (consensus)**            | Each write must be confirmed by a majority of regions                                    | Strong consistency, but each write waits a cross-region round trip (tens of ms)                   | Google Spanner, CockroachDB               |
| **Accept writes everywhere, merge later** | Each region writes locally and syncs in the background, then resolves conflicts         | Fast local writes, but last write wins can drop data, or you need data types that merge (CRDTs)  | DynamoDB global tables, Cassandra         |

#### Pros and cons of active-active

Pros:

* Failures are routine. Traffic shifting happens all the time, so it's always
  tested.
* Near-zero downtime: losing a copy only means less capacity.
* No idle hardware.
* Lower latency, because users are served by the nearest region.

Cons:

* Concurrent writes must be handled with one of the approaches above.
* Needs global traffic routing and cross-region replication, so it costs more
  to build.

### Side-by-side

| Point                  | Active-passive                              | Active-active                                     |
|------------------------|---------------------------------------------|---------------------------------------------------|
| Who serves traffic     | One copy                                    | All copies                                        |
| On failure             | Detect, promote, switch                     | Stop routing to the dead copy                     |
| Downtime               | Seconds to hours, depending on standby type | Near zero                                         |
| Data writes            | Simple: one writer                          | Hard: partition, consensus, or conflict merging   |
| Idle capacity          | Standby sits idle                           | Every copy works, but needs headroom              |
| Confidence in failover | Low: rarely exercised                       | High: exercised constantly                        |
| Complexity             | Lower                                       | Higher                                            |
| Typical availability   | Up to 3 to 4 nines                          | 4 to 5+ nines                                     |

### Mixing both in one system

Real systems use different patterns for different layers:

```text
 App servers:    active-active across 3 zones         (stateless, easy)
 Cache:          active-active, each region its own    (losing it is fine)
 Database:       active-passive inside a region        (one primary, standby in another zone)
 Across regions: active-active traffic, but each user's writes go to their home region
```

In a ride-hailing design, for example, matching and location services run
active-active in every region, while each trip record has one writer in its
home region and a hot standby elsewhere.

### When to choose which

* **Active-passive:** Strong consistency with simple writes, budgets that
  don't fit multi-region writes, or targets up to about 3 to 4 nines. Most
  relational databases start here.
* **Active-active:** Stateless services (almost always), global low-latency
  products, and targets of 4 to 5+ nines, where a failover step is too slow or
  too risky.

## The answer in one paragraph

> "Every nine allows 10 times less downtime and costs roughly 10 times more, so
> I'd start by agreeing on the nine the product needs and measuring it as a
> request success rate. Four ideas drive the design: dependencies multiply, so
> I keep critical ones few and give the rest fallbacks; redundancy adds nines
> only when copies fail independently; downtime is failure frequency times
> recovery time; and limiting blast radius makes each failure cheaper. Three
> nines comes from removing single points of failure inside a region. Four
> nines leaves about 4 minutes per month, so recovery must be automatic and
> every change rolls out through canaries with automatic rollback, enforced by
> an error budget. Five nines leaves no time for failover, so I'd run
> active-active in 3 or more regions with majority-vote replication, split
> users into independent cells, keep the serving path working when the control
> plane is down, and test it with chaos engineering. Six nines is realistic
> only for narrow, simple components like anycast DNS, using extreme
> simplicity, redundancy with no switchover, and diverse implementations so one
> bug can't take down every copy."
