#!/usr/bin/env python3
"""Build transparent unlock suggestions from frozen strength and resource evidence."""
from __future__ import annotations
import collections
import hashlib
import heapq
import json
import math
from pathlib import Path
import re
import argparse
from build_recommendation_profiles import ROOT,read_data,read_json
from crawl_effects import MULTI_REWARD_BUNDLES

TOOLS=ROOT/'tools'
ENSEMBLE=ROOT/'docs/research/ensemble-v1/ensemble-results-v1.json'
HISTORY=TOOLS/'unlock_resource_references.json'
REVIEWS=TOOLS/'unlock_plan_reviews.json'
OUT=TOOLS/'unlock_plan.json'
RESOURCE_TYPES={'trinket','card','rune','soulstone','pill','pickup','interactive'}
TYPE_LABELS={'collectible':'收藏道具','trinket':'饰品','card':'卡牌','rune':'符文','soulstone':'魂石',
             'pill':'胶囊','pickup':'特殊掉落','interactive':'互动资源','character':'角色',
             'starting':'起始能力','route':'路线 / 机制','completion':'完成类目标'}
PHASE_NAMES={0:'并行与累计准备',1:'主线开放与早期补强',2:'常规打标与资源补强',3:'困难角色与深层目标',4:'终盘与全成就清单'}
MARKS={'Boss Rush':['boss-rush'],"Mom's Heart":['moms-heart'],'Hush':['hush'],'Isaac':['isaac-boss'],
       'Satan':['satan'],'???':['blue-baby'],'The Lamb':['lamb'],'Mega Satan':['mega-satan'],
       'Delirium':['delirium'],'Mother':['mother'],'The Beast':['beast'],'Ultra Greed':['greed'],
       'Ultra Greedier':['greedier'],'Isaac, ???, Satan, Lamb':['isaac-boss','blue-baby','satan','lamb'],
       'Boss Rush & Hush':['boss-rush','hush']}
TIER_UTILITY={'GOD':90,'GOOD':75,'MILD':55,'BAD':30,'SHIT':15}
CHARACTER_EFFORT={'The Lost':25,'Keeper':18,'Jacob and Esau':25,'Tainted Lost':45,
                  'Tainted Jacob':40,'Tainted Lazarus':35,'Tainted Cain':30,'Tainted Eden':15}
BOSS_EFFORT={'moms-heart':12,'isaac-boss':18,'satan':18,'blue-baby':24,'lamb':24,
             'boss-rush':25,'hush':30,'mega-satan':35,'delirium':42,'mother':35,'beast':30,
             'greed':20,'greedier':38}
SPECIAL_INTERACTIVE={243,247,323,406,593,601,604,605,607,608,609,611,612,614,616,617}
SPECIAL_PICKUPS={224,226,240,242,328,333,391,411,613,615}
PROGRESSION_TARGETS={5,16,17,18,33,66,68,86,87,88,142,151,152,153,154,155,246,275,337,341,342,343,344,345,347,348,412,413,414,641}
STARTING={191,236,237,248,250,331,332,334}
NORMAL_UNLOCKS={'Magdalene':1,'Cain':2,'Judas':3,'???':32,'Eve':42,'Samson':67,'Azazel':79,
                'Lazarus':80,'Eden':81,'The Lost':82,'Lilith':199,'Keeper':251,'Apollyon':340,
                'The Forgotten':390,'Bethany':404,'Jacob and Esau':405}


def priority_score(benefit,effort,*,future=1.,gateway=0.,risk=0.):
    if not all(math.isfinite(v) for v in [benefit,effort,future,gateway,risk]) or not 0<=benefit<=100 or effort<0 or not 0<=future<=1 or gateway<0 or risk<0:
        raise ValueError('Invalid unlock benefit/cost input')
    return round(max(0.,min(100.,benefit*future/(1+effort/100)+gateway-risk)),4)


def normalize(value):return re.sub(r'[^a-z0-9?]','',value.lower().replace('the ','').replace('&','and'))


def historical_targets(raw,unlocks):
    characters={normalize(c['nameEn']):c['id'] for c in unlocks['characters']}
    characters['taintedjacobandesau']='c33-tainted-jacob'
    rules={(r['characterId'],tuple(sorted(r['bossIds']))):r['achievementId'] for r in unlocks['unlockRules']}
    result={}
    for entry in raw['entries']:
        if entry['unlockMarkRaw']=='All Marks':continue
        character=characters.get(normalize(entry['character']))
        aid=rules.get((character,tuple(sorted(MARKS[entry['unlockMarkRaw']]))))
        if aid is None or aid in result:raise RuntimeError('Ambiguous historical unlock association')
        result[aid]=entry
    if len(result)!=340:raise RuntimeError('Historical source must map its 340 completion targets exactly')
    return result


