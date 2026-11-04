"""Auditable research prototype, not a calibrated game win-rate predictor.

Only observed strength comparisons enter a regularized Bradley--Terry-style
composite loss. A list is one source family, not thousands of independent votes.
"""
from __future__ import annotations
import math
import numpy as np


def canonical_sources(sources,universe):
    """Remove a same-family view whose comparisons add no new information."""
    allowed=set(universe); records=[]
    for source in sources:
        entries={entry['id']:entry for entry in source['entries']
                 if entry['id'] in allowed and entry.get('version',source['version'])>0
                 and (entry.get('votes') is None or entry['votes']>0)}
        q=source['quality']*source['relevance']*source.get('weightMultiplier',1)
        levels=np.array([entry['level'] for entry in entries.values()])
        records.append((source,entries,q,int((levels[:,None]!=levels[None,:]).sum())))
    redundant={}
    for source,entries,q,pairs in records:
        ids=list(entries)
        levels=np.array([entries[cid]['level'] for cid in ids])
        sign=np.sign(levels[:,None]-levels[None,:])
        for parent,parent_entries,parent_q,parent_pairs in records:
            if source['id']==parent['id'] or source['family']!=parent['family']: continue
            if q>parent_q or not set(entries)<=set(parent_entries): continue
            if len(entries)==len(parent_entries) and (pairs,source.get('published',''),source['id'])>=(parent_pairs,parent.get('published',''),parent['id']): continue
            if any(entries[cid].get('version',source['version'])>parent_entries[cid].get('version',parent['version']) for cid in ids): continue
            parent_levels=np.array([parent_entries[cid]['level'] for cid in ids])
            if np.any((sign!=0)&(np.sign(parent_levels[:,None]-parent_levels[None,:])!=sign)): continue
            redundant[source['id']]=parent['id']; break
    return [source for source in sources if source['id'] not in redundant],redundant


