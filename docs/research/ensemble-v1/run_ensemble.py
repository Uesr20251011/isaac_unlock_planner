"""Reproduce the formula trial using only explicitly selected, mapped evidence."""
import argparse
import copy
import csv
import json
import itertools
from pathlib import Path
import re
import time
import numpy as np
from ensemble_model import assemble_sources,fit_model,model_scores,rank_summary,relative_tiers

HERE=Path(__file__).resolve().parent
PROJECT=next((parent for parent in HERE.parents if (parent/'tools/community_rankings.json').is_file()),None)


def create_inputs():
    if PROJECT is None:
        raise ValueError('Use --inputs ensemble-inputs-v1.json outside the project repository')
    data=json.loads((PROJECT/'tools/community_rankings.json').read_text('utf-8'))
    items=[item for item in data['entries'] if item['collectibleId'] is not None]
    normalize=lambda value:re.sub('[^a-z0-9]','',value.lower().replace('(Item)',''))
    by_name={normalize(item['name']):item['collectibleId'] for item in items}
    angel=['The Stairway','Spirit Sword','Sacred Heart','The Wafer','Revelation','Godhead',
           'Sacred Orb','Book of Revelations','Holy Mantle','Star of Bethlehem','Crown of Light','Trisagion']
    sources=[dict(id='unduel-20261028',family='unduel',basis='strength',quality=.8,relevance=1.,version=.6,
                  published='2026-10-28',scope='global',url=data['sourceUrl'],
                  note='Verified719-row original snapshot;718 mapped entities; patch unspecified Repentance; vote records are not game outcomes.',
                  entries=[dict(id=item['collectibleId'],level=item['rank'],votes=item['itemVoterCount']) for item in items]),
             dict(id='anothermatt-angel-s-20250607',family='anothermatt',basis='strength',quality=.75,relevance=1.,version=.6,
                  published='2025-06-07',scope='verified internal order of12 Angel S-tier slides only',
                  url='https://www.youtube.com/watch?v=89UIC_l02Nk',
                  note='Do not infer positions or tiers for any other item. Same author as any BY THEIR UNLOCKS spreadsheet.',
                  entries=[dict(id=by_name[normalize(name)],level=i+1) for i,name in enumerate(angel)])]
    extra=HERE/'ensemble-sources-extra.json'
    if extra.exists(): sources.extend(json.loads(extra.read_text('utf-8')))
    inputs=dict(date='2026-11-04',status='formula trial; global multi-source coverage must be audited per item',
                universe=[dict(id=item['collectibleId'],name=item['name'],nameZh=item['nameZh'],originalRank=item['rank']) for item in items],
                excluded=[item for item in data['entries'] if item['collectibleId'] is None],sources=sources)
    (HERE/'ensemble-inputs-v1.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2),'utf-8')
    return inputs


def run(inputs,sources=None,reg=.03,initial=None,sample_half=50,coverage_power=.5):
    sources=inputs['sources'] if sources is None else sources
    ids=[item['id'] for item in inputs['universe']]
    c,t,audit=assemble_sources(sources,ids,sample_half=sample_half,coverage_power=coverage_power)
    if len(audit['observedIds'])!=len(ids) or len(audit['components'])!=1:
        return None,audit
    fit=fit_model(c,t,reg=reg,initial=initial)
    if not fit['converged']: raise RuntimeError(f"Model did not converge: {fit['gradientMax']}")
    scores=model_scores(fit['theta'])
    ranks,low,high=rank_summary(fit['theta'])
    result=dict(theta=fit['theta'],scores=scores,ranks=ranks,rankLow=low,rankHigh=high,
                iterations=fit['iterations'],gradientMax=fit['gradientMax'],regularization=reg)
    return result,audit


def source_agreements(sources):
    rows=[]
    for first,second in itertools.combinations(sources,2):
        if first['family']==second['family']: continue
        a={entry['id']:entry['level'] for entry in first['entries']}
        b={entry['id']:entry['level'] for entry in second['entries']}
        common=sorted(set(a)&set(b)); compared=agree=0
        for i,j in itertools.combinations(common,2):
            if a[i]==a[j] or b[i]==b[j]:continue
            compared+=1;agree+=((a[i]<a[j])==(b[i]<b[j]))
        rows.append(dict(first=first['id'],second=second['id'],commonItems=len(common),
                         comparablePairs=compared,agreeingPairs=agree,
                         agreement=agree/compared if compared else None))
    return rows


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--sensitivity',action='store_true')
    parser.add_argument('--inputs',type=Path,help='Use a frozen input snapshot rather than importing the local project')
    args=parser.parse_args()
    started=time.monotonic()
    inputs=json.loads(args.inputs.read_text('utf-8')) if args.inputs else create_inputs()
    base,audit=run(inputs)
    if base is None: raise RuntimeError('No connected global comparison graph; refuse to fabricate an all-item ordering')
    families=sorted({source['family'] for source in inputs['sources']})
    scenarios=[]; holdouts=[]; single_source_audits=[]
    for family in families:
        result,remaining=run(inputs,[source for source in inputs['sources'] if source['family']==family])
        entry=dict(family=family,globalComparable=result is not None,
                   observedItems=len(remaining['observedIds']),components=len(remaining['components']))
        if result is not None:
            source_order=np.argsort([item['originalRank'] for item in inputs['universe']])
            expected=np.empty(len(source_order),dtype=int);expected[source_order]=np.arange(1,len(source_order)+1)
            difference=np.abs(result['ranks']-expected)
            entry.update(comparisonBaseline='declared canonical universe ordered by original Unduel position',
                         changedPositions=int((difference>0).sum()),maxRankChange=float(difference.max()))
        single_source_audits.append(entry)
    if args.sensitivity:
        for family in families:
            for multiplier in [.75,1.25]:
                sources=copy.deepcopy(inputs['sources'])
                for source in sources:
                    if source['family']==family: source['weightMultiplier']=multiplier
                result,_=run(inputs,sources,initial=base['theta'])
                if result: scenarios.append((f'{family} weight x{multiplier}',result))
        for reg in [.01,.1]:
            result,_=run(inputs,reg=reg,initial=base['theta']); scenarios.append((f'regularization {reg}',result))
        for sample_half in [25,100]:
            result,_=run(inputs,sample_half=sample_half,initial=base['theta']); scenarios.append((f'sample half {sample_half}',result))
        result,_=run(inputs,coverage_power=1.,initial=base['theta']); scenarios.append(('linear coverage discount',result))
        for family in families:
            result,remaining=run(inputs,[source for source in inputs['sources'] if source['family']!=family],initial=base['theta'])
            holdouts.append(dict(removedFamily=family,globalComparable=result is not None,
                                 observedItems=len(remaining['observedIds']),components=len(remaining['components']),
                                 maxRankChange=float(np.abs(result['ranks']-base['ranks']).max()) if result else None))
            if result: scenarios.append((f'leave out {family}',result))
    rows=[]
    for i,item in enumerate(inputs['universe']):
        family_mass={family:float(masses[i]) for family,masses in audit['familyItemMass'].items() if masses[i]>0}
        positions=[int(base['rankLow'][i]),int(base['rankHigh'][i])]+[int(value) for _,result in scenarios for value in (result['rankLow'][i],result['rankHigh'][i])]
        relative_tier='/'.join(relative_tiers(base['rankLow'][i],base['rankHigh'][i],len(inputs['universe'])))
        scenario_tiers=[]
        for _,result in scenarios:
            scenario_tiers.append('/'.join(relative_tiers(result['rankLow'][i],result['rankHigh'][i],len(inputs['universe']))))
        rows.append(dict(**item,rank=float(base['ranks'][i]),rankLow=int(base['rankLow'][i]),rankHigh=int(base['rankHigh'][i]),score=round(float(base['scores'][i]),4),theta=float(base['theta'][i]),
                         relativeTier=relative_tier,sourceFamilies=list(family_mass),familyCount=len(family_mass),
                         familyMass=family_mass,weightScenarioRankMin=min(positions),weightScenarioRankMax=max(positions),
                         tierStability=(sum(tier==relative_tier for tier in scenario_tiers)/len(scenario_tiers)) if scenario_tiers else None,
                         possibleTiers=sorted(set('/'.join(scenario_tiers+[relative_tier]).split('/')),key='SABCDF'.index),
                         note='single-source estimate' if len(family_mass)<2 else 'multi-source comparison evidence; not calibrated gameplay performance'))
    rows.sort(key=lambda row:row['rank'])
    output=dict(date=inputs['date'],status=inputs['status'],model='source-capped regularized pairwise preference',
                parameters=dict(regularization=.03,sampleHalf=50,coveragePower=.5,tieTolerance=1e-8),
                total=len(rows),familyCount=len(families),multipleSourceItems=sum(row['familyCount']>1 for row in rows),
                sourceAudit=audit['sources'],redundantSources=audit['redundantSources'],
                sourceAgreements=source_agreements(inputs['sources']),
                singleSourceAudits=single_source_audits,holdouts=holdouts,
                sensitivityScenarios=[name for name,_ in scenarios],
                scenarioDiagnostics=[dict(name=name,iterations=result['iterations'],gradientMax=result['gradientMax'],
                                          maxRankChange=float(np.abs(result['ranks']-base['ranks']).max()),
                                          rankCorrelation=float(np.corrcoef(result['ranks'],base['ranks'])[0,1]))
                                     for name,result in scenarios],
                convergence={key:base[key] for key in ['iterations','gradientMax','regularization']},
                seconds=round(time.monotonic()-started,3),entries=rows)
    (HERE/'ensemble-results-v1.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),'utf-8')
    columns=['rank','rankLow','rankHigh','id','name','nameZh','score','relativeTier','familyCount','weightScenarioRankMin','weightScenarioRankMax','originalRank','note']
    with (HERE/'ensemble-results-v1.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=columns,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({key:output[key] for key in ['total','familyCount','multipleSourceItems','convergence','seconds']},ensure_ascii=True))
    print(json.dumps([{key:row[key] for key in ['rank','name','score','familyCount']} for row in rows[:12]],ensure_ascii=True))


if __name__=='__main__': main()
