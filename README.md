# Plan: initial RFC subject-tag vocabulary and corpus tagging

Status 2026-08-31: nothing generated yet. No vocabulary exists, no RFC is tagged. The
pipeline below is specified and reviewed; the prompts in this directory are written and
current. Execution starts at W0.

Figures throughout come from the datatracker dev environment, DB snapshot 2026-08-19,
`/assets/ietf-ftp/rfc/` populated (9,833 `.txt`, 9,827 `.html`, 1,371 `.xml`,
10,023 `.json`). Re-measure at W0 against the environment you actually run on.

---

## 0. For reviewers

This repo exists for review of the plan. Execution happens in a datatracker development
container, not here.

**You are reviewing the plan, not the vocabulary.** No vocabulary exists yet. The
expensive review — reading `tags.yaml` line by line — is gate 1 at W8, and it comes to
you as a separate round once W5–W7 have produced something. Reviewing the plan well now
is what keeps that round from being wasted.

Read §1 (what we are building), §2 (what is already decided), §7 (the work and its
order), §10 (how we will know it worked). Skip §3, §5, §6 and §12 — execution mechanics.

What we need from you:

| Ask | Where | Who |
|---|---|---|
| Answer **Q1–Q4**. Q1 — reef's schema and API for the vocabulary and the tag→RFC map — is the one that blocks work: it fixes what Stage B delivers. Q3 decides who runs Prompt B for a newly published RFC. | §2 | reef and Purple maintainers |
| Confirm **D6–D9** read correctly, particularly D9. The datatracker's community app already offers RFC subscription by group and area; it is a different feature, will not see these tags, and is not being changed. If that is wrong, say so now — it changes where half the work goes. | §2 | design team |
| Sanity-check the **facet shape** — 25–35 `topic/`, 90–140 `tech/`, 8–12 `kind/`. Already decided (D1), listed so you can see the constraint the prompts work under. Say so now if it looks wrong; it is cheap today and costs a full re-tag after W12. | §2, D1 | design team |
| Agree that **gate 5 measures notifications per year**, not corpus counts. This changes which tags survive: a tag on 400 RFCs all published before 1995 is a good browse category and a dead subscription. | §10 | design team |
| **Own the gold set** — W10 is 150 RFCs tagged by a human, drawn across eras. It is the main piece of human work in the plan and nothing downstream substitutes for it. It needs a name against it. | §7, W10 | volunteer needed |
| Decide **Q5** — whether subject tags should also surface in `rfc-index.xml`. If yes it is an additive `<tags>` element in `add_rfc_xml_index_entries` plus an `rfc-index.xsd` change with external consumers to coordinate; if no, reef is the only place they appear. | §2, Q5 | design team |

Two things worth knowing before you read. The tags are stored in reef, not the
datatracker; the datatracker is here as the source of the metadata the vocabulary is
derived from, and the plan is deliberately thin on datatracker code. And roughly a third
of the corpus has no working group behind it, including almost every document with no
abstract — that set is the hardest part of the job, and §4 says exactly how big it is.

---

## 1. Objective

rfc-editor.org is adding subscription: a logged-in user subscribes to a tag and is
notified of events on RFCs carrying it — above all the publication of a new RFC.
Deliver two things:

1. A frozen subject-tag vocabulary, `tags.yaml`, to be loaded into reef as its initial
   vocabulary.
2. That vocabulary applied to every published RFC, delivered as a tag→RFC map for reef,
   and applied to each new RFC at publication.

**Subscription is the governing constraint.** A wrong tag mails people who did not want
it; a missing tag silently fails someone who did. Two consequences bind every stage:
tags are sized by notification volume rather than conceptual tidiness, and the prompt
that tags the back catalogue must be the same prompt that tags each new RFC, or the two
drift apart.

## 2. Fixed decisions

Made by the design team. Do not relitigate.

