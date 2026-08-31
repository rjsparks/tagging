# Prompt A2 — Inductive (bottom-up) tag vocabulary

Run once, after building the stratified sample described in README.md. Model: a
frontier reasoning model with a long context window, temperature 0.

The sample is ~1,200 RFC records (title + date + status + abstract-or-body-excerpt),
stratified by decade, status, and stream as described in README.md.

**Strip `area`, `stream`, `source`, and `keywords` from the records before
sending them.** All four come from the datatracker and including them would collapse
this pass into Prompt A1 — `source` gives the producing group's full name, so the model
would read "Domain Name System Operations" off the record and reproduce the org chart
instead of clustering the content. Titles, dates, statuses and abstracts only. Assert
this in code before sending; when it goes wrong it goes wrong silently.

**Run this in a session that has not seen Prompt A1 or its output.** The value of
this pass is that it sees what is actually in the corpus rather than what the IETF's
organisational chart says should be there.

---

You are given a representative sample of ~1,200 documents from the RFC series,
spanning 1969 to the present. Induce a tag vocabulary **from this evidence alone**.

The RFC Editor will use it to let readers subscribe to tags and be notified when a
new RFC carrying one is published.

## Method — follow this order, and show your work at each step

1. **Read the whole sample before naming anything.** Do not begin proposing tags
   while reading.
2. **Cluster.** Group the documents by what they are actually about. Let the
   clusters fall where the documents fall, including clusters that cut across any
   organisational boundary you might expect, and clusters that exist only in one
   decade.
3. **Report cluster sizes** in the sample before you name the clusters. A cluster
   holding 3 of 1,200 documents and one holding 180 are different kinds of object
   and should not be given the same kind of name.
4. **Name** the clusters in the plainest language that a working engineer outside
   the IETF would recognise.
5. **Assign the names to facets** — `topic/` for broad subject areas, `tech/` for
   specific named protocols and technologies, `kind/` for what sort of document it
   is. Budget: 25–35 topic, 90–140 tech, 8–12 kind; 125–185 total.

## Constraints

- **Ground every tag in the sample.** Each one must cite at least three RFC numbers
  from the sample that carry it. If you cannot find three, the tag does not survive
  this pass — say so in `rejected` rather than keeping it.
- **Do not import vocabulary the sample does not support.** If you know a working
  group exists but nothing in the sample reflects it, that is a finding to report
  under `expected_but_absent`, not a tag to emit. Resist the pull toward the
  familiar taxonomy; the reconciliation pass will restore anything genuinely missing.
- **Give the old corpus its due.** About 200 of the 1,200 records predate 1990 — a
  sixth of the sample for a tenth of the corpus, floored deliberately so the clusters
  can form.
  Some of those records carry a one-line editor-written abstract rather than an
  author's — "Susceptibility of ARPANET to security violations" is the whole of
  RFC 602's. Terse is not uninformative; cluster on it.
  Those documents are about things — host-to-host protocols, NCP, ARPANET
  operations, early mail, network measurement, the FTP and Telnet lineages,
  meeting notes and design correspondence. Tag them on their own terms. If a
  cluster is historically bounded, say so; do not stretch a modern tag over it.
- **Note documents you could not cluster.** An RFC that resists every cluster is
  information about the vocabulary's blind spots.
- **Scale each tag to subscription volume.** From its share of the sample, project
  its count across the full ~9,800-RFC corpus and its likely rate of new
  publications per year. Flag any tag projecting under 15 documents or over 1,500.

## Output

A single YAML document, no prose around it:

```yaml
clusters_before_naming:
  - size_in_sample: 47
    description: <what these documents have in common, before you gave it a name>
    became: tech/quic
facets:
  topic:
    - id: <slug>
      label: <display name>
      definition: <one sentence for a subscriber>
      evidence: [821, 5321, 8461]        # >= 3 RFC numbers from the sample
      sample_count: 38
      projected_corpus_count: 310
      projected_new_per_year: 6
      era: all | pre-1990 | post-2000    # if the cluster is time-bounded
  tech: [...]
  kind: [...]
rejected:
  - candidate: <slug>
    reason: <fewer than three supporting documents / subsumed by X / not a subject>
unclusterable:
  - rfc: 748
    why: <why nothing fit>
expected_but_absent:
  - <topics you anticipated finding and did not, with your reading of why>
```
