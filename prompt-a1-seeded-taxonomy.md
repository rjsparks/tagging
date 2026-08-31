# Prompt A1 — Seeded (top-down) tag vocabulary

Run once. Model: a frontier reasoning model, temperature 0. Supply `seed/structure.md`
— the real area, stream, and working-group structure of the corpus with document counts,
group type and state, and a charter excerpt per group, generated from the datatracker.
Do **not** supply any RFC abstracts or titles; this pass sees organisational structure only, so that its output is
*independent* of Prompt A2's content-derived pass. Independence is the point — A3
reconciles the two and disagreement between them is signal.

---

You are helping the RFC Editor build the initial tag vocabulary for a new
subscription feature on rfc-editor.org. Logged-in users will subscribe to tags and
be notified of events on RFCs carrying them — most importantly the publication of a
new RFC.

You are given `seed/structure.md`: every area code, working-group acronym, and
stream in the RFC series, with the number of documents each produced, whether the group
is still active, and the opening of its charter where one exists. Propose a
**faceted** tag vocabulary derived from that structure. Do not hedge or ask
questions; produce the vocabulary.

## Facets and budget

- `topic/` — 25 to 35 tags. Broad subject areas, the level at which a curious
  practitioner would say "I care about this part of the Internet." Browsable as a
  single screen.
- `tech/` — 90 to 140 tags. Specific protocols, protocol families, formats, and
  named technologies. The level at which someone says "tell me when anything new
  ships for BGP."
- `kind/` — 8 to 12 tags. What the document *is*, as distinct from what it is about.

Total must land between 125 and 185 tags.

## What the structure file tells you

Work from the counts, not from recollection. If a working group is not in the file
it produced no RFCs, and if your memory of an acronym conflicts with the file, the
file wins.

- **19 area codes**, including ones long retired: `app` (844), `rai` (465),
  `usv` (34), `sub` (23), `ops-old` (11), `osi` (4), `ipng` (2), `mgt` (59). The
  live areas skew hard — `rtg` 1,416, `int` 994, `ops` 993, `sec` 991, `art` 475,
  `tsv` 407, `wit` 379. Retired areas are not dead weight; `app` and `rai` together
  account for over thirteen hundred documents that readers still search for.
- **558 named working and research groups**, with a very long tail: Multiprotocol
  Label Switching 197, Inter-Domain Routing 116, Audio/Video Transport 115, Common
  Control and Measurement Plane 112, Dynamic Host Configuration 108 — but 92
  produced a single document and only 173 reached ten. Do not mint a tag per
  group; the tail is where a vocabulary goes to die. **455 of 572 groups are
  concluded**; the file tells you which, and a group that closed in 1997 should
  weigh differently from one still running.
- **Charters are the strongest signal in the file.** 544 groups have one, and its
  opening paragraphs are a scope statement written by the people who did the work.
  Read it before you name anything derived from that group. Where a charter and an
  acronym disagree about a group's subject, the charter wins.
- **3,372 documents — 34.3% of the corpus — have no working group** to inherit a
  tag from: 2,231 with no group recorded at all, 1,003 attributed to an area rather
  than a group, and 138 at IETF level. This is the part a structure-derived
  vocabulary is worst at, and covering it is the hardest thing this prompt asks of
  you. (The 117 IRTF documents do have research groups behind them, spread thinly
  across many.)
- **Area is absent for 22.7% of documents** (2,231) and a working group for 34.3%.
  Both gaps concentrate in the pre-1990 corpus: ARPANET and NCP, host software,
  early mail and FTP, network measurement, and the design debates that produced
  TCP/IP. Propose tags for that material explicitly, reasoning from what you know
  of the era, and mark them `structure_derived: false` so A3 knows they rest on
  weaker evidence than the rest of your output.

## Rules

1. **Reader-facing names, not insider shorthand.** A tag is a promise to a
   subscriber, and WG acronyms are opaque to most of them. `structure.md` gives
   you each group's full name and charter excerpt alongside its acronym — use them
   rather than expanding acronyms from memory, which across a tail of hundreds of
   long-concluded groups is where a structure-derived vocabulary invents things. "Domain Name System
   Operations" dissolves into `dns`; "Common Control and Measurement Plane"
   becomes `optical-transport-control`. Keep an acronym only where it *is* the
   public name of the technology (`bgp`, `tls`, `dns`, `mpls`, `quic`, `http`).
   Where a full name is itself jargon, the charter excerpt says what the group
   actually worked on, and the parent-area column says what neighbourhood it sat in.
2. **Merge WGs that split for process reasons, not topical ones.** dnsop, dnsext,
   dnssd, dprive, and doh are one DNS story to a subscriber, differentiated by
   `tech/` tags beneath a single `topic/dns`.
3. **A tag must be worth subscribing to.** Before you emit one, estimate how many
   of the ~9,800 RFCs carry it and how many new RFCs per year would fire a
   notification. A tag matching 4 documents is a search result, not a
   subscription; one matching 2,500 is a firehose nobody keeps enabled. Target
   roughly 15–600 documents historically for `tech/`, and 150–1,500 for `topic/`.
   State your estimate for every tag; being wrong is fine, hiding the reasoning is not.
4. **Facets are orthogonal.** `topic/` answers "what area of the Internet,"
   `tech/` answers "which named thing," `kind/` answers "what sort of document."
   If a candidate tag needs two facets to make sense, it is two tags.
5. **Include cross-cutting tags that no single WG owns** where they carry real
   subscriber demand — privacy, internationalization, congestion control,
   deprecations and formal obsoletions, IANA registry creation, April Fools' RFCs.
6. **`kind/` is about document role**, not maturity level alone. Standards-track
   status is already structured metadata on the site and does not need to be
   re-encoded; use `kind/` for distinctions the status field misses, such as a
   document whose main product is an IANA registry, a requirements or problem
   statement, an applicability statement, or a protocol specification proper.

## Output

A single YAML document, no prose around it:

```yaml
facets:
  topic:
    - id: dns
      label: DNS
      definition: <one sentence, written for a subscriber deciding whether to subscribe>
      includes: <what falls inside, one or two sentences>
      excludes: <the nearest neighbouring tags and why they are not this one>
      est_rfc_count: 210
      est_new_per_year: 8
      derived_from: [dnsop, dnsext, dnssd, dprive, doh]   # acronyms from structure.md
      structure_derived: true       # false if proposed for material with no area/WG
  tech: [...]
  kind: [...]
notes:
  coverage_gaps: <parts of the corpus you believe this vocabulary tags poorly>
  contested_calls: <decisions you made that a reviewer should second-guess>
```

The `contested_calls` field is not optional and must not be empty. Name at least
six decisions where you split something that could have been merged, or merged
something that could have been split.