| # | Decision |
|---|---|
| D1 | **Faceted vocabulary, 125–185 tags**: `topic/` 25–35 broad subject areas, `tech/` 90–140 named protocols and technologies, `kind/` 8–12 document roles. Not a flat ~40 (too noisy to subscribe to), not a flat ~400 (unbrowsable). |
| D2 | **Derive the vocabulary twice and reconcile**: once top-down from IETF structure, once bottom-up from document content, then adjudicate. Both, not one. |
| D3 | **Tag from title + abstract + metadata.** Not full text, not titles alone. |
| D4 | **The deliverable is prompts plus a run harness**, not a built pipeline. |
| D5 | **Author-supplied keywords are not candidate tags.** They are uncurated author self-labelling; the vocabulary must be better curated than they are. Admitted for naming and aliases only. |

Architecture, as directed by the design team:

| # | Decision |
|---|---|
| D6 | **Tags live in `ietf-tools/reef`.** Reef stores the tag vocabulary and the tag→RFC map, and reef is where new tags are created. The datatracker does **not** store them: no `RfcTagName`, no `Document.rfc_tags`, no migration. Stage B's output is loaded into reef. |
| D7 | **The datatracker is the metadata source, not the tag store.** Everything the vocabulary is derived from — titles, abstracts, groups, areas, charters, publication dates, relations — comes from the datatracker ORM (§4–§6). That is its whole role here, plus the probable relay in D8. |
| D8 | **Publication-time tagging flows Purple → datatracker → reef.** Purple hints the tags for a newly published RFC; the datatracker relays to reef. The hint would ride the existing publication notification, `POST /api/purple/rfc/publish/` (`RfcPubSerializer`, `ietf/api/serializers_rpc.py:286`). Expected shape, not yet settled — see Q1–Q4. |
| D9 | **The community app is out of scope and stays untouched.** The datatracker's existing RFC subscription — `CommunityList`/`SearchRule` with `group_rfc`, `area_rfc`, `author_rfc`, and the `type_id != "draft"` guard in `ietf/community/signals.py` — is a *similar but unrelated* feature. It will not see these tags, no `tag_rfc` rule type is added, and that guard is not this plan's to change. Subscription and notification for subject tags are reef's, not the community app's. |

D9 is stated as a prohibition because the resemblance is a trap: the community app already
subscribes to RFCs by group and area, so it reads like the delivery half of this feature.
It is not, and building toward it would produce a feature wired to the wrong store.

### Open questions

These block W9 and fix Stage B's output format. They are not ours to answer alone.

| # | Question | Needed by |
|---|---|---|
| Q1 | Reef's data model and API for the vocabulary and the tag→RFC map. Determines what Stage B emits and how it is loaded. | W9, and §11's output format |
| Q2 | Does the datatracker persist anything — tag hints, a cached map — or is it purely a relay? Decides whether any datatracker schema change happens at all. | W9 |
| Q3 | Does Purple hint tags itself, or does it call something that runs Prompt B? The same prompt must tag new RFCs as tagged the back catalogue, or the two drift (§1). Whoever runs it, it must be that prompt against the frozen vocabulary. | W15 |
| Q4 | How reef delivers subscription and notification, and whether tag volume there matches the assumptions gate 5 is built on. | W13, W14 |
| Q5 | Should tags also appear in `rfc-index.xml`? The datatracker generates that file from the ORM (`ietf/sync/rfcindex.py`) and rfc-editor.org consumes it, so it is an available channel — but with tags in reef it may not be wanted, and it costs an `rfc-index.xsd` change with external consumers. | after W14 |

## 3. Environment

| Resource | Value | Survives a container rebuild? |
|---|---|---|
| Metadata | Datatracker ORM. `Document.objects.filter(type_id="rfc")` | Named volume `postgresdb-data`. Yes, unless `docker/cleandb` or `docker/cleanall` |
| Document text | `/assets/ietf-ftp/rfc/` = `settings.RFC_PATH`, reached as `doc.text(n)` | Named volume `app-assets`. Yes, unless `docker/cleanall` (`down -v`), which destroys the artifact sync |
| Charters | `settings.CHARTER_PATH`, reached as `group.charter.text()` | Same volume as above |
| This repo | prompts, seed inputs, plan, run outputs. `git@github.com:rjsparks/tagging.git` | Yes — its own git repo with a remote |

