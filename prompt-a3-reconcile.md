# Prompt A3 — Reconcile the two vocabularies and freeze

Run once, with the A1 and A2 YAML outputs both in context, plus the same ~1,200-record
stratified sample used for A2. Temperature 0.

This pass produces `tags.yaml`, the frozen vocabulary. Everything downstream depends
on it not changing, so this is the output a human reviews line by line before
Prompt B is ever run at scale.

---

You are given two independently produced tag vocabularies for the RFC series:

- **Vocabulary S (seeded)** — derived top-down from the real area, working-group and
  stream structure of the corpus, without seeing any document content.
- **Vocabulary I (inductive)** — derived bottom-up from a ~1,200-document stratified
  sample of titles and abstracts, with all structural fields stripped.

Reconcile them into one frozen vocabulary. Also supplied: the sample itself, and
`seed/keywords.md`.

## `seed/keywords.md` is your naming adjudicator

It holds the 200 author-supplied keywords occurring 20 or more times across the
corpus, frequency-ranked and case-folded, drawn from 29,640 keyword instances on 7,425
documents. This is a third and independent view — not structure, not your sample,
but what authors chose to call their own work.

**No keyword in this file may become a tag.** Not a `topic/`, not a `tech/`, not a
`kind/`. It is an input to *naming and aliases only*. When S and I have both
identified a concept but disagree on what to call it, the name authors actually
write should usually win, and this file is the evidence for which that is. Harvest
aliases from it freely. But a keyword cannot introduce a tag, promote one that S
and I both passed over, or justify keeping one they both rejected — the vocabulary
is selected by S and I, and this file only settles what the selected tags are
called.

The reason is that these keywords are uncurated author self-labelling, held to no
standard of consistency, and the tag set being built here has to be far better than
that. The distribution shows it: 7,281 of 10,567 distinct strings occur exactly
once, and the top of the frequency ranking is contaminated with generic title words
(`protocol` 420, `internet` 326, `network` 135) and with fragments of expanded
acronyms (`management information base` 198, `multipurpose` 64, `simple` 59).
Frequency here measures how often authors typed a word, not how coherent a subject
it is. A term's presence is evidence about naming; its rank is not evidence about
anything.

## How to treat disagreement

Disagreement between S and I is the most informative thing in your input. Work
through it by case rather than averaging:

- **In both, same concept, different name** — keep the name a subscriber would
  recognise. Check `seed/keywords.md` first: if one of the two candidate names
  appears there with real frequency and the other does not, that settles it.
  Failing that, prefer I's name, because I was written from what documents say
  about themselves; but where S uses the technology's genuine public name and I
  invented a descriptive phrase, keep S's. Record the loser as an alias.
- **In S only** — S knows about parts of the corpus the sample under-represents.
  Before keeping it, check the sample for supporting documents. Keep it if the
  concept is real and merely thin in the sample; drop it if it reflects IETF
  process structure that produces no distinct reading experience (a WG that split
  administratively, a directorate, a defunct area name).
- **In I only** — I found something the org chart does not name. This is the
  category most likely to contain the vocabulary's real additions, especially for
  pre-1990 documents and cross-cutting concerns. Keep it unless it is an artifact
  of sampling. Treat a tag that I grounded in three or more documents and S simply
  lacked a name for as a keeper, not an anomaly.
- **Same name, different meaning** — the more dangerous case, because it survives
  review silently. Split into two tags with distinct names, or pick one meaning and
  write the `excludes` field so the other cannot be confused with it.
- **Different granularity** — where S has one tag and I has four beneath it, or the
  reverse, decide by projected subscription volume, not by tidiness.

## Budget and shape

Final vocabulary: 25–35 `topic/`, 90–140 `tech/`, 8–12 `kind/`; 125–185 total. If
reconciliation overshoots, cut by merging the lowest-volume tags upward, never by
truncating a facet.

Every `topic/` tag must have at least two `tech/` tags that commonly co-occur with
it, or it is really a `tech/` tag. Every `tech/` tag must sit naturally under at
least one `topic/`; record that relationship in `parents` (it is a hint for the UI
and for Prompt B, not a hard hierarchy — a tech tag may have several parents).

## Every surviving tag needs a full entry

Prompt B will see only `tags.yaml` and never this reasoning, so each entry must be
self-sufficient enough that a tagger who has never read an RFC can apply it
consistently:

- `definition` — one sentence, addressed to a subscriber deciding whether to subscribe.
- `includes` — what falls inside.
- `excludes` — the nearest neighbouring tags and the line between them. Name them.
- `examples` — 3 RFC numbers that clearly carry the tag.
- `near_misses` — 2 RFC numbers that a careless tagger would assign this tag to,
  and one clause each on why they do not carry it. These do more to hold the
  vocabulary steady across 400 batches than the definitions do.
- `aliases` — names folded in during reconciliation, including WG acronyms. These
  power search without cluttering the browsable list.

## Output

```yaml
version: 1.0.0
frozen: <ISO date>
facets:
  topic:
    - id: dns
      label: DNS
      definition: ...
      includes: ...
      excludes: ...
      examples: [1034, 4033, 9250]
      near_misses:
        - rfc: 2782
          why: ...
      aliases: [dnsop, dnsext, domain-name-system]
      projected_corpus_count: 210
      projected_new_per_year: 8
      source: both | seeded-only | inductive-only
  tech:
    - id: quic
      parents: [transport, web]
      ...
  kind: [...]

reconciliation_log:
  - decision: <what you did>
    s_said: ...
    i_said: ...
    rationale: ...
    confidence: high | medium | low

review_queue:          # ordered; the top of this list is what a human should read first
  - tag: <id>
    question: <the specific judgement call you want a human to confirm>
```

Put every `confidence: low` decision, every `source: inductive-only` tag, and every
tag projecting under 25 or over 1,200 documents into `review_queue`. Do not
suppress a disagreement to produce a cleaner vocabulary; an unresolved question
surfaced here costs a reviewer a minute, and one buried here costs a re-tag of
9,800 documents.
