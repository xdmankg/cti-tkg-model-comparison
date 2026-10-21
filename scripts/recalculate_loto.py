#!/usr/bin/env python3
"""Recalculate paired LOTO intervals from preserved transition losses.
Validate both reference comparisons before calculating R0 minus R2.
"""
import csv, json, hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'results/main'
def read(name):
 with (P/name).open(newline='') as f:return list(csv.DictReader(f))
loss=read('LOTO_primary_losses.csv');reference=read('table8_LOTO.csv')
def difference(sc,rep,left,right):
 rows=[r for r in loss if r['scenario']==sc and r['replicate']==rep]
 by={(r['holdout'],r['model']):float(r['mse']) for r in rows}
 holds=sorted({int(r['holdout']) for r in rows})
 assert holds==list(range(21)) and len(rows)==63
 return np.array([by[str(i),left]-by[str(i),right] for i in holds])
def interval(d,seed,b):
 rng=np.random.default_rng(seed);starts=rng.integers(0,len(d)-3+1,size=(b,(len(d)+2)//3))
 indices=(starts[:,:,None]+np.arange(3)).reshape(b,-1)[:,:len(d)]
 lo,hi=np.quantile(d[indices].mean(axis=1),[.025,.975],method='linear')
 return float(d.mean()),float(lo),float(hi)
checks=[];outputs=[]
for r in reference:
 assert r['scheme']=='MOVING_BLOCK_L3' and int(r['B'])==10000
 left,right=r['comparison'].split('_MINUS_')
 got=interval(difference(r['scenario'],r['replicate'],left,right),int(r['seed']),int(r['B']))
 error=max(abs(x-float(r[k])) for x,k in zip(got,['mean_error_difference','low','high']))
 checks.append(error)
assert len(checks)==30 and max(checks)<1e-10,checks
for r in reference:
 if r['comparison']!='R1_MINUS_R2':continue
 mean,lo,hi=interval(difference(r['scenario'],r['replicate'],'R0','R2'),int(r['seed']),int(r['B']))
 outputs.append(dict(scenario=r['scenario'],replicate=r['replicate'],input=r['input'],comparison='R0_MINUS_R2',scheme=r['scheme'],B=r['B'],seed=r['seed'],mean_error_difference=mean,low=lo,high=hi,contains_zero=lo<=0<=hi))
with (P/'LOTO_R0_R2.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(outputs[0]));w.writeheader();w.writerows(outputs)
report=dict(provenance='Recalculated from released losses; not a recovered original result file.',reference_intervals_checked=30,max_reference_error=max(checks),new_intervals=len(outputs),intervals_including_zero=sum(r['contains_zero'] for r in outputs),seed_policy='Reuse the R1_MINUS_R2 seed of the same scenario and replicate.',block_length=3,bootstrap_samples=10000,quantiles=[.025,.975],quantile_method='linear',numpy_version=np.__version__,input_sha256={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['LOTO_primary_losses.csv','table8_LOTO.csv']})
(P/'LOTO_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