This repo is checked out separately from the datatracker, but every stage needs the
datatracker ORM, so scripts run through that checkout's `manage.py` with this repo's path
passed in:

```
TAGGING=/path/to/tagging
cd /path/to/datatracker
TAGGING_DIR=$TAGGING python ietf/manage.py shell -c "exec(open('$TAGGING/baseline.py').read())"
```

After any rebuild or refresh, run W0 before anything else: it re-measures §4 and confirms
`RFC_PATH` is still populated. If `text reachable` comes back near zero, the artifact
sync needs redoing and the `body_excerpt` half of §6 is blocked until it is.

The static mirror is no longer an input. Everything the plan needs is reachable from the
ORM or from `RFC_PATH` through ORM accessors.

## 4. Corpus reference facts

| Fact | Value |
|---|---|
| Published RFCs | 9,828, numbered to 10031 |
| Abstract present | 9,121 (92.8%) |
| Abstract absent | 707 — of which 700 have document text, **7 have neither** (RFC 8, 9, 51, 418, 500, 530, 598) |
| Abstract by band | 1–1499: 746/1,430 · 1500–2999: 1,481/1,498 · 3000–5999: 2,920/2,926 · 6000+: 3,974/3,974 |
| Streams | ietf 7,236 · legacy 1,893 · ise 435 · iab 134 · irtf 127 · editorial 3 |
| Status | ps 4,419 · inf 3,006 · unkn 887 · exp 557 · hist 353 · bcp 336 · ds 138 · std 132 |
| Decades | 1960s 26 · 1970s 666 · 1980s 376 · 1990s 1,593 · 2000s 2,888 · 2010s 2,954 · 2020s 1,325 |
| Area resolved | 7,597 (77.3%) via `area_acronym()`, across 19 codes: rtg 1,416 · int 994 · ops 993 · sec 991 · app 844 · art 475 · rai 465 · tsv 407 · wit 379 · gen 242 · ietf 138 · irtf 117 · mgt 59 · usv 34 · sub 23 · ops-old 11 · osi 4 · rfceditor 3 · ipng 2 |
| Area unresolved | 2,231 (22.7%) — all `group.acronym == "none"`, `type_id == "individ"`. By stream: legacy 1,847 · ise 266 · ietf 102 · iab 11 · irtf 5 |
| Real WG/RG group | 6,456 (65.7%), 558 groups. mpls 197 · idr 116 · avt 115 · ccamp 112 · dhc 108 · tsvwg 93. 92 produced one RFC; 173 reached ten |
| No real group | 3,372 (34.3%) — individ 2,231 · area-type 1,003 · ietf-type 138 |
| Groups with charter text | 544 of 572 |
| Author keywords | 29,640 instances on 7,425 documents; case-folded 10,567 distinct, 7,281 hapax, 200 occurring 20+ |
| Relations | `RelatedDocument`: `obs` 1,543 · `updates` 2,156 |
| Publication rate | 198 RFCs/yr mean 2021–2025 (2021: 240 · 2022: 194 · 2023: 173 · 2024: 175 · 2025: 208) |

**The hard core.** Of the 707 RFCs with no abstract, **706 also have no area and no real
working group**. The two hard sets are all but perfectly nested; better structural
metadata reaches one document. Expect the low-confidence review queue to be dominated by
this set, and treat that as the design working.

## 5. Data access rules

Obey these; each one is a trap that has already been checked.

1. **Use `Document.area_acronym()`, not `Document.area`.** The two disagree by design
   (`ietf/doc/models.py:1209` and `:1226`). `.area` returns `None` for any non-IETF-stream
   document and for documents whose own group *is* an area, resolving well under half the
   corpus. `area_acronym()` gives the 77.3%.