def catalogue():
    unlocks=read_data('unlocks.js');achievements=read_data('achievements.js')
    effects=read_data('effects.js')['entries'];characters={c['id']:c for c in unlocks['characters']}
    bosses={b['id']:b for b in unlocks['bosses']};rows={}
    for rule in unlocks['unlockRules']:
        aid=rule['achievementId'];effect=effects.get(str(aid),{});char=characters[rule['characterId']]
        catalog=unlocks['achievementCatalog'][str(aid)]
        entities=[]
        if effect.get('entityType') in {'collectible','trinket','card','pill'} and type(effect.get('entityId')) is int:
            entities=[dict(entityType=effect['entityType'],entityId=effect['entityId'])]
        for _,category,cid in MULTI_REWARD_BUNDLES.get(str(aid),{}).get('parts',[]):
            entities.append(dict(entityType=category,entityId=cid))
        rows[aid]=dict(achievementId=aid,name=effect.get('name') or catalog['name'],nameEn=catalog['name'],kind='rule',
                      condition=f"{char['name']} → "+' + '.join(bosses[b]['name'] for b in rule['bossIds']),
                      effect=effect.get('effect',''),rewardEntities=entities,categories=['character'],
                      characterId=char['id'],characterNameEn=char['nameEn'],bossIds=rule['bossIds'],tainted=char['tainted'])
    for challenge in read_data('challenges.js')['entries']:
        aid=challenge['rewardAchievementId'];entities=[]
        if challenge.get('entityType') in {'collectible','trinket','card','pill'} and type(challenge.get('entityId')) is int:
            entities=[dict(entityType=challenge['entityType'],entityId=challenge['entityId'])]
        for _,category,cid in MULTI_REWARD_BUNDLES.get(str(aid),{}).get('parts',[]):
            entities.append(dict(entityType=category,entityId=cid))
        rows[aid]=dict(achievementId=aid,name=challenge['rewardName'],nameEn=challenge.get('rewardEnglishName',''),kind='challenge',condition=f"完成挑战 #{challenge['challengeId']}",
                      effect=challenge['effect'],rewardEntities=entities,categories=['challenge'],challengeId=challenge['challengeId'],
                      challengePrerequisite=challenge.get('prerequisiteAchievementId'),rawEntityType=challenge.get('entityType'))
    for category,group in [('main',achievements['main']),('character-unlock',achievements['characters']['normal']+achievements['characters']['tainted']),
                           ('cumulative',achievements['cumulative']),('completion',achievements['completion'])]:
        for entry in group:
            aid=entry['achievementId']
            if aid in rows:
                rows[aid]['categories'].append(category)
                if category=='character-unlock':rows[aid]['condition']=entry['condition']
                continue
            rows[aid]=dict(achievementId=aid,name=entry['rewardName'] or entry['name'],kind='achievement',condition=entry['condition'],
                          effect=entry['rewardEffect'],rewardEntities=entry.get('rewardEntities',[]),categories=[category],
                          sequenceGroup=entry.get('sequenceGroup'))
    return unlocks,achievements,rows


def classify(row):
    aid=row['achievementId'];types=[]
    if aid in STARTING:return ['starting']
    if 'character-unlock' in row['categories']:return ['character']
    for entity in row['rewardEntities']:
        kind,cid=entity['entityType'],entity['entityId']
        if kind=='card':kind='soulstone' if 81<=cid<=97 else 'rune' if 32<=cid<=41 or cid==55 else 'card'
        if kind not in types:types.append(kind)
    if aid in SPECIAL_INTERACTIVE:types.append('interactive')
    if aid in SPECIAL_PICKUPS:types.append('pickup')
    if aid in {603,606}:types.append('pill')
    if row.get('rawEntityType')=='pickup':types.append('pickup')
    if row.get('rawEntityType')=='pill-bundle':types.append('pill')
    if not types:types=['route' if 'main' in row['categories'] or aid in PROGRESSION_TARGETS else 'completion']
    return list(dict.fromkeys(types))


