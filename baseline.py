"""W0 baseline: re-measure every corpus fact README.md section 4 depends on.

Needs the datatracker ORM, so it runs through that checkout's manage.py. This repo may
be cloned anywhere, so pass its location explicitly:

    TAGGING=/path/to/tagging
    cd /path/to/datatracker
    TAGGING_DIR=$TAGGING python ietf/manage.py shell -c "exec(open('$TAGGING/baseline.py').read())"

TAGGING_DIR may be omitted when the datatracker checkout has this repo at
tmp/tags/tagging, or when the shell's cwd is this repo.

Prints a report and writes baseline-<snapshot-date>.json into this repo. Every number in
README.md section 4 comes from here; re-run after any environment refresh — a rebuild, a
new DB snapshot, a re-sync of RFC_PATH — and update that section from the output.
"""

import json
import os
from collections import Counter

from django.conf import settings

from ietf.doc.models import Document, DocEvent, RelatedDocument
from ietf.group.models import Group

REAL_GROUP_TYPES = ("wg", "rg", "ag", "rag", "edwg")
MARKER = "prompt-b-tag-batch.md"  # identifies this repo's root


def find_output_dir():
    """This script is exec'd inside a Django shell, so __file__ is not available."""
    candidates = [
        os.environ.get("TAGGING_DIR"),
        os.getcwd(),
        os.path.join(os.getcwd(), "tmp", "tags", "tagging"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, MARKER)):
            return candidate
    raise SystemExit(
        "Cannot locate the tagging repo. Set TAGGING_DIR to its path and re-run."
    )


OUT_DIR = find_output_dir()


def area_acronym(doc):
    """Mirror of Document.area_acronym(). Do not substitute Document.area -- it
    returns None for non-IETF streams and for area-as-group docs, and resolves
    well under half the corpus. See README.md section 5 rule 1."""
    g = doc.group
    if not g:
        return None
    if g.type_id == "area":
        return g.acronym
    if g.type_id != "individ" and g.parent:
        return g.parent.acronym
    return None


def has_real_group(doc):
    return bool(doc.group and doc.group.type_id in REAL_GROUP_TYPES)


rfcs = list(
    Document.objects.filter(type_id="rfc").select_related(
        "group", "group__parent", "stream", "std_level"
    )
)
pub_year = {
    e.doc_id: e.time.year
    for e in DocEvent.objects.filter(type="published_rfc").order_by("time")
}
snapshot = max(
    DocEvent.objects.order_by("-time").values_list("time", flat=True)[:1]
).date().isoformat()

r = {"snapshot_date": snapshot, "rfc_count": len(rfcs)}

# --- abstracts and text ---
no_abstract = [d for d in rfcs if not d.abstract]
no_text = [d for d in no_abstract if not d.text_exists()]
r["abstract_present"] = len(rfcs) - len(no_abstract)
r["abstract_absent"] = len(no_abstract)
r["absent_but_text_available"] = len(no_abstract) - len(no_text)
r["neither_abstract_nor_text"] = sorted(d.rfc_number for d in no_text)
r["rfc_path"] = str(settings.RFC_PATH)
r["rfc_path_populated"] = sum(1 for d in rfcs if d.text_exists())
r["abstract_by_band"] = {}
for lo, hi in [(1, 1499), (1500, 2999), (3000, 5999), (6000, 99999)]:
    band = [d for d in rfcs if lo <= (d.rfc_number or 0) <= hi]
    r["abstract_by_band"][f"{lo}-{hi}"] = [
        sum(1 for d in band if d.abstract), len(band)
    ]