2. **Represent the 2,231 group-less documents as absence of a group**, never as a group
   named `none`. A1 must not read `none` as a subject.
3. **Case-fold author keywords** when regenerating the seed. The DB preserves author case
   (`protocol` 234 + `Protocol` 186); folding reproduces the reviewed ranking exactly
   (10,567 distinct, 200 at ≥20, `protocol` 420, `internet` 326).
4. **Read body text through `doc.text(n)`**, which resolves `RFC_PATH/rfcNNNN.txt` and
   decodes via `ietf.utils.text.decode_document_content`. Do not open files directly; the
   old files need that decoder. Use `doc.text_exists()` to enumerate reachability up front.
5. **Publication date is `doc.latest_event(type="published_rfc").time`** — see
   `Document.pub_date()`. Format `YYYY-MM`.
6. **Subseries** (BCP/STD/FYI) are `Document`s of `type_id` in `bcp`/`std`/`fyi` linked by
   `RelatedDocument`; see `add_subseries_xml_index_entries`. Not a metadata field.
7. **Never derive tags from group membership.** It would look accurate on modern
   IETF-stream RFCs and fail on the 34.3% with no real group — which contains 706 of the
   707 documents with no abstract either. The shortcut is most accurate where tagging is
   easiest and absent where it is hardest. `prompt-b-tag-batch.md` states this; it must
   survive every edit.

## 6. Record schema

Fed to A2 and to B. Frozen — the prompts depend on these key names.

```json
{
  "rfc": 8415,
  "title": "Dynamic Host Configuration Protocol for IPv6 (DHCPv6)",
  "date": "2018-11",
  "status": "PROPOSED STANDARD",
  "stream": "IETF",
  "area": "int",
  "source": "Dynamic Host Configuration",
  "keywords": ["DHCPv6", "IPv6", "DHCP"],
  "abstract": "This document describes ...",
  "body_excerpt": null,
  "obsoletes": [3315, 3633, 3736, 4242, 7083, 7283, 7550],
  "obsoleted_by": [9915],
  "updates": []
}
```

| Field | Source | Rule |
|---|---|---|
| `rfc` | `doc.rfc_number` | |
| `title` | `doc.title` | |
| `date` | `published_rfc` event time | `YYYY-MM` |
| `status` | `doc.std_level.name` | |
| `stream` | `doc.stream.name` | |
| `area` | `doc.area_acronym()` | not `doc.area` |
| `source` | `doc.group.name` | `null` when `group.type_id == "individ"` |
| `keywords` | `doc.keywords` | already a list |
| `abstract` | `doc.abstract` | cap 1,500 chars |
| `body_excerpt` | `doc.text(4000)` | only when `abstract` is empty. First 1,200 chars after the header block; strip form feeds and running headers/footers. 700 records |
| `obsoletes` / `obsoleted_by` / `updates` | `RelatedDocument` `obs` / `updates` | |

Query: `Document.objects.filter(type_id="rfc").select_related("group", "group__parent", "stream", "std_level")`.

~550 tokens per record; ~5.4M tokens for the full Stage B pass.

## 7. Work items

