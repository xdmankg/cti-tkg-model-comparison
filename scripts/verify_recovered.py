#!/usr/bin/env python3
"""Check recovered data, numerical identities and source-scope projections.
No randomization, fitting, plotting or extraction is performed.
"""
from pathlib import Path
import json,hashlib,csv
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]
checks=[]
def ck(name,actual,expected,tol=0):
 ok=bool(actual==expected) if isinstance(expected,(str,bool)) else abs(actual-expected)<=tol
 checks.append(dict(check_id=name,actual=actual,expected=expected,tolerance=tol,status='PASS' if ok else 'FAIL'))
def read(p):return pd.read_csv(R/p,float_precision='round_trip')
can=read('data/canonical_documents.csv');ids=set(can.loc[can.included_in_analytical_corpus,'canonical_document_id'])
ck('canonical_reports',len(can),1856);ck('final_reports',len(ids),1474)
te=read('data/technique_evidence.csv');ck('mapping_evidence',len(te),9550);ck('quarantined_mapping_evidence',int(te.pair_conflict_flag.sum()),313)
ck('eligible_final_evidence',int((te.canonical_document_id.isin(ids)&te.primary_pair_eligible).sum()),8622)
tl=read('data/document_techniques.csv');ck('final_links',len(tl),4852);ck('techniques',tl.canonical_attack_id.nunique(),449)
t=read('data/event_time_assignments.csv');ck('time_all',len(t),14252);ck('time_final',int(t.canonical_document_id.isin(ids).sum()),14236)
w=read('data/document_year_weights.csv');ck('weight_rows',len(w),4060);ck('weight_reports_match',set(w.canonical_document_id)==ids,True)
# Reconstruct W from the released links and original weights and compare all 620,290 values.
u=read('data/relation_universe.csv').sort_values('feature_index');tech=sorted(set(tl.canonical_attack_id));ti={x:i for i,x in enumerate(tech)};ds=sorted(ids);di={x:i for i,x in enumerate(ds)}
A=np.zeros((len(ds),len(tech)),dtype=float)
for x in tl.itertuples():A[di[x.canonical_document_id],ti[x.canonical_attack_id]]=1
idxi=np.array([ti[x] for x in u.technique_i_id]);idxj=np.array([ti[x] for x in u.technique_j_id]);W=[];supports=[]
for year in range(2002,2024):
 wt=np.zeros(len(ds))
 for x in w[w.year==year].itertuples():wt[di[x.canonical_document_id]]=x.weight
 W.append(((A.T*wt)@A)[idxi,idxj]/wt.sum());supports.append(((A.T*(wt>0))@A)[idxi,idxj])
W=np.asarray(W);supports=np.asarray(supports)
z0=np.load(R/'results/followup/foundation/S0_FULL_replicate_0.npz',allow_pickle=False)
ck('original_weights_links_to_W_max_error',float(abs(W-z0['observed']).max()),0,1e-12)
ck('original_weights_links_to_support_max_error',float(abs(supports-z0['supports']).max()),0)
files=sorted((R/'results/followup/foundation').glob('*.npz'));ck('foundation_file_count',len(files),15)
for p in files:
 z=np.load(p,allow_pickle=False);ck(p.stem+':shape',str(z['observed'].shape),'(22, 28195)')
 ck(p.stem+':finite',all(np.isfinite(z[k]).all() for k in z.files),True)
 for level in ['L0_STAGE15_MATCHED','L1_EXTENDED','L2_HIGH']:
  ck(p.stem+':'+level+':residual',float(abs(np.maximum(0,z['observed']-z['mu_'+level])-z['residual_'+level]).max()),0,1e-14)
 base=np.load(R/('results/followup/foundation/'+p.stem.rsplit('_',1)[0]+'_0.npz'),allow_pickle=False)
 ck(p.stem+':W_same_across_bundles',float(abs(z['observed']-base['observed']).max()),0)
a=pd.read_parquet(R/'results/initial/stage15/validation_rcd1_residual_long.parquet').sort_values(['annual_window','feature_index'])
ck('initial_W_matches_followup_W',float(abs(a.observed_wgt3.to_numpy().reshape(22,-1)-z0['observed']).max()),0)
ck('initial_residual_identity',float(abs(np.maximum(0,a.observed_wgt3-a.null_expected_wgt3)-a.positive_excess).max()),0,1e-14)
rm=read('results/corrections/loto_rmse_summary_corrected.csv');row=rm[(rm.aggregation_scope=='OVERALL')&(rm.comparison=='PREPROCESSING_FOLDLOCAL_MINUS_LEGACY')&(rm.model=='R2')].iloc[0]
for c,v in [('n',49),('n_decrease',18),('n_equal',20),('n_increase',11)]:ck('corrected_R2_'+c,int(row[c]),v)
rank=read('results/initial/figure_05/rich_document_ranking.csv');ck('ranking_scope_match',set(rank.canonical_document_id)==ids,True);ck('pair_potential_formula',float(abs(rank.pair_potential-rank.n_techniques*(rank.n_techniques-1)/2).max()),0);ck('potential_total',int(rank.pair_potential.sum()),66325)
ck('top74_share_percent',float(rank.sort_values('rank').head(74).pair_potential.sum()/rank.pair_potential.sum()*100),92.72,.005)
for rel,n in [('results/time_revision/v3_1/hold_both_time_assignments',14082),('results/time_revision/residual_six/revised_time_assignments',14076)]:
 d=read(rel+'.csv');v=read(rel+'_final_scope.csv');ck(rel+':final_count',len(v),n);ck(rel+':outside_count',int((~d.canonical_document_id.isin(ids)).sum()),16);ck(rel+':candidate_match',set(v.candidate_id)==set(d.loc[d.canonical_document_id.isin(ids),'candidate_id']),True)
seeds=json.loads((R/'configs/followup_seeds.json').read_text());ck('seed_count',len(seeds['entries']),1980)
ck('seed_derivation',all(int(x['seed_uint64'])==int.from_bytes(hashlib.sha256(x['seed_token'].encode()).digest()[:8],'little') for x in seeds['entries']),True)
for x in checks:print(x['status'],x['check_id'],x['actual'])
with (R/'docs/recovered_verification.csv').open('w',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=checks[0].keys());wr.writeheader();wr.writerows(checks)
n=sum(x['status']=='FAIL' for x in checks);print(f'PASS {len(checks)-n} FAIL {n}');raise SystemExit(bool(n))
