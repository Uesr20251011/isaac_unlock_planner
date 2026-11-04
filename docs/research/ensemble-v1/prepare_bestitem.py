"""Map the saved original Best Item snapshot without treating site IDs as game IDs."""
import collections
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent


def main():
    raw_path=HERE/'english-ensemble-bestitem-ranking-raw.json'
    raw=json.loads(raw_path.read_text('utf-8'))
    catalogue=json.loads((HERE/'ensemble-inputs-v1.json').read_text('utf-8'))['universe']
    universe={row['id']:row for row in catalogue}
    normalize=lambda name:re.sub('[^a-z0-9]','',name.lower().replace('(item)',''))
    by_name=collections.defaultdict(list)
    for cid,row in universe.items(): by_name[normalize(row['name'])].append(cid)
    # Explicit spelling / part-name equivalences to the canonical collectible entity.
    aliases={
        'Humbling Bundle':(203,'EID canonical spelling Humbleing Bundle'),
        'Odd Mushroom (fat)':(121,'large mushroom variant, not thin variant C120'),
        'Broken Shovel 1 (handle)':(550,'active handle; separate head C551 is excluded below'),
        'Broken Shovel 2 (head)':(551,'second passive quest piece, outside this 718-item universe'),
        'Knife Piece 1 (handle)':(626,'first knife piece, canonical C626'),
        'Knife Piece 2 (blade)':(627,'second knife piece, canonical C627'),
        'Glass Cannon (broken)':(474,'broken state C474, not intact Glass Cannon C352'),
        'Key Piece 1 (loop end)':(238,'first key piece'),
        'Key Piece 2 (tooth end)':(239,'second key piece'),
        "Blue Baby's Only Friend":(320,"canonical ???'s Only Friend"),
        'Number Two':(378,'canonical No. 2'),
    }
    rows=[dict(row,segment=segment) for segment,entries in raw.items() for row in entries]
    assert set(raw)=={'best','worst'} and all(len(v)==200 for v in raw.values())
    assert len({row['id'] for row in rows})==len(rows)==400
    assert len({row['name'] for row in rows})==400
    mapped=[]; excluded=[]; audit=[]
    for row in rows:
        matches=by_name.get(normalize(row['name']),[])
        if row['name'] in aliases: cid,reason=aliases[row['name']]
        elif len(matches)==1: cid,reason=matches[0],'unique normalized name within the declared canonical universe'
        else: raise ValueError(f"Unresolved original name: {row['name']!r}: {matches}")
        record=dict(platformId=row['id'],originalName=row['name'],rawScore=row['score'],
                    segment=row['segment'],collectibleId=cid,mappingReason=reason)
        if cid not in universe:
            record['excludedReason']='outside declared universe; retain raw record, do not map a second shovel piece onto the handle'
            excluded.append(record)
        else:
            mapped.append(dict(id=cid,level=-row['score']))
            record['canonicalName']=universe[cid]['name']
        audit.append(record)
    assert len({entry['id'] for entry in mapped})==len(mapped)
    metadata=json.loads((HERE/'english-ensemble-bestitem-api-metadata.json').read_text('utf-8'))
    source=dict(id='bestitem-20261104',family='bestitem',basis='strength',quality=.65,
                relevance=1.,version=.6,published='2026-11-04',
                scope='only observed best200 and worst200; identical scores are unordered',
                url='https://bestitem.onrender.com/',apiUrl=metadata['url'],retrievedAt=metadata['retrievedAt'],
                note='Platform IDs are not collectible IDs. No sample/exposure counts or scoring algorithm exposed. No vote was submitted. Unshown items provide no comparison evidence. Damocles maps to the normal collectible C577, not its hidden activated state C656.',
                entries=mapped)
    (HERE/'ensemble-sources-extra.json').write_text(json.dumps([source],ensure_ascii=False,indent=2),'utf-8')
    output=dict(source=source['id'],rawSha256=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                retrievedAt=metadata['retrievedAt'],originalRows=len(rows),mappedRows=len(mapped),
                excluded=excluded,scoreCounts=dict(sorted(collections.Counter(row['score'] for row in rows).items())),
                note='No exposure counts are inferred from raw score. Equal raw scores do not create internal order.',
                mappings=audit)
    (HERE/'bestitem-mapping-audit.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({key:output[key] for key in ['originalRows','mappedRows','excluded','rawSha256']},ensure_ascii=True))


if __name__=='__main__':main()