| ID | Work | Depends on | Deliverable |
|---|---|---|---|
| **W0** | Baseline. Run `baseline.py` per §3 — re-measures every §4 figure, enumerates text reachability, and writes the snapshot-dated JSON. Update §4 from its output. | — | `baseline-<date>.json`, §4 updated |
| **W1** | Confirm D6–D9 with the design team. | W0 | Naming and ownership settled |
| **W2** | Record builder: one ORM pass emitting §6 records. | W0 | `build_records.py`, `records.jsonl` |
| **W3** | Seed generation per §8. **Replaces the committed `seed/` files, which are stale** — they were built from the retired mirror by `seed/build-seed.py`, carry pre-datatracker counts, and have no charter excerpts. Do not run A1 on them as they stand. | W2 | 3 regenerated seed files, ORM-based generator |
| **W4** | A2 sample: draw and commit per §9. | W2 | `sample-a2.json` + committed RFC numbers + snapshot date |
| **W5** | Run A1 (`prompt-a1-seeded-taxonomy.md`). Isolated session. | W3 | `vocab-s.yaml` |
| **W6** | Run A2 (`prompt-a2-inductive-taxonomy.md`). Isolated session, stripped records. | W4 | `vocab-i.yaml` |
| **W7** | Run A3 (`prompt-a3-reconcile.md`). | W5, W6 | `tags.yaml` draft + `review_queue` |
| **W8** | **Human review of `tags.yaml`.** Gate 1. Ordered `review_queue` first. | W7 | Frozen `tags.yaml` v1.0.0 |
| **W9** | Plumbing, in parallel from W1 and **blocked on Q1–Q2**: reef vocabulary and tag→RFC schema; a loader that takes Stage B output into reef; the Purple → datatracker → reef hint path. Nothing in the community app; no datatracker schema change unless Q2 says otherwise. | W1, Q1, Q2 | Merged, tested |
| **W10** | Gold set: human-tag 150 RFCs drawn across eras. | W8 | `gold.json` |
| **W11** | Score B against gold. Gate 2. Below ~0.75 F1, fix the prompt or the vocabulary and repeat — do not proceed intending to clean up later. | W9, W10 | Score report |
| **W12** | Stage B full run: ~393 batches of 25. | W11 | `tags-batch-*.json`, loaded into reef |
| **W13** | Gates 3, 4, 4b, 4c, 5, 6 (§10). | W12 | Gate reports, review queue |
| **W14** | Enable export and subscription; announce. | W13 | Live |
| **W15** | Ongoing: per-publication tagging via the Purple hint path (§11), pending Q3; `proposed_tags` review cycle. | W14, Q3 | — |

W10 is the main piece of human work and nothing downstream substitutes for it. W8 is the
only gate that is genuinely expensive to skip: a vocabulary error costs a full re-tag.

## 8. Seed generation (W3)

The `seed/` files in this repo were generated from the retired static mirror and are
marked stale in place. W3 regenerates all three from the ORM; `seed/build-seed.py` is kept
only because its output shape is the one to reproduce.

`seed/structure.md` — input to A1, which never sees document content. Per group, from the
ORM:

- Full name, acronym, `type_id`, `state_id`, parent area, RFC count.
- **Charter excerpt**: first two paragraphs of `group.charter.text()`, capped at 900
  characters. All 544 groups that have one — ~104k tokens total. Do not threshold by RFC
  count: the long tail of concluded groups is exactly where a structure-derived
  vocabulary invents a subject from an acronym, and 455 of 572 groups are concluded.
  (Full charter text would be ~378k tokens; ≥10-RFC groups only would be ~32k and cover
  5,092 of 6,456 grouped RFCs.)
- Areas and streams with counts, from §4.
- The 2,231 group-less documents shown as an unattributed block per §5.2.

`seed/keywords.md` — the 200 case-folded author keywords occurring 20+ times,
frequency-ranked. Input to **A3, for naming and aliases only** (D5).
`seed/keywords-full.json` — all 10,567 folded strings with counts, for alias harvesting.
Optionally carry the case-preserved variants as alias candidates; author capitalisation is
often the correct rendering of an acronym.

## 9. A2 sample (W4)

1,200 records, one ORM query with `Count` annotations. Stratify so the sample reflects the
corpus's shape rather than recent publication volume:

- **By decade**, proportional but floored at 60 per decade. Without the floor the 1980s
  get ~46 records and no cluster forms.
- **By status**, at least 40 each of Experimental, Historic, BCP and Unknown.
- **By stream**, at least 30 each of IRTF, IAB and ISE, and at least 200 from `legacy`
  (1,893 documents, the largest block with no working group behind it).
- **By producing group**, cap any one group at 8 records, so mpls and idr do not crowd out
  the tail. Exempt the group-less block — capping it at 8 would defeat the stream floor.
  Apply the cap when selecting; the field is stripped before sending.
