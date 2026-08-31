# Plan: initial RFC subject-tag vocabulary and corpus tagging

Status 2026-08-31: nothing generated yet. No vocabulary exists, no RFC is tagged. The
pipeline below is specified and reviewed; the prompts in this directory are written and
current. Execution starts at W0.

Figures throughout come from the datatracker dev environment, DB snapshot 2026-08-19,
`/assets/ietf-ftp/rfc/` populated (9,833 `.txt`, 9,827 `.html`, 1,371 `.xml`,
10,023 `.json`). Re-measure at W0 against the environment you actually run on.

---

## 1. Objective

rfc-editor.org is adding subscription: a logged-in user subscribes to a tag and is
notified of events on RFCs carrying it — above all the publication of a new RFC.
Deliver two things:

1. A frozen subject-tag vocabulary, `tags.yaml`.
2. That vocabulary applied to every published RFC, and to each new RFC at publication.

**Subscription is the governing constraint.** A wrong tag mails people who did not want
it; a missing tag silently fails someone who did. Two consequences bind every stage:
tags are sized by notification volume rather than conceptual tidiness, and the prompt
that tags the back catalogue must be the same prompt that tags each new RFC, or the two
drift apart.

## 2. Fixed decisions

Made by the RFC Editor. Do not relitigate.

| # | Decision |
|---|---|
| D1 | **Faceted vocabulary, 125–185 tags**: `topic/` 25–35 broad subject areas, `tech/` 90–140 named protocols and technologies, `kind/` 8–12 document roles. Not a flat ~40 (too noisy to subscribe to), not a flat ~400 (unbrowsable). |
| D2 | **Derive the vocabulary twice and reconcile**: once top-down from IETF structure, once bottom-up from document content, then adjudicate. Both, not one. |
| D3 | **Tag from title + abstract + metadata.** Not full text, not titles alone. |
| D4 | **The deliverable is prompts plus a run harness**, not a built pipeline. |
| D5 | **Author-supplied keywords are not candidate tags.** They are uncurated author self-labelling; the vocabulary must be better curated than they are. Admitted for naming and aliases only. |

Settled against the datatracker; confirm with the RFC Editor at W1 but proceed on these:

| # | Decision |
|---|---|
| D6 | **New model, new name.** `RfcTagName(NameModel)` in `ietf/name/models.py` with `facet` (`topic`/`tech`/`kind`) and `aliases`; `Document.rfc_tags = M2M(RfcTagName)`. Do **not** reuse `Document.tags`/`DocTagName` (all 33 rows are workflow substates such as `need-rev`, `ad-f-up`, `missref`; `ietf/doc/models.py:441` reads them as `iesg_substate`). Do **not** reuse `Document.keywords` (that field holds the author keywords D5 excludes). Say "subject tag" in code and UI; reserve "tag" for `DocTagName`. |
| D7 | **The datatracker owns the tags.** `ietf/sync/rfcindex.py` *generates* `rfc-index.xml` from the ORM and publishes it to the red bucket and `RFC_PATH`; rfc-editor.org consumes it. Tags live in the datatracker and export through `add_rfc_xml_index_entries` as an additive optional `<tags>` element. Budget for coordinating an `rfc-index.xsd` change with external consumers. |
| D8 | **Subscription reuses the community-list machinery.** `CommunityList` → `SearchRule` → `EmailSubscription` already carries `group_rfc`, `area_rfc` and `author_rfc` rule types, and `community_list_rules_matching_doc` handles `type_id == "rfc"`. Add a `tag_rfc` rule type. Do not build a parallel subscription store on rfc-editor.org. |
| D9 | **Fix the notification guard, do not work around it.** `ietf/community/signals.py` returns early unless `event.doc.type_id == "draft"`, so all 9,828 `published_rfc` events are dropped today and RFC subscription rules mail nobody. Widen the guard and define what "significant" means for an RFC (`states_of_significant_change()` is all draft states). |

## 3. Environment

