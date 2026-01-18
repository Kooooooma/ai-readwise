# **Glossary**

<span id="page-574-0"></span>![](images/_page_574_Picture_1.jpeg)

Please note that the definitions in this glossary are short and sim‐ ple, intended to convey the core idea but not the full subtleties of a term. For more detail, please follow the references into the main text.

#### **asynchronous**

Not waiting for something to complete (e.g., sending data over the network to another node), and not making any assumptions about how long it is going to take. See ["Synchronous Versus Asynchro‐](#page-174-0) [nous Replication" on page 153,](#page-174-0) ["Synchro‐](#page-305-0) [nous Versus Asynchronous Networks" on](#page-305-0) [page 284,](#page-305-0) and ["System Model and Reality"](#page-327-0) [on page 306](#page-327-0).

#### **atomic**

- 1. In the context of concurrent operations: describing an operation that appears to take effect at a single point in time, so another concurrent process can never encounter the operation in a "halffinished" state. See also *isolation*.
- 2. In the context of transactions: grouping together a set of writes that must either all be committed or all be rolled back, even if faults occur. See ["Atomicity" on page 223](#page-244-0) and ["Atomic Commit and Two-Phase](#page-375-0) [Commit \(2PC\)" on page 354](#page-375-0).

#### **backpressure**

Forcing the sender of some data to slow down because the recipient cannot keep

up with it. Also known as *flow control*. See ["Messaging Systems" on page 441.](#page-462-0)

#### **batch process**

A computation that takes some fixed (and usually large) set of data as input and pro‐ duces some other data as output, without modifying the input. See [Chapter 10.](#page-410-0)

#### **bounded**

Having some known upper limit or size. Used for example in the context of net‐ work delay (see ["Timeouts and Unboun‐](#page-302-0) [ded Delays" on page 281\)](#page-302-0) and datasets (see the introduction to [Chapter 11](#page-460-0)).

#### **Byzantine fault**

A node that behaves incorrectly in some arbitrary way, for example by sending contradictory or malicious messages to other nodes. See ["Byzantine Faults" on](#page-325-0) [page 304.](#page-325-0)

#### **cache**

A component that remembers recently used data in order to speed up future reads of the same data. It is generally not complete: thus, if some data is missing from the cache, it has to be fetched from some underlying, slower data storage <span id="page-575-0"></span>system that has a complete copy of the data.

#### **CAP theorem**

A widely misunderstood theoretical result that is not useful in practice. See ["The](#page-357-0) [CAP theorem" on page 336.](#page-357-0)

#### **causality**

The dependency between events that ari‐ ses when one thing "happens before" another thing in a system. For example, a later event that is in response to an earlier event, or builds upon an earlier event, or should be understood in the light of an earlier event. See ["The "happens-before"](#page-207-0) [relationship and concurrency" on page](#page-207-0) [186](#page-207-0) and ["Ordering and Causality" on page](#page-360-0) [339.](#page-360-0)

#### **consensus**

A fundamental problem in distributed computing, concerning getting several nodes to agree on something (for exam‐ ple, which node should be the leader for a database cluster). The problem is much harder than it seems at first glance. See ["Fault-Tolerant Consensus" on page 364](#page-385-0).

#### **data warehouse**

A database in which data from several dif‐ ferent OLTP systems has been combined and prepared to be used for analytics pur‐ poses. See ["Data Warehousing" on page](#page-112-0) [91.](#page-112-0)

#### **declarative**

Describing the properties that something should have, but not the exact steps for how to achieve it. In the context of quer‐ ies, a query optimizer takes a declarative query and decides how it should best be executed. See ["Query Languages for Data"](#page-63-0) [on page 42.](#page-63-0)

#### **denormalize**

To introduce some amount of redun‐ dancy or duplication in a *normalized* dataset, typically in the form of a *cache* or *index*, in order to speed up reads. A denormalized value is a kind of precom‐ puted query result, similar to a material‐

ized view. See ["Single-Object and Multi-](#page-249-0)[Object Operations" on page 228](#page-249-0) and ["Deriving several views from the same](#page-482-0) [event log" on page 461.](#page-482-0)

#### **derived data**

A dataset that is created from some other data through a repeatable process, which you could run again if necessary. Usually, derived data is needed to speed up a par‐ ticular kind of read access to the data. Indexes, caches, and materialized views are examples of derived data. See the introduction to [Part III.](#page-406-0)

#### **deterministic**

Describing a function that always pro‐ duces the same output if you give it the same input. This means it cannot depend on random numbers, the time of day, net‐ work communication, or other unpredict‐ able things.

#### **distributed**

Running on several nodes connected by a network. Characterized by *partial failures*: some part of the system may be broken while other parts are still working, and it is often impossible for the software to know what exactly is broken. See ["Faults](#page-295-0) [and Partial Failures" on page 274](#page-295-0).

#### **durable**

Storing data in a way such that you believe it will not be lost, even if various faults occur. See ["Durability" on page 226.](#page-247-0)

#### **ETL**

Extract–Transform–Load. The process of extracting data from a source database, transforming it into a form that is more suitable for analytic queries, and loading it into a data warehouse or batch processing system. See ["Data Warehousing" on page](#page-112-0) [91.](#page-112-0)

#### **failover**

In systems that have a single leader, fail‐ over is the process of moving the leader‐ ship role from one node to another. See ["Handling Node Outages" on page 156](#page-177-0).

#### <span id="page-576-0"></span>**fault-tolerant**

Able to recover automatically if some‐ thing goes wrong (e.g., if a machine crashes or a network link fails). See ["Reli‐](#page-27-0) [ability" on page 6.](#page-27-0)

#### **flow control**

See *backpressure*.

#### **follower**

A replica that does not directly accept any writes from clients, but only processes data changes that it receives from a leader. Also known as a *secondary*, *slave*, *read replica*, or *hot standby*. See ["Leaders and](#page-173-0) [Followers" on page 152](#page-173-0).

#### **full-text search**

Searching text by arbitrary keywords, often with additional features such as matching similarly spelled words or syno‐ nyms. A full-text index is a kind of *secon‐ dary index* that supports such queries. See ["Full-text search and fuzzy indexes" on](#page-109-0) [page 88](#page-109-0).

#### **graph**

A data structure consisting of *vertices* (things that you can refer to, also known as *nodes* or *entities*) and *edges* (connec‐ tions from one vertex to another, also known as *relationships* or *arcs*). See ["Graph-Like Data Models" on page 49](#page-70-0).

#### **hash**

A function that turns an input into a random-looking number. The same input always returns the same number as out‐ put. Two different inputs are very likely to have two different numbers as output, although it is possible that two different inputs produce the same output (this is called a *collision*). See ["Partitioning by](#page-224-0) [Hash of Key" on page 203](#page-224-0).

#### **idempotent**

Describing an operation that can be safely retried; if it is executed more than once, it has the same effect as if it was only exe‐ cuted once. See ["Idempotence" on page](#page-499-0) [478.](#page-499-0)

#### **index**

A data structure that lets you efficiently search for all records that have a particu‐ lar value in a particular field. See ["Data](#page-91-0) [Structures That Power Your Database" on](#page-91-0) [page 70](#page-91-0).

#### **isolation**

In the context of transactions, describing the degree to which concurrently execut‐ ing transactions can interfere with each other. *Serializable* isolation provides the strongest guarantees, but weaker isolation levels are also used. See ["Isolation"](#page-246-0) on [page 225.](#page-246-0)

#### **join**

To bring together records that have some‐ thing in common. Most commonly used in the case where one record has a refer‐ ence to another (a foreign key, a docu‐ ment reference, an edge in a graph) and a query needs to get the record that the ref‐ erence points to. See ["Many-to-One and](#page-54-0) [Many-to-Many Relationships" on page 33](#page-54-0) and ["Reduce-Side Joins and Grouping" on](#page-424-0) [page 403.](#page-424-0)

#### **leader**

When data or a service is replicated across several nodes, the leader is the designated replica that is allowed to make changes. A leader may be elected through some pro‐ tocol, or manually chosen by an adminis‐ trator. Also known as the *primary* or *master*. See ["Leaders and Followers" on](#page-173-0) [page 152.](#page-173-0)

#### **linearizable**

Behaving as if there was only a single copy of data in the system, which is updated by atomic operations. See ["Linearizability"](#page-345-0) [on page 324](#page-345-0).

#### **locality**

A performance optimization: putting sev‐ eral pieces of data in the same place if they are frequently needed at the same time. See ["Data locality for queries" on page 41](#page-62-0).

#### <span id="page-577-0"></span>**lock**

A mechanism to ensure that only one thread, node, or transaction can access something, and anyone else who wants to access the same thing must wait until the lock is released. See ["Two-Phase Locking](#page-278-0) [\(2PL\)" on page 257](#page-278-0) and ["The leader and](#page-322-0) [the lock" on page 301](#page-322-0).

#### **log**

An append-only file for storing data. A *write-ahead log* is used to make a storage engine resilient against crashes (see ["Mak‐](#page-103-0) [ing B-trees reliable" on page 82](#page-103-0)), a *logstructured* storage engine uses logs as its primary storage format (see ["SSTables](#page-97-0) [and LSM-Trees" on page 76](#page-97-0)), a *replication log* is used to copy writes from a leader to followers (see ["Leaders and Followers" on](#page-173-0) [page 152\)](#page-173-0), and an *event log* can represent a data stream (see ["Partitioned Logs" on](#page-467-0) [page 446\)](#page-467-0).

#### **materialize**

To perform a computation eagerly and write out its result, as opposed to calculat‐ ing it on demand when requested. See ["Aggregation: Data Cubes and Material‐](#page-122-0) [ized Views" on page 101](#page-122-0) and ["Materializa‐](#page-440-0) [tion of Intermediate State" on page 419](#page-440-0).

#### **node**

An instance of some software running on a computer, which communicates with other nodes via a network in order to accomplish some task.

#### **normalized**

Structured in such a way that there is no redundancy or duplication. In a normal‐ ized database, when some piece of data changes, you only need to change it in one place, not many copies in many different places. See ["Many-to-One and Many-to-](#page-54-0)[Many Relationships" on page 33.](#page-54-0)

#### **OLAP**

Online analytic processing. Access pattern characterized by aggregating (e.g., count, sum, average) over a large number of records. See ["Transaction Processing or](#page-111-0) [Analytics?" on page 90.](#page-111-0)

#### **OLTP**

Online transaction processing. Access pattern characterized by fast queries that read or write a small number of records, usually indexed by key. See ["Transaction](#page-111-0) [Processing or Analytics?" on page 90.](#page-111-0)

#### **partitioning**

Splitting up a large dataset or computa‐ tion that is too big for a single machine into smaller parts and spreading them across several machines. Also known as *sharding*. See [Chapter 6.](#page-220-0)

#### **percentile**

A way of measuring the distribution of values by counting how many values are above or below some threshold. For example, the 95th percentile response time during some period is the time *t* such that 95% of requests in that period com‐ plete in less than *t*, and 5% take longer than *t*. See ["Describing Performance" on](#page-34-0) [page 13](#page-34-0).

#### **primary key**

A value (typically a number or a string) that uniquely identifies a record. In many applications, primary keys are generated by the system when a record is created (e.g., sequentially or randomly); they are not usually set by users. See also *secondary index*.

#### **quorum**

The minimum number of nodes that need to vote on an operation before it can be considered successful. See ["Quorums for](#page-200-0) [reading and writing" on page 179](#page-200-0).

#### **rebalance**

To move data or services from one node to another in order to spread the load fairly. See ["Rebalancing Partitions" on](#page-230-0) [page 209.](#page-230-0)

#### **replication**

Keeping a copy of the same data on sev‐ eral nodes (*replicas*) so that it remains <span id="page-578-0"></span>accessible if a node becomes unreachable. See [Chapter 5.](#page-172-0)

#### **schema**

A description of the structure of some data, including its fields and datatypes. Whether some data conforms to a schema can be checked at various points in the data's lifetime (see ["Schema flexibility in](#page-60-0) [the document model" on page 39](#page-60-0)), and a schema can change over time (see [Chap‐](#page-132-0) [ter 4](#page-132-0)).

#### **secondary index**

An additional data structure that is main‐ tained alongside the primary data storage and which allows you to efficiently search for records that match a certain kind of condition. See ["Other Indexing Struc‐](#page-106-0) [tures" on page 85](#page-106-0) and ["Partitioning and](#page-227-0) [Secondary Indexes" on page 206](#page-227-0).

#### **serializable**

A guarantee that if several transactions execute concurrently, they behave the same as if they had executed one at a time, in some serial order. See ["Serializability"](#page-272-0) [on page 251](#page-272-0).

#### **shared-nothing**

An architecture in which independent nodes—each with their own CPUs, mem‐ ory, and disks—are connected via a con‐ ventional network, in contrast to sharedmemory or shared-disk architectures. See the introduction to [Part II](#page-166-0).

#### **skew**

- 1. Imbalanced load across partitions, such that some partitions have lots of requests or data, and others have much less. Also known as *hot spots*. See ["Skewed Work‐](#page-226-0) [loads and Relieving Hot Spots" on page](#page-226-0) [205](#page-226-0) and ["Handling skew" on page 407](#page-428-0).
- 2. A timing anomaly that causes events to appear in an unexpected, nonsequential order. See the discussions of *read skew* in ["Snapshot Isolation and Repeatable Read"](#page-258-0) [on page 237,](#page-258-0) *write skew* in ["Write Skew](#page-267-0) [and Phantoms" on page 246,](#page-267-0) and *clock*

*skew* in ["Timestamps for ordering events"](#page-312-0) [on page 291](#page-312-0).

#### **split brain**

A scenario in which two nodes simultane‐ ously believe themselves to be the leader, and which may cause system guarantees to be violated. See ["Handling Node Out‐](#page-177-0) [ages" on page 156](#page-177-0) and ["The Truth Is](#page-321-0) [Defined by the Majority" on page 300.](#page-321-0)

#### **stored procedure**

A way of encoding the logic of a transac‐ tion such that it can be entirely executed on a database server, without communi‐ cating back and forth with a client during the transaction. See ["Actual Serial Execu‐](#page-273-0) [tion" on page 252.](#page-273-0)

#### **stream process**

A continually running computation that consumes a never-ending stream of events as input, and derives some output from it. See [Chapter 11](#page-460-0).

#### **synchronous**

The opposite of *asynchronous*.

#### **system of record**

A system that holds the primary, authori‐ tative version of some data, also known as the *source of truth*. Changes are first writ‐ ten here, and other datasets may be derived from the system of record. See the introduction to [Part III.](#page-406-0)

#### **timeout**

One of the simplest ways of detecting a fault, namely by observing the lack of a response within some amount of time. However, it is impossible to know whether a timeout is due to a problem with the remote node, or an issue in the network. See ["Timeouts and Unbounded](#page-302-0) [Delays" on page 281](#page-302-0).

#### **total order**

A way of comparing things (e.g., time‐ stamps) that allows you to always say which one of two things is greater and which one is lesser. An ordering in which

<span id="page-579-0"></span>some things are incomparable (you can‐ not say which is greater or smaller) is called a *partial order*. See ["The causal](#page-362-0) [order is not a total order" on page 341](#page-362-0).

#### **transaction**

Grouping together several reads and writes into a logical unit, in order to sim‐ plify error handling and concurrency issues. See [Chapter 7.](#page-242-0)

#### **two-phase commit (2PC)**

An algorithm to ensure that several data‐ base nodes either all commit or all abort a

transaction. See ["Atomic Commit and](#page-375-0) [Two-Phase Commit \(2PC\)" on page 354.](#page-375-0)

#### **two-phase locking (2PL)**

An algorithm for achieving serializable isolation that works by a transaction acquiring a lock on all data it reads or writes, and holding the lock until the end of the transaction. See ["Two-Phase Lock‐](#page-278-0) [ing \(2PL\)" on page 257.](#page-278-0)

#### **unbounded**

Not having any known upper limit or size. The opposite of *bounded*.