- Fill the remainder uniformly at random. Seed the RNG; commit the sampled RFC numbers and
  the snapshot date so A2 is reproducible after a prompt edit.

**Strip `area`, `stream`, `source` and `keywords` from the A2 records.** Serialise to §6
records first and strip there; never pass model instances or let a template touch
`doc.group`. Assert in code that no A2 record contains any of the four keys. This is the
rule that fails silently: if A2 sees the structural fields it reproduces the org chart,
A3's disagreement list comes back empty, and D2 has bought nothing.

## 10. Quality gates

| # | Gate | Needs a human | When |
|---|---|---|---|
| 1 | **Vocabulary review.** Read `tags.yaml` against A3's ordered `review_queue`. | yes | W8, before any Stage B run |
| 2 | **Gold set.** Score B against 150 human-tagged RFCs across eras. Below ~0.75 F1, stop and fix. | yes | W11 |
| 3 | **Self-consistency.** Re-run 200 RFCs in differently composed batches. Identical at temperature 0; drift means a batching or caching bug. | no | W13 |
| 4 | **Obsoletes-chain consistency.** An RFC and the RFC obsoleting it are almost always about the same thing. Jaccard over all 1,543 `obs` and 2,156 `updates` pairs; read the bottom 50. Each is a genuine scope change worth knowing about or a tagging error. | reads 50 | W13 |
| 4b | **Producing-group coherence.** For each of the 173 groups with 10+ RFCs, entropy of assigned `topic/` tags. Scatter means mis-tagging or a genuinely broad charter, and `state_id` distinguishes a narrow concluded group from a live broad one. Exclude the non-group buckets. | reads outliers | W13, after gate 2 |
| 4c | **Charter agreement.** For each of the 544 charters, compare its documents' `topic/` tags against the charter text. Honest check because B never sees charters — A1 does. | reads outliers | W13, after gate 2 |
| 5 | **Notification volume.** For each tag compute the expected subscriber mail rate from the last five years of publications carrying it (198 RFCs/yr). This is what D1 sizes tags by; corpus counts do not measure it. Keep 15/1,500 corpus counts as a secondary browsability check. Expect reclassification: a tag on 400 RFCs all published before 1995 is a good browse category and a dead subscription. | reads flags | W13 |
| 6 | **Review queue.** Every `low` confidence result and every record with a `proposed_tags` entry. | yes | W13 |

Gates 4b and 4c must run *after* gate 2 and must never feed back into prompt B. B derives
tags independently of group and charter; that independence is what makes them checks
rather than circular reinforcement.

Every gate runs on Stage B's batch JSON joined to datatracker metadata, before or
independently of loading into reef. None of them needs reef to exist, so W13 is not
blocked on Q1 — which matters, because a gate failure should be caught before anything
is written to the system of record.

## 11. Running Stage B (W12, W15)

- 25 records per call, ~393 calls. Frozen `tags.yaml` in the system prompt on every call,
  prompt-cached; it is the bulk of the input.
- Temperature 0. Batches are independent — parallelise freely, but **no batch may see
  another batch's output**, or per-batch conventions diverge across the corpus.
- Order batches by RFC number so a reviewer sees coherent runs of related documents.
- Validate every response against the closed vocabulary before writing. A tag id outside
  `tags.yaml` is a failed batch, not a new tag — re-run once, then route to review.
- Write batch JSON as the reviewable artefact, then load into reef with a separate step,
  so a batch is re-runnable and revertible and a gate failure never reaches the system of
  record. Never write the store directly from the model call. The exact load format waits
  on Q1; the batch JSON in §11's schema is stable regardless.
- **Per-publication tagging** runs the same Prompt B against the frozen vocabulary with a
  batch of 1. That identity is the point — it is what keeps new RFCs consistent with the
  back catalogue — and it holds whoever invokes it, which is Q3.
- Wherever it runs, two constraints hold. An LLM call must never sit inside the
  publication transaction or be able to fail a publication: in the datatracker the RFC and
  its `published_rfc` event are created inside `transaction.atomic()` in
  `ietf/api/serializers_rpc.py`, so any tagging happens after commit. And the tags must
  land before reef notifies subscribers, or the first notification for a new RFC carries
  none.