def build_plan():
    unlocks,achievements,rows=catalogue()
    source=read_json(ENSEMBLE);models={e['id']:e for e in source['entries']}
    history=historical_targets(read_json(HISTORY),unlocks)
    reviews={e['achievementId']:e for e in read_json(REVIEWS)['entries']}
    legacy={e['achievementId']:e for e in read_json(TOOLS/'research_rankings.json')['entries']}
    # Pool associations already distinguish starting equipment and mixed rewards.
    from build_research_rankings import build_community
    _,associations=build_community(read_json(TOOLS/'community_rankings.json'),read_json(TOOLS/'research_rankings.json'))
    pool_ids={e['achievementId']:e['collectibleIds'] for e in associations}
    character_unlock={c['id']:(474+i-17 if c['tainted'] else NORMAL_UNLOCKS.get(c['nameEn'])) for i,c in enumerate(unlocks['characters'])}
    normal_character_ids={c['id'] for c in unlocks['characters'] if not c['tainted']}
    for aid,row in rows.items():
        types=classify(row);old=legacy.get(aid);historical=history.get(aid);review=reviews.get(aid,{})
        refs=[{key:models[cid][key] for key in ['id','name','nameZh','rank','score','relativeTier','familyCount','weightScenarioRankMin','weightScenarioRankMax']}
              for cid in pool_ids.get(aid,[]) if cid in models]
        refs.sort(key=lambda x:x['rank'])
        benefit=max((ref['score'] for ref in refs),default=0.)
        evidence='ensemble' if refs else 'historical-single-author' if historical and '(Co-Op)' not in historical['rawReward'] else 'checklist'
        ids=['ENS_V1','LOCAL'] if refs else ['HIST_UNLOCKS','LOCAL'] if historical else ['LOCAL']
        phase=1;effort=35.;future=1.;gateway=risk=0.;reason=''
        prerequisites=[];preparation=[]
        if not refs and historical:benefit=TIER_UTILITY[historical['tier']]
        if old and not refs and old['strength']!='—':
            label=old['strength'];benefit=90 if label.startswith('S') else 80 if label.startswith('A') else 55 if label.startswith('B') else 30
            evidence='prior-editorial';ids=list(dict.fromkeys(ids+old['sourceIds']))
        if row['kind']=='rule':
            effort=max(BOSS_EFFORT[b] for b in row['bossIds'])+max(0,len(row['bossIds'])-1)*10
            effort+=CHARACTER_EFFORT.get(row['characterNameEn'],0)+(8 if row['tainted'] else 0)
            phase=3 if row['characterNameEn'] in {'Tainted Lost','Tainted Jacob','Tainted Lazarus','Tainted Cain'} else 2 if row['tainted'] or set(row['bossIds'])&{'mother','beast','delirium','mega-satan','greedier'} else 1
            if character_unlock.get(row['characterId']) in {82,251,340,390,405}:phase=max(phase,2)
            if character_unlock.get(row['characterId']):prerequisites.append(character_unlock[row['characterId']])
            for boss,gate in [('greedier',341),('mother',407),('beast',635),('hush',234)]:
                if boss in row['bossIds']:prerequisites.append(gate)
            reason=f"先开放对应角色与路线，按{row['condition']}推进；获取成本计入角色难度、目标路线和捆绑标记。"
        elif row['kind']=='challenge':
            effort=30 if row['challengeId']<=20 else 50
            phase=1 if row['challengeId']<=20 else 2
            if row['challengeId'] in {28,34,37,38,39,40,41,42,43,44,45}:effort+=15;phase=3
            if row['challengePrerequisite']:prerequisites.append(row['challengePrerequisite'])
            reason=f"{row['condition']}；先检查挑战前置，挑战作为专门补强局安排。"
        else:
            phase=2;effort=35
            reason='按所列条件随正常打标或资源充足的局推进；随机收集条件不视为固定局数。'
            if row.get('sequenceGroup') is not None:effort=30
        if set(types)&RESOURCE_TYPES and not refs:
            phase=max(phase,2) if row['kind']!='challenge' else phase
            if historical:reason+=f" 历史解锁表原作者将该奖励列为{historical['tier']}，仅作单作者参考，当前用途与成本另列。"
        if types==['completion']:
            phase=4;benefit=0;future=0;evidence='checklist'
            reason='此目标主要用于完成类进度或联机外观；对当前单人全角色打标不计额外强度收益，最终全成就仍需完成。'
        if types==['route'] and 'main' not in row['categories']:
            benefit=55;evidence='progression';reason='开放头目、章节变体、商店或其他游戏机制；按所列条件随正常打标推进，不当作收藏道具的战斗强度。'
        if 'main' in row['categories']:
            phase=1 if aid in {4,234,34} else 2
            benefit=100;gateway=20;effort=25;evidence='progression';ids=['LOCAL','EN4']
            reason='优先开放主线分支，扩大后续可打标的路线与角色范围；此处按路线功能安排，不按奖励的战斗名次。'
        if types==['character']:
            phase=2 if 474<=aid<=490 or aid in {82,251,340,390,405} else 1
            benefit=90;gateway=10;evidence='progression';ids=['LOCAL','EN4'];effort=30
            reason='开放新的角色与其整组解锁目标，服务后续全角色打标；前置或随机条件未满足时先推进其他可做目标。'
            if 474<=aid<=490:
                prerequisites.extend([635,415])
                normal=unlocks['characters'][aid-474]
                if NORMAL_UNLOCKS.get(normal['nameEn']):prerequisites.append(NORMAL_UNLOCKS[normal['nameEn']])
        if aid in {79,199,474,485,404,405}:benefit=95;gateway=15
        if aid==405:prerequisites.append(407)
        if aid==404:prerequisites.append(80)
        if aid==415:phase=2;gateway=20;effort=25;prerequisites.append(635);reason='红钥匙与钥匙碎片帮助开放里角色，是后续里角色资源链的重要准备。'
        if aid in {348,406,391,411}:benefit=75;effort=30;evidence='progression';reason='开放路线、房间或掉落资源，随正常探索推进；以解锁后续内容的作用评估。'
        if aid==156:prerequisites.extend(r['achievementId'] for r in unlocks['unlockRules'] if r['characterId']=='c10-the-lost')
        if aid in {276,547,636}:
            phase=4;effort=100;future=.5 if aid==547 else 0 if aid==636 else .6
            targets=[r['achievementId'] for r in unlocks['unlockRules'] if aid==636 or r['characterId'] in normal_character_ids and (aid!=276 or r['bossIds']==['mega-satan'])]
            prerequisites.extend(targets)
            reason='这是大范围标记完成奖励，收益与到达该条件后的剩余进度分别看待；不为取得它而把完整清标当成早期步骤。'
        if aid==637:phase=4;future=0;prerequisites.append(636)
        if aid in {320,407,635}:prerequisites.extend(int(a) for a,b in achievements['mainEdges'] if b==aid)
        for before,after in achievements['mainEdges']:
            if after==aid:prerequisites.append(before)
        if review:
            benefit=review.get('utility',benefit);effort=review.get('effort',effort)
            future=review.get('futureFactor',future);gateway=review.get('gateway',gateway);risk=review.get('risk',risk)
            phase=review.get('phase',phase);reason=review.get('reason',reason)
            preparation=review.get('preparationIds',[])
            if review.get('effectText'):row['effect']=review['effectText']
            if review.get('displayName'):row['name']=review['displayName']
            ids=list(dict.fromkeys(ids+review.get('sourceIds',[])))
            if not refs:evidence='mechanism-review'
            elif 'utility' in review:evidence='mixed-reward-review'
        if not refs and benefit==0 and set(types)&RESOURCE_TYPES:
            raise RuntimeError(f'Missing resource benefit assessment for achievement {aid}')
        if benefit<55 and phase<2 and not gateway:phase=2
        score=priority_score(benefit,effort,future=future,gateway=gateway,risk=risk)
        priority='strong' if score>=55 and benefit>=70 else 'recommended' if score>=34 and benefit>=45 else 'normal'
        priority=review.get('priority',priority)
        parallel=old.get('parallelOrder') if old else None
        if parallel:phase=0
        row.update(rewardTypes=types,benefit=round(benefit,4),effort=effort,futureFactor=future,gateway=gateway,risk=risk,
                   priorityScore=score,priority=priority,phase=phase,phaseName=PHASE_NAMES[phase],reason=reason,
                   caveat=review.get('caveat',''),
                   effectOverride=review.get('effectText'),displayNameOverride=review.get('displayName'),
                   searchAliases=review.get('searchAliases',[]),
                   evidenceKind=evidence,sourceIds=ids,ensembleReferences=refs,
                   historicalReference=historical,prerequisiteAchievementIds=sorted(set(prerequisites)-{aid}),
                   preparationIds=preparation,parallelOrder=parallel,unlockRank=None,
                   priorUnlockRank=old.get('unlockRank') if old else None)
    # A stable topological sort keeps recorded prerequisites before their targets.
    incoming={aid:set(row['prerequisiteAchievementIds'])&set(rows) for aid,row in rows.items()}
    children=collections.defaultdict(list)
    for aid,parents in incoming.items():
        for parent in parents:children[parent].append(aid)
    # Carry a valuable target's scheduling priority back to its preparation chain.
    # Otherwise an unhelpful co-op reward needed for Godhead would strand it
    # behind every unrelated terminal checklist entry.
    scheduling={aid:(row['phase'],-row['priorityScore']) for aid,row in rows.items()}
    for _ in range(len(rows)):
        changed=False
        for child,parents in incoming.items():
            if rows[child]['parallelOrder'] is not None:continue
            for parent in parents:
                inherited=min(scheduling[parent],scheduling[child])
                if inherited!=scheduling[parent]:scheduling[parent]=inherited;changed=True
        if not changed:break
    key=lambda aid:(*scheduling[aid],aid)
    ready=[(*key(aid),aid) for aid,parents in incoming.items() if not parents];heapq.heapify(ready)
    order=[]
    while ready:
        *_,aid=heapq.heappop(ready);order.append(aid)
        for child in children[aid]:
            incoming[child].remove(aid)
            if not incoming[child]:heapq.heappush(ready,(*key(child),child))
    if len(order)!=len(rows):raise RuntimeError(f'Unlock prerequisite cycle: {[aid for aid,p in incoming.items() if p]}')
    number=0
    for aid in order:
        rows[aid]['schedulingPhase']=scheduling[aid][0]
        rows[aid]['preparationFor']=sorted(child for child in children[aid]
            if rows[child]['parallelOrder'] is None and scheduling[aid] < (rows[aid]['phase'],-rows[aid]['priorityScore']))
        if rows[aid]['schedulingPhase'] < rows[aid]['phase']:
            rows[aid]['phaseName']='前置准备 / '+PHASE_NAMES[rows[aid]['schedulingPhase']]
        if rows[aid]['parallelOrder'] is None:number+=1;rows[aid]['unlockRank']=number
    entries=[rows[aid] for aid in order]
    return dict(version=2,date='2026-11-05',objective='提高后续全角色打标效率，最终走向全成就',
                methodology='优先分=收益×剩余价值/(1+成本点/100)+路线增益−风险；先按准备阶段、优先分排序，并保持已记录前置在目标前。成本点不是小时，参数为编辑默认判断；资源收益不冒充收藏道具多榜强度。载入存档时可做目标优先，编号保持稳定。',
                resourceTypeLabels=TYPE_LABELS,total=len(entries),numbered=number,parallel=len(entries)-number,
                resourceCount=sum(bool(set(row['rewardTypes'])&RESOURCE_TYPES) for row in entries),
                modelTargetCount=sum(bool(row['ensembleReferences']) for row in entries),
                modelSnapshotSha256=hashlib.sha256(ENSEMBLE.read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
                evidenceCounts=dict(collections.Counter(row['evidenceKind'] for row in entries)),entries=entries)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--update-priorities',action='store_true',help='Update the public built-in profile, preserving browser custom profiles')
    args=parser.parse_args()
    plan=build_plan();OUT.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf-8')
    if args.update_priorities:apply_priorities(plan)
    print(json.dumps({key:plan[key] for key in ['total','numbered','parallel','resourceCount','modelTargetCount','evidenceCounts']},ensure_ascii=True))


def apply_priorities(plan):
    by_id={row['achievementId']:row for row in plan['entries']}
    def write(name,data):(TOOLS/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
    data=read_json(TOOLS/'recommendation_seed.json')
    data['entries']=[dict(characterId=r['characterId'],bossId=b,priority=by_id[r['achievementId']]['priority'])
                     for r in read_data('unlocks.js')['unlockRules'] for b in r['bossIds']]
    write('recommendation_seed.json',data)
    data=read_json(TOOLS/'challenge_priority.json')
    data['entries']=[dict(challengeId=r['challengeId'],priority=by_id[r['rewardAchievementId']]['priority']) for r in read_data('challenges.js')['entries']]
    write('challenge_priority.json',data)
    data=read_json(TOOLS/'achievement_priority.json')
    data['entries']=[dict(achievementId=row['achievementId'],priority=row['priority']) for row in plan['entries'] if row['kind']=='achievement']
    achievement_data=data
    data=read_json(TOOLS/'research_rankings.json')
    for entry in data['entries']:
        new=by_id[entry['achievementId']]
        entry['priority']=new['priority']
        if entry['priority']!=entry['previousPriority']:
            entry['correctionReason']='根据综合强度或特殊资源收益，结合前置、取得成本与后续打标价值修订。'+new['reason']
        else:entry['correctionReason']=''
    data['revisionDate']=plan['date']
    data['methodology']='65项原人工意见保留作参考；当前解锁排序与颜色使用unlockPlan的606项目标建议，收藏道具接入综合榜、特殊资源按已核验机制和历史意见评估，另计取得成本与前置。'
    known={s['id'] for s in data['sources']}
    extra=[dict(id='ENS_V1',title='718项综合强度公式与试算',url='https://github.com/Uesr20251011/isaac_unlock_planner/blob/feat/complete-guide-local-save/docs/research/ensemble-v1/ensemble-trial-report-v1.md',use='收藏道具的模型分数、名次与来源覆盖',limitation='399项多来源，319项单来源；相对强度不是解锁顺序或实战胜率。'),
           dict(id='HIST_UNLOCKS',title='Another Matt：2025解锁收益表归档',url='https://github.com/luisgtez/isaac-best-unlocks/tree/a7113097909428642b80d8ac84d547e1baec9d43/UnlocksInfo',use='特殊奖励的历史单作者意见',limitation='2025归档，部分忏悔+机制已变化；不作为新的独立收藏道具强度票。'),
           dict(id='EID_MECHANICS',title='EID：奖励机制说明',url='https://github.com/wofsauge/External-Item-Descriptions',use='资源实际效果与版本变更',limitation='机制说明不等于独立玩家评级。')]
    wiki_titles={'wiki-crane':'夹娃娃机与机器','wiki-machines':'机器','wiki-chests':'箱子','wiki-coins':'硬币','wiki-batteries':'电池','wiki-beggars':'乞丐','wiki-sacks':'福袋','wiki-black-sack':'黑福袋','wiki-poops':'粪便','wiki-rocks':'岩石','wiki-pills':'胶囊','wiki-trinkets':'饰品','matt2025':'Another Matt历史解锁表（2025归档）'}
    for src in read_json(REVIEWS).get('sources',[]):
        title=src.get('title') or ('以撒维基：'+wiki_titles[src['id']] if src['id'].startswith('wiki-') and src['id'] in wiki_titles else wiki_titles.get(src['id'],'特殊资源机制参考'))
        extra.append(dict(id=src['id'],title=title,url=src['url'],
                          use='奖励机制或历史意见核验',limitation=src.get('caveat') or '机制资料与评级意见区分；详见来源原文。'))
    for src in extra:
        if src['id'] not in known:data['sources'].append(src);known.add(src['id'])
        else:next(item for item in data['sources'] if item['id']==src['id']).update(src)
    write('research_rankings.json',data)
    achievement_data.setdefault('priorReviews',achievement_data.get('reviews',[]))
    achievement_data['reviews']=[dict(achievementId=row['achievementId'],name=row['name'],
        strength=row['ensembleReferences'][0]['relativeTier'] if row['ensembleReferences'] else '机制 / 编辑收益' if row['evidenceKind']!='checklist' else '完成类目标',
        reason=row['reason'],caveat=row['caveat'] or '按已注明来源与规则生成的开荒建议；成本为相对估计，详细机制与个人适用条件见来源。',
        sourceIds=row['sourceIds'],evidenceKind=row['evidenceKind']) for row in plan['entries'] if row['kind']=='achievement']
    achievement_data['sources']=data['sources']
    achievement_data['revisionDate']=plan['date']
    achievement_data['scope']='221项其他成就的内置建议，包含综合道具榜、资源机制复核、历史作者参考、前置与全成就清单；依据类型逐项标明。'
    write('achievement_priority.json',achievement_data)
    data=read_json(TOOLS/'recommendation_profiles.json')
    for profile in data['profiles']:
        if profile['id']=='beginner-9.10':profile['description']='结合718项综合道具榜及卡牌、符文、魂石、饰品、互动资源机制修订，覆盖606项目标的开荒建议；计入前置、成本与全角色打标价值。'
    write('recommendation_profiles.json',data)


if __name__=='__main__':main()