def assemble_sources(sources, universe, sample_half=50, coverage_power=.5):
    universe=list(universe)
    index={cid:i for i,cid in enumerate(universe)}
    if len(index)!=len(universe): raise ValueError('Duplicate universe ID')
    if sample_half<=0 or coverage_power<=0: raise ValueError('Invalid sensitivity parameter')
    for source in sources:
        if source.get('basis')!='strength':
            raise ValueError('An unlock route or mechanism catalogue is not a strength vote')
        ids=[entry['id'] for entry in source['entries']]
        if len(set(ids))!=len(ids): raise ValueError('Duplicate source item')
    sources,redundant=canonical_sources(sources,universe)
    n=len(universe)
    families={}; budgets={}
    source_audit=[]
    for source in sorted(sources,key=lambda s:(s.get('published',''),s['id'])):
        if source.get('basis')!='strength':
            raise ValueError('An unlock route or mechanism catalogue is not a strength vote')
        quality,relevance=float(source['quality']),float(source['relevance'])
        multiplier=float(source.get('weightMultiplier',1))
        if not 0<=quality<=1 or not 0<=relevance<=1 or multiplier<0:
            raise ValueError('Invalid source weight')
        q=quality*relevance*multiplier
        entries=[entry for entry in source['entries'] if entry['id'] in index]
        if len({entry['id'] for entry in entries})!=len(entries):
            raise ValueError('Duplicate source item')
        family=source['family']
        group_c,group_t=families.setdefault(family,(np.zeros((n,n)),np.zeros((n,n))))
        ids=np.array([index[entry['id']] for entry in entries],dtype=int)
        levels=np.array([entry['level'] for entry in entries],dtype=float)
        version=np.array([entry.get('version',source['version']) for entry in entries],dtype=float)
        if np.any((version<0)|(version>1)): raise ValueError('Invalid version compatibility')
        confidence=[]
        for entry in entries:
            votes=entry.get('votes')
            if votes is None: confidence.append(1.0)  # Not a poll; source quality handles author evidence.
            elif votes<0: raise ValueError('Invalid item vote count')
            else: confidence.append(math.sqrt(votes/(votes+sample_half)))
        confidence=np.array(confidence)
        # Same-tier items were not strictly ordered by this source. Abstain.
        usable=(version>0)&(confidence>0)
        mask=(levels[:,None]!=levels[None,:]) & usable[:,None] & usable[None,:]
        degrees=mask.sum(axis=1)
        effective_items=int((degrees>0).sum())
        coverage=(effective_items-1)/(n-1) if effective_items>1 and n>1 else 0
        coverage_factor=coverage**coverage_power
        # Per-item exposure is not a new strength observation. Using it on each
        # edge plus shrinkage can reverse a complete, unopposed source ranking.
        # Use one robust exposure proxy for the source; retain zero-count masks.
        known_confidence=[confidence[i] for i,entry in enumerate(entries)
                          if entry.get('votes') is not None and usable[i]]
        exposure_factor=float(np.median(known_confidence)) if known_confidence else 1.
        budgets[family]=max(budgets.get(family,0),q*exposure_factor*coverage_factor)
        denominator=np.maximum(degrees[:,None],degrees[None,:])
        product=np.sqrt(version[:,None]*version[None,:])
        weights=np.divide(q*exposure_factor*coverage_factor*product,denominator,out=np.zeros_like(product),where=denominator>0)*mask
        outcomes=(levels[:,None]<levels[None,:]).astype(float)
        block=np.ix_(ids,ids)
        # Reposts/translated editions from one family never add a second vote.
        # On equal predeclared weight, the latest dated source is selected.
        old_c=group_c[block]
        select=(weights>0)&(weights>=old_c)
        group_c[block]=np.where(select,weights,old_c)
        group_t[block]=np.where(select,weights*outcomes,group_t[block])
        source_audit.append(dict(id=source['id'],family=family,matched=len(entries),
                                 comparablePairs=int(mask.sum()//2),
                                 coverageFactor=coverage_factor,scopeCoverage=coverage,
                                 exposureFactor=exposure_factor,
                                 unmatchedIds=[entry['id'] for entry in source['entries'] if entry['id'] not in index],
                                 maxPerItemMass=float(weights.sum(axis=1).max()) if len(entries) else 0))
    for family,(group_c,group_t) in families.items():
        budget=budgets[family]
        if budget<=0: continue
        row_mass=group_c.sum(axis=1)/budget
        scale=np.maximum(1,np.maximum(row_mass[:,None],row_mass[None,:]))
        group_c/=scale
        group_t/=scale
    c=sum((values[0] for values in families.values()),np.zeros((n,n)))
    t=sum((values[1] for values in families.values()),np.zeros((n,n)))
    observed=c.sum(axis=1)>0
    seen=set(); components=[]
    for i in np.flatnonzero(observed):
        if int(i) in seen: continue
        stack=[int(i)]; seen.add(int(i)); group=[]
        while stack:
            current=stack.pop(); group.append(universe[current])
            for j in np.flatnonzero(c[current]>0):
                if int(j) not in seen: seen.add(int(j)); stack.append(int(j))
        components.append(group)
    audit=dict(familyCount=len(families),sources=source_audit,
               redundantSources=redundant,
               observedIds=[cid for cid,active in zip(universe,observed) if active],
               unobservedIds=[cid for cid,active in zip(universe,observed) if not active],
               components=components,
               familyItemMass={name:values[0].sum(axis=1).tolist() for name,values in families.items()})
    return c,t,audit


def objective_gradient(theta,c,t,reg):
    delta=theta[:,None]-theta[None,:]
    probability=1/(1+np.exp(-np.clip(delta,-50,50)))
    loss=float(np.triu(c*np.logaddexp(0,delta)-t*delta,1).sum()+reg*np.dot(theta,theta)/2)
    gradient=(c*probability-t).sum(axis=1)+reg*theta
    return loss,gradient


def fit_model(c,t,reg=.03,initial=None,tolerance=1e-7,max_iterations=4000):
    if reg<=0: raise ValueError('A positive regularizer is required')
    n=len(c)
    theta=np.zeros(n) if initial is None else np.array(initial,dtype=float,copy=True)
    y=theta.copy(); momentum=1.0
    # The largest Hessian eigenvalue is bounded by half the maximum row mass + reg.
    step=1/(.5*float(c.sum(axis=1).max())+reg)
    previous_loss,_=objective_gradient(theta,c,t,reg)
    converged=False
    for iteration in range(1,max_iterations+1):
        _,gradient=objective_gradient(y,c,t,reg)
        candidate=y-step*gradient
        candidate-=candidate.mean()
        loss,new_gradient=objective_gradient(candidate,c,t,reg)
        if loss>previous_loss+1e-10:
            y=theta.copy(); momentum=1.0
            _,gradient=objective_gradient(y,c,t,reg)
            candidate=y-step*gradient; candidate-=candidate.mean()
            loss,new_gradient=objective_gradient(candidate,c,t,reg)
        new_momentum=(1+math.sqrt(1+4*momentum**2))/2
        y=candidate+(momentum-1)/new_momentum*(candidate-theta)
        theta=candidate; momentum=new_momentum; previous_loss=loss
        if float(np.abs(new_gradient).max())<tolerance:
            converged=True; break
    return dict(theta=theta,converged=converged,iterations=iteration,loss=loss,
                gradientMax=float(np.abs(new_gradient).max()),regularization=reg)


def model_scores(theta):
    n=len(theta)
    if n<2: return np.full(n,50.)
    preference=1/(1+np.exp(-np.clip(theta[:,None]-theta[None,:],-50,50)))
    return 100*(preference.sum(axis=1)-.5)/(n-1)


def rank_summary(theta,tolerance=1e-8):
    order=np.argsort(-theta,kind='stable'); n=len(order)
    ranks=np.empty(n); low=np.empty(n,dtype=int); high=np.empty(n,dtype=int)
    start=0
    while start<n:
        end=start+1
        while end<n and abs(theta[order[end]]-theta[order[start]])<=tolerance: end+=1
        members=order[start:end]
        ranks[members]=(start+1+end)/2; low[members]=start+1; high[members]=end
        start=end
    return ranks,low,high


def relative_tiers(low,high,n):
    tiers=[]
    for rank in range(int(low),int(high)+1):
        p=100*(n-rank)/(n-1) if n>1 else 50
        tier=next(tier for cutoff,tier in [(95,'S'),(80,'A'),(55,'B'),(30,'C'),(10,'D'),(-1,'F')] if p>=cutoff)
        if tier not in tiers: tiers.append(tier)
    return tiers