## 12. Implementation notes

Reef owns the store (D6), so this plan writes little datatracker code. What it does write
is read-only extraction (W2) plus scripts (`baseline.py`, the W3 seed generator), which
need no models, no migrations and no API resources.

- **Version the vocabulary in reef**, since that is where it lives. `tags.yaml` carries
  `version`; reef needs to record which version produced a given tag→RFC map, or the
  "bump version, re-tag only what changed" rule in §13 has nothing to compare against.
- **If Q2 turns out to require datatracker storage** — a hint field, a cached map — then
  two things apply that are easy to miss: a new `ietf.doc` model needs a Tastypie resource
  registered (`ietf/name/resources.py:52` is the template; omitting it turns CI red while
  the feature's own tests stay green), and the datatracker's test runner needs whole
  module labels, not single-method ones.
- **Do not extend `ietf/community/tests.py` or its notification path.** Per D9 that code
  is not in scope, and a test asserting RFC events notify community-list subscribers would
  encode the wrong architecture.

## 13. After launch

`proposed_tags` accumulates the vocabulary's real gaps from live traffic. Batch them for
periodic review rather than acting on them singly. New tags are created in reef (D6), so
the review cycle ends there, not in this repo.

When the vocabulary changes, bump `version` in `tags.yaml` and re-run Stage B **only** for
tags that were added, split or redefined — a full re-tag churns every subscriber's feed.
That selective re-tag needs reef to know which version tagged what; see §12.

Extending tags to Internet-Drafts is the obvious follow-on request. Drafts, authors and
document history are all reachable from the same ORM; the record schema in §6 is the
piece that would need revisiting.

## 14. File inventory and artifact flow

| File | Role |
|---|---|
| `README.md` | This plan |
| `prompt-a1-seeded-taxonomy.md` | W5 — vocabulary from structure and charters, content unseen |
| `prompt-a2-inductive-taxonomy.md` | W6 — vocabulary induced from the 1,200-record sample, structure stripped |
| `prompt-a3-reconcile.md` | W7 — reconciles A1 and A2 into frozen `tags.yaml` |
| `prompt-b-tag-batch.md` | W12, W15 — tags 25 RFCs per call; also the per-publication tagger |
| `baseline.py` | W0 — re-measures every figure in §4. Invocation in §3 |
| `baseline-<date>.json` | W0 output, one per environment snapshot |
| `seed/structure.md` | W3 → A1. **Stale**: mirror-derived, no charters |
| `seed/keywords.md`, `seed/keywords-full.json` | W3 → A3, naming only. **Stale**: mirror-derived |
| `seed/build-seed.py` | Superseded mirror-based generator; reference shape for the W3 rewrite |
| `archive/` | Superseded working notes. Git-ignored, local only — not in the remote |

Execution runs in the container; this repo is how its output reaches reviewers. Push the
artefacts that carry a judgement, keep the bulk local:

| Artefact | Stage | Pushed for review? |
|---|---|---|
| `baseline-<date>.json` | W0 | yes — small, and it dates every figure in §4 |
| `records.jsonl` | W2 | no — ~9,800 records, and regenerable from the ORM in one pass |
| `sample-a2-rfc-numbers.txt` | W4 | yes — the committed sample identity, needed for reproducibility |
| `sample-a2.json` | W4 | no — regenerable from the numbers plus the snapshot date |
| `vocab-s.yaml`, `vocab-i.yaml` | W5, W6 | yes — A3's adjudication is only checkable against both inputs |
| `tags.yaml` | W7, W8 | **yes — this is what gate 1 reviews** |
| `gold.json` | W10 | yes — small, human-made, and the reference every later score depends on |
| `tags-batch-*.json` | W12 | no — ~393 files; reef is the destination and gate reports are the readable summary |
| Gate reports | W13 | yes |