| Resource | Value |
|---|---|
| Metadata | Datatracker ORM. `Document.objects.filter(type_id="rfc")` |
| Document text | `/assets/ietf-ftp/rfc/` = `settings.RFC_PATH`, reached as `doc.text(n)` |
| Charters | `settings.CHARTER_PATH`, reached as `group.charter.text()` |
| Working dir | this directory; prompts, seed inputs, run outputs |

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
| **W0** | Baseline. Re-measure §4 against the live environment; run `text_exists()` across the abstract-less set; record the snapshot date. | — | `baseline-<date>.json`, §4 updated |
| **W1** | Confirm D6–D9 with the RFC Editor. | W0 | Naming and ownership settled |
| **W2** | Record builder: one ORM pass emitting §6 records. | W0 | `build_records.py`, `records.jsonl` |
| **W3** | Seed generation: `seed/structure.md` (see §8), `seed/keywords.md`, `seed/keywords-full.json`. | W2 | 3 seed files |
| **W4** | A2 sample: draw and commit per §9. | W2 | `sample-a2.json` + committed RFC numbers + snapshot date |
| **W5** | Run A1 (`prompt-a1-seeded-taxonomy.md`). Isolated session. | W3 | `vocab-s.yaml` |
| **W6** | Run A2 (`prompt-a2-inductive-taxonomy.md`). Isolated session, stripped records. | W4 | `vocab-i.yaml` |
| **W7** | Run A3 (`prompt-a3-reconcile.md`). | W5, W6 | `tags.yaml` draft + `review_queue` |
| **W8** | **Human review of `tags.yaml`.** Gate 1. Ordered `review_queue` first. | W7 | Frozen `tags.yaml` v1.0.0 |
| **W9** | Plumbing, in parallel from W1: `RfcTagName` + `Document.rfc_tags` + migration; Tastypie resources; `tag_rfc` `SearchRule`; widen the `signals.py` guard; `<tags>` in the index generator behind a flag; batch-loader management command. | W1 | Merged, tested |
| **W10** | Gold set: human-tag 150 RFCs drawn across eras. | W8 | `gold.json` |
| **W11** | Score B against gold. Gate 2. Below ~0.75 F1, fix the prompt or the vocabulary and repeat — do not proceed intending to clean up later. | W9, W10 | Score report |
| **W12** | Stage B full run: ~393 batches of 25. | W11 | `tags-batch-*.json`, loaded to DB |
| **W13** | Gates 3, 4, 4b, 4c, 5, 6 (§10). | W12 | Gate reports, review queue |
| **W14** | Enable export and subscription; announce. | W13 | Live |
| **W15** | Ongoing: per-publication tagging hook (§11); `proposed_tags` review cycle. | W14 | — |

W10 is the main piece of human work and nothing downstream substitutes for it. W8 is the
only gate that is genuinely expensive to skip: a vocabulary error costs a full re-tag.

## 8. Seed generation (W3)

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

## 11. Running Stage B (W12, W15)

- 25 records per call, ~393 calls. Frozen `tags.yaml` in the system prompt on every call,
  prompt-cached; it is the bulk of the input.
- Temperature 0. Batches are independent — parallelise freely, but **no batch may see
  another batch's output**, or per-batch conventions diverge across the corpus.
- Order batches by RFC number so a reviewer sees coherent runs of related documents.
- Validate every response against the closed vocabulary before writing. A tag id outside
  `tags.yaml` is a failed batch, not a new tag — re-run once, then route to review.
- Write batch JSON as the reviewable artefact; load to `Document.rfc_tags` with the
  management command, so a batch is re-runnable and revertible. Do not write the DB from
  the model call.
- **Per-publication tagging** hooks the RPC publication path, not a cron over the index.
  `ietf/api/serializers_rpc.py` creates the RFC and its `published_rfc` event inside
  `transaction.atomic()`. Tag in a Celery task **after that transaction commits** — an
  LLM call must never hold a write transaction or be able to fail a publication — and
  before the subscriber notification fires, or the first mail for a new RFC carries no
  tags. Mirror `ietf/community/tasks.py`.

## 12. Implementation notes for this codebase

- **A new `ietf.doc` model needs a Tastypie resource.** Registering `RfcTagName` and the
  M2M in `ietf/name/resources.py` and `ietf/doc/resources.py` is not optional — omitting
  it turns CI red while the feature's own tests stay green. Copy `DocTagNameResource`
  (`ietf/name/resources.py:52`).
- **Run whole test modules, not single-method labels.** `ietf/community/tests.py`,
  `ietf/doc/tests.py`.
- `ietf/community/tests.py` already covers `notify_event_to_subscribers` and its task
  wrapper. Extend those when the D9 guard changes and add a case asserting that an RFC
  `published_rfc` event notifies.
- Load the frozen vocabulary as a **data migration**, so `tags.yaml`'s `version` is
  tracked in schema history and the "bump version, re-tag only changed tags" rule has an
  anchor.
- Add an `RfcTagName` factory in `ietf/doc/factories.py`.

## 13. After launch

`proposed_tags` accumulates the vocabulary's real gaps from live traffic. Batch them for
periodic review rather than acting on them singly. When the vocabulary changes, bump
`version` in `tags.yaml` and re-run Stage B **only** for tags that were added, split or
redefined — a full re-tag churns every subscriber's feed.

Extending tags to Internet-Drafts is the obvious follow-on request. Drafts, authors and
document history are all reachable from the same ORM; the record schema in §6 is the
piece that would need revisiting.

## 14. File inventory

| File | Role |
|---|---|
| `README.md` | This plan |
| `prompt-a1-seeded-taxonomy.md` | W5 — vocabulary from structure and charters, content unseen |
| `prompt-a2-inductive-taxonomy.md` | W6 — vocabulary induced from the 1,200-record sample, structure stripped |
| `prompt-a3-reconcile.md` | W7 — reconciles A1 and A2 into frozen `tags.yaml` |
| `prompt-b-tag-batch.md` | W12, W15 — tags 25 RFCs per call; also the per-publication tagger |
| `seed/structure.md` | W3 → A1 |
| `seed/keywords.md`, `seed/keywords-full.json` | W3 → A3, naming only |
| `archive/` | Superseded working notes, kept for provenance |
