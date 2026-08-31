#!/usr/bin/env python3
"""SUPERSEDED at W3 -- kept for reference, do not run to produce inputs.

This regenerates seed/ from the static corpus mirror at ../../rfc/, which the plan has
retired: it does not exist in a standalone clone of this repo, and the datatracker is now
the source for every field it reads. It also cannot produce the charter excerpts,
group type or group state that Prompt A1 now expects.

Replace it with an ORM-based generator per README.md section 8. Kept because its output
shape -- one block per group, streams and areas with counts -- is the shape to reproduce.
"""
import json, glob, re, collections, os

RFC = os.path.join(os.path.dirname(__file__), '..', '..', 'rfc')
OUT = os.path.dirname(__file__)

# per-RFC JSON: full group name in `source`, 100% coverage, published RFCs only
J = {}
for f in glob.glob(os.path.join(RFC, 'rfc[0-9]*.json')):
    d = json.load(open(f))
    m = re.match(r'RFC(\d+)$', d.get('doc_id') or '')
    if m and d.get('pub_date'):          # skips the 188 not-issued stubs
        J[int(m.group(1))] = d

# index XML: area and stream, which the JSON does not carry
xml = open(os.path.join(RFC, 'rfc-index.xml'), encoding='utf-8', errors='replace').read()
X = {}
for e in re.findall(r'<rfc-entry>(.*?)</rfc-entry>', xml, re.S):
    n = int(re.search(r'<doc-id>RFC(\d+)</doc-id>', e).group(1))
    g = lambda t: (re.search(r'<%s>(.*?)</%s>' % (t, t), e, re.S).group(1).strip()
                   if re.search(r'<%s>' % t, e) else None)
    X[n] = {'area': g('area'), 'wg': g('wg_acronym'), 'stream': g('stream')}

rows = collections.defaultdict(lambda: {'n': 0, 'areas': collections.Counter(),
                                        'acr': collections.Counter()})
A = collections.Counter(); S = collections.Counter(); K = collections.Counter()
for n, d in J.items():
    x = X.get(n, {}); r = rows[d['source']]; r['n'] += 1
    if x.get('area'):   r['areas'][x['area']] += 1; A[x['area']] += 1
    if x.get('stream'): S[x['stream']] += 1
    if x.get('wg') and x['wg'] != 'NON WORKING GROUP': r['acr'][x['wg']] += 1
kw_docs = 0
for e in re.findall(r'<rfc-entry>(.*?)</rfc-entry>', xml, re.S):
    kws = re.findall(r'<kw>(.*?)</kw>', e, re.S)
    if kws: kw_docs += 1
    for k in kws: K[k.strip().lower()] += 1

BUCKETS = ('Legacy', 'IETF - NON WORKING GROUP', 'INDEPENDENT', 'IAB')
bucket_n = sum(rows[b]['n'] for b in BUCKETS if b in rows)

with open(os.path.join(OUT, 'structure.md'), 'w') as o:
    o.write(f"""# Empirical structure of the RFC corpus

Joined from `../rfc/rfc-index.xml` (area, stream, working-group acronym) and the
per-RFC `../rfc/rfcNNNN.json` files (`source` — the working group's **full name**,
100% coverage). Counts are published documents; not-issued numbers are excluded.
Regenerate with `python3 seed/build-seed.py`.

The `source` field mixes levels: "Legacy", "INDEPENDENT", "IAB" and
"IETF - NON WORKING GROUP" are streams or catch-alls, while the rest are named
working and research groups. Together those four buckets hold {bucket_n:,} documents —
just over a third of the corpus, with no working group to inherit a tag from.

## Streams (from XML, 100% coverage of published RFCs)

""" + "\n".join(f"- `{k}` — {v}" for k, v in S.most_common()) + f"""

## Areas (from XML, {100*sum(A.values())/len(J):.1f}% coverage; includes retired area codes)

""" + "\n".join(f"- `{k}` — {v}" for k, v in A.most_common()) + """

## Groups and buckets by document count

Format: full name — count · `acronym` · dominant area

""")
    for k, r in sorted(rows.items(), key=lambda kv: -kv[1]['n']):
        acr = r['acr'].most_common(1); ar = r['areas'].most_common(1)
        o.write(f"- {k} — {r['n']}" + (f" · `{acr[0][0]}`" if acr else "")
                + (f" · {ar[0][0]}" if ar else "") + "\n")

k20 = [(k, v) for k, v in K.most_common() if v >= 20]
hapax = sum(1 for v in K.values() if v == 1)
with open(os.path.join(OUT, 'keywords.md'), 'w') as o:
    o.write(f"""# Author-supplied keywords, frequency-ranked

From `<kw>` in `../rfc/rfc-index.xml`: {sum(K.values()):,} instances across {kw_docs:,}
documents ({100*kw_docs/len(J):.1f}% of published RFCs), {len(K):,} distinct strings.
Regenerate with `python3 seed/build-seed.py`.

**These are not candidate tags and must never be used as any.** They are uncurated
author self-labelling, held to no consistency standard, and the tag set being built
here has to be considerably better curated than they are. This file has exactly one
job: settling what an already-selected tag should be *called*, and supplying aliases
for search.

Only 18% of keyword instances are fully contained in their document's own title, so
these are largely genuine author labelling rather than title restatement — which is
what makes them useful as naming evidence. But the distribution is extreme: {hapax:,} of
{len(K):,} strings occur exactly once, and the highest-frequency band is contaminated
with generic title words (`protocol`, `internet`, `network`, `base`, `simple`,
`transfer`) and with fragments of expanded acronyms (`management information base`,
`multipurpose`). Rank here measures how often authors typed a word, not how coherent
a subject it is.

## The {len(k20)} strings occurring 20 or more times

""" + "\n".join(f"- {k} — {v}" for k, v in k20) + "\n")

json.dump(dict(K), open(os.path.join(OUT, 'keywords-full.json'), 'w'), indent=0)
print(f"published={len(J)} groups+buckets={len(rows)} bucket_docs={bucket_n} "
      f"kw_instances={sum(K.values())} kw_docs={kw_docs} kw_distinct={len(K)} "
      f"kw>=20={len(k20)} hapax={hapax}")