# --- structural distributions ---
r["streams"] = dict(Counter(d.stream_id for d in rfcs).most_common())
r["status"] = dict(Counter(d.std_level_id for d in rfcs).most_common())
r["decades"] = dict(
    sorted(Counter((pub_year.get(d.pk, 0) // 10) * 10 for d in rfcs).items())
)

areas = Counter(area_acronym(d) for d in rfcs)
r["area_unresolved"] = areas.pop(None, 0)
r["area_resolved"] = len(rfcs) - r["area_unresolved"]
r["areas"] = dict(sorted(areas.items(), key=lambda kv: -kv[1]))
r["area_unresolved_by_stream"] = dict(
    Counter(d.stream_id for d in rfcs if not area_acronym(d)).most_common()
)

groups = Counter(d.group.acronym for d in rfcs if has_real_group(d))
r["real_group_docs"] = sum(groups.values())
r["real_group_count"] = len(groups)
r["real_group_top"] = groups.most_common(6)
r["groups_with_one_rfc"] = sum(1 for v in groups.values() if v == 1)
r["groups_with_ten_plus"] = sum(1 for v in groups.values() if v >= 10)
r["no_real_group_docs"] = len(rfcs) - r["real_group_docs"]
r["no_real_group_breakdown"] = dict(
    Counter(
        d.group.type_id if d.group else "none"
        for d in rfcs
        if not has_real_group(d)
    ).most_common()
)

# --- the hard core: README.md section 4 rests on this nesting ---
r["no_abstract_and_no_area"] = sum(1 for d in no_abstract if not area_acronym(d))
r["no_abstract_and_no_real_group"] = sum(
    1 for d in no_abstract if not has_real_group(d)
)

# --- charters, the A1 seed input ---
charter_groups = Group.objects.filter(
    pk__in=[d.group_id for d in rfcs if has_real_group(d)], charter__isnull=False
).select_related("charter")
full = trunc = n = 0
for g in charter_groups:
    try:
        text = g.charter.text() or ""
    except Exception:
        text = ""
    if not text:
        continue
    n += 1
    full += len(text)
    paras = [p for p in text.split("\n\n") if p.strip()]
    trunc += len(" ".join(paras[:2])[:900])
r["charters"] = {
    "groups_with_charter_text": n,
    "full_tokens_approx": full // 4,
    "truncated_tokens_approx": trunc // 4,
}
r["group_states"] = dict(
    Counter(
        g.state_id for g in Group.objects.filter(pk__in={d.group_id for d in rfcs})
    ).most_common()
)

# --- author keywords, case-folded per README.md section 5 rule 3 ---
kw = Counter()
docs_with_kw = 0
for d in rfcs:
    vals = [k.strip().lower() for k in (d.keywords or []) if k and k.strip()]
    if vals:
        docs_with_kw += 1
    kw.update(vals)
r["keywords"] = {
    "instances": sum(kw.values()),
    "documents": docs_with_kw,
    "distinct_folded": len(kw),
    "hapax": sum(1 for v in kw.values() if v == 1),
    "at_least_20": sum(1 for v in kw.values() if v >= 20),
    "top": kw.most_common(8),
}

# --- relations and publication rate ---
r["relations"] = dict(
    Counter(
        rd.relationship_id
        for rd in RelatedDocument.objects.filter(
            source__type_id="rfc", relationship_id__in=("obs", "updates")
        )
    ).most_common()
)
by_year = Counter(y for y in pub_year.values() if y)
recent = {y: by_year[y] for y in range(2021, 2026)}
r["publications_by_year_recent"] = recent
r["publications_per_year_mean_5y"] = round(sum(recent.values()) / len(recent), 1)

# --- report ---
print(f"snapshot {r['snapshot_date']}   RFCs {r['rfc_count']}")
print(
    f"abstract: {r['abstract_present']} present, {r['abstract_absent']} absent; "
    f"of those absent, {r['absent_but_text_available']} have text"
)
print(f"  RFC_PATH={r['rfc_path']}  text reachable for {r['rfc_path_populated']} RFCs")
print(f"  neither abstract nor text: {r['neither_abstract_nor_text']}")
print(
    f"area: {r['area_resolved']} resolved "
    f"({100 * r['area_resolved'] / r['rfc_count']:.1f}%), "
    f"{r['area_unresolved']} unresolved"
)
print(
    f"group: {r['real_group_docs']} in {r['real_group_count']} real groups; "
    f"{r['no_real_group_docs']} "
    f"({100 * r['no_real_group_docs'] / r['rfc_count']:.1f}%) with none"
)
print(
    f"HARD CORE: of {r['abstract_absent']} abstract-less, "
    f"{r['no_abstract_and_no_area']} also lack an area and "
    f"{r['no_abstract_and_no_real_group']} also lack a group"
)
print(f"charters: {r['charters']}")
print(f"keywords: {r['keywords']['distinct_folded']} distinct folded, "
      f"{r['keywords']['at_least_20']} at 20+")
print(f"publication rate: {r['publications_per_year_mean_5y']}/yr {recent}")

path = os.path.join(OUT_DIR, f"baseline-{snapshot}.json")
with open(path, "w") as fh:
    json.dump(r, fh, indent=2, sort_keys=True)
print(f"\nwrote {path}")
