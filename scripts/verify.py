#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the released numerical results against the values reported in the manuscript.

Run from the package root:  python3 scripts/verify.py
Standard library only. Each check prints expected value, actual value, tolerance and status.
Checks cover the supplied data and selected numerical results.
Exit code 0 only when every implemented check passes.
"""
import csv, hashlib, statistics, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = []  # (check_id, source, expected, actual, tolerance, status)


def rows(rel):
    p = ROOT / rel
    if not p.exists():
        return None
    with p.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def check(cid, source, expected, actual, tol=0.0):
    if actual is None:
        RESULTS.append((cid, source, expected, '', tol, 'NOT_AVAILABLE')); return
    if isinstance(expected, str):
        ok = str(actual) == expected
    else:
        ok = abs(float(actual) - float(expected)) <= tol
    RESULTS.append((cid, source, expected, actual, tol, 'PASS' if ok else 'FAIL'))


# ---------------------------------------------------------------- 1. checksums
def check_hashes():
    p = ROOT / 'checksums.sha256'
    if not p.exists():
        check('checksums.sha256', 'package', 'present', None); return
    n_ok = n_bad = 0
    for line in p.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        h, name = line.split(None, 1)
        name = name.strip().lstrip('*')
        f = ROOT / name
        if not f.exists():
            check(f'hash:{name}', 'checksums.sha256', 'exists', None); continue
        actual = hashlib.sha256(f.read_bytes()).hexdigest()
        check(f'hash:{name}', 'checksums.sha256', h, actual)


# ---------------------------------------------------------------- 2. Table 7 (conditional tests)
TABLE7 = {  # (composition, direction): (p_min, p_max, holm_min, holm_max)
    ('S0_FULL', 'TIME_GIVEN_COVERAGE'): (0.7849, 0.8082, 0.7849, 0.8082),
    ('S0_FULL', 'COVERAGE_GIVEN_TIME'): (0.0330, 0.0380, 0.0660, 0.0760),
    ('S1_DROP_TOP1', 'TIME_GIVEN_COVERAGE'): (0.1811, 0.2190, 0.3622, 0.4380),
    ('S1_DROP_TOP1', 'COVERAGE_GIVEN_TIME'): (0.4488, 0.5372, 0.4488, 0.5372),
    ('S2_DROP_TOP5', 'TIME_GIVEN_COVERAGE'): (0.1139, 0.1210, 0.1930, 0.2278),
    ('S2_DROP_TOP5', 'COVERAGE_GIVEN_TIME'): (0.0965, 0.1232, 0.1930, 0.2278),
}


def check_table7():
    r = rows('results/main/table8_conditional_tests.csv')
    for (sc, d), (pmin, pmax, hmin, hmax) in TABLE7.items():
        if r is None:
            for k in ('p_min', 'p_max', 'holm_min', 'holm_max'):
                check(f'Table7:{sc}:{d}:{k}', 'Table 7', 0, None)
            continue
        sel = [x for x in r if x['scenario'] == sc and x['direction'] == d]
        ps = [float(x['p']) for x in sel]; hs = [float(x['p_holm_two_directions']) for x in sel]
        check(f'Table7:{sc}:{d}:n_bundles', 'Table 7', 5, len(sel))
        if sel:
            check(f'Table7:{sc}:{d}:p_min', 'Table 7', pmin, round(min(ps), 4), 5e-5)
            check(f'Table7:{sc}:{d}:p_max', 'Table 7', pmax, round(max(ps), 4), 5e-5)
            check(f'Table7:{sc}:{d}:holm_min', 'Table 7', hmin, round(min(hs), 4), 5e-5)
            check(f'Table7:{sc}:{d}:holm_max', 'Table 7', hmax, round(max(hs), 4), 5e-5)


# ---------------------------------------------------------------- 3. LOTO (Section 4.4, Table 7 note)
LOTO = {('S0_FULL', 'R1_MINUS_R0'): 5, ('S1_DROP_TOP1', 'R1_MINUS_R0'): 5, ('S2_DROP_TOP5', 'R1_MINUS_R0'): 5,
        ('S0_FULL', 'R1_MINUS_R2'): 5, ('S1_DROP_TOP1', 'R1_MINUS_R2'): 3, ('S2_DROP_TOP5', 'R1_MINUS_R2'): 3}
LOTO_BELOW = {('S1_DROP_TOP1', 'R1_MINUS_R2'): 2, ('S2_DROP_TOP5', 'R1_MINUS_R2'): 2}


def check_loto():
    r = rows('results/main/table8_LOTO.csv')
    for (sc, cmp), n0 in LOTO.items():
        if r is None:
            check(f'LOTO:{sc}:{cmp}:intervals_including_0', 'Section 4.4', n0, None); continue
        sel = [x for x in r if x['scenario'] == sc and x['comparison'] == cmp]
        inc = sum(float(x['low']) <= 0 <= float(x['high']) for x in sel)
        check(f'LOTO:{sc}:{cmp}:intervals_including_0', 'Section 4.4', f'{n0}/5', f'{inc}/{len(sel)}')
        if (sc, cmp) in LOTO_BELOW:
            below = sum(float(x['high']) < 0 for x in sel)
            check(f'LOTO:{sc}:{cmp}:intervals_below_0', 'Section 4.4', LOTO_BELOW[(sc, cmp)], below)
    r2 = rows('results/main/LOTO_R0_R2.csv')
    if r2 is None:
        check('LOTO:R0_MINUS_R2:intervals_including_0', 'Section 4.4', '15/15', None)
    else:
        inc = sum(float(x['low']) <= 0 <= float(x['high']) for x in r2 if x.get('comparison', 'R0_MINUS_R2') == 'R0_MINUS_R2')
        check('LOTO:R0_MINUS_R2:intervals_including_0', 'Section 4.4', '15/15', f'{inc}/{len(r2)}')


# ---------------------------------------------------------------- 4. Table 8 / S16 / S17 (B2)
T8 = {  # (q_policy, lambda, start_year): {scenario: {candidate_set: count}}
    ('legacy_fixed', '1.0', '2002'): {'S0_FULL': {'{R0}': 3, '{R2}': 2}, 'S1_DROP_TOP1': {'{R0}': 5}, 'S2_DROP_TOP5': {'{R0}': 2, '{R2}': 2, '{R0,R2}': 1}},
    ('reestimated', '1.0', '2002'): {'S0_FULL': {'{R0}': 5}, 'S1_DROP_TOP1': {'{R0}': 5}, 'S2_DROP_TOP5': {'{R2}': 5}},
    ('reestimated', '0.75', '2002'): {s: {'{R2}': 5} for s in ('S0_FULL', 'S1_DROP_TOP1', 'S2_DROP_TOP5')},
    ('reestimated', '0.5', '2002'): {s: {'{R2}': 5} for s in ('S0_FULL', 'S1_DROP_TOP1', 'S2_DROP_TOP5')},
    ('legacy_fixed', '1.0', '2004'): {s: {'{R0}': 5} for s in ('S0_FULL', 'S1_DROP_TOP1', 'S2_DROP_TOP5')},
    ('legacy_fixed', '1.0', '2005'): {s: {'{R0}': 5} for s in ('S0_FULL', 'S1_DROP_TOP1', 'S2_DROP_TOP5')},
    ('reestimated', '1.0', '2004'): {s: {'{R0}': 5} for s in ('S0_FULL', 'S1_DROP_TOP1', 'S2_DROP_TOP5')},
    ('reestimated', '1.0', '2005'): {s: {'{R0}': 5} for s in ('S0_FULL', 'S1_DROP_TOP1', 'S2_DROP_TOP5')},
}
ZERO_BUDGET = {('legacy_fixed', '1.0'): (0, 0, 0), ('reestimated', '1.0'): (1, 1, 2), ('reestimated', '0.75'): (2, 4, 4), ('reestimated', '0.5'): (4, 4, 4)}
MEDIAN_BUDGET = {('reestimated', '1.0'): (83, 20, 9)}
SCEN = ('S0_FULL', 'S1_DROP_TOP1', 'S2_DROP_TOP5')


def norm_set(s):
    return '{' + ','.join(sorted(x.strip() for x in s.strip('{}').split(','))) + '}'


def check_b2():
    bm = rows('results/main/B2/B2_L2_models.csv')
    if bm is not None:
        qs = sorted({round(float(x['q']), 6) for x in bm})
        check('B2:q_values', 'Table 8 note', '[0.004505, 0.039039]', str(qs))
    for (qp, lam, sy), exp in T8.items():
        for sc, sets in exp.items():
            cid = f'Table8/S17:{qp}:lambda={lam}:start={sy}:{sc}'
            if bm is None:
                check(cid, 'Table 8 / Table S17', str(dict(sorted(sets.items()))), None); continue
            sel = [x for x in bm if x['q_policy'] == qp and x['lambda'] == lam and x['start_year'] == sy and x['scenario'] == sc]
            got = Counter(norm_set(x['candidate_set']) for x in sel)
            check(cid, 'Table 8 / Table S17', str(dict(sorted({norm_set(k): v for k, v in sets.items()}.items()))), str(dict(sorted(got.items()))))
    sel_rows = rows('results/main/B2/selection_details.csv')
    for (qp, lam), zb in ZERO_BUDGET.items():
        for sc, z in zip(SCEN, zb):
            cid = f'TableS16:zero_budget:{qp}:lambda={lam}:{sc}'
            if sel_rows is None:
                check(cid, 'Table 8 / Table S16', z, None); continue
            reps = sorted({x['replicate'] for x in sel_rows})
            per = {sum(1 for x in sel_rows if x['q_policy'] == qp and x['lambda'] == lam and x['scenario'] == sc and x['replicate'] == rep and x['budget'] == '0') for rep in reps}
            check(cid, 'Table 8 / Table S16', str({z}), str(per))
    for (qp, lam), meds in MEDIAN_BUDGET.items():
        for sc, m in zip(SCEN, meds):
            cid = f'TableS16:median_budget:{qp}:lambda={lam}:{sc}'
            if bm is None:
                check(cid, 'Section 4.6', m, None); continue
            sel = [x for x in bm if x['q_policy'] == qp and x['lambda'] == lam and x['start_year'] == '2002' and x['scenario'] == sc]
            check(cid, 'Section 4.6', m, statistics.median(float(x['median_budget']) for x in sel), 0.5)


# ---------------------------------------------------------------- 5. Table S14 (contrast tests)
S14 = [  # input, threshold, test, T12, null_median, count, p
    ('baseline', '0.0', 'E02', -1.8095, 63.3723, 1, 0.009950),
    ('baseline', '0.0', 'E03', -1.8095, 62.4089, 0, 0.004975),
    ('baseline', '1e-12', 'E02', 7.2748, 77.9101, 0, 0.004975),
    ('baseline', '1e-12', 'E03', 7.2748, 79.2859, 0, 0.004975),
    ('modified', '1e-12', 'E02', 13.8711, 69.6222, 1, 0.009950),
    ('modified', '1e-12', 'E03', 13.8711, 67.5037, 0, 0.004975),
    ('modified', '0.0', 'E02', 19.7510, 71.5621, 4, 0.024876),
    ('modified', '0.0', 'E03', 19.7510, 74.8421, 4, 0.024876),
]


def check_s14():
    r = rows('results/main/contrast/contrast_results.csv')
    for inp, thr, test, t12, med, cnt, p in S14:
        cid = f'TableS14:{inp}:{thr}:{test}'
        sel = [x for x in (r or []) if x['input'] == inp and float(x['threshold']) == float(thr) and x['test'] == test]
        if not sel:
            check(cid + ':T12', 'Table S14', t12, None); continue
        x = sel[0]
        check(cid + ':T12', 'Table S14', t12, float(x['T12']), 5e-5)
        check(cid + ':null_median', 'Table S14', med, float(x['null_median']), 5e-5)
        check(cid + ':count', 'Table S14', cnt, int(x['count']))
        check(cid + ':p', 'Table S14', p, float(x['p']), 5e-7)
        threshold_label = '0' if float(thr) == 0 else thr
        null = rows(f'results/main/contrast/{inp}_{threshold_label}_{test}_null.csv')
        if null is None:
            check(cid + ':null_file_rows', 'Table S14', 200, None); continue
        vals = [float(y['T12_null']) for y in null]
        check(cid + ':null_file_rows', 'Table S14', 200, len(vals))
        check(cid + ':recomputed_count', 'Equation (12)', cnt, sum(v <= float(x['T12']) for v in vals))
        check(cid + ':recomputed_p', 'Equation (12)', p, (1 + sum(v <= float(x['T12']) for v in vals)) / 201, 5e-7)
        check(cid + ':recomputed_median', 'Table S14', med, statistics.median(vals), 5e-5)


# ---------------------------------------------------------------- 6. Audit and additional released results
def check_added():
    import json
    a=rows('results/audit/initial_and_final_labels.csv')
    for group,subset,expected_match,expected_kappa in [('technique',[x for x in a if x['blind_id'].startswith('T-')],176,0.70799),('time',[x for x in a if x['blind_id'].startswith('M-')],95,0.89994)]:
        n=len(subset); match=sum(x['rater1_initial']==x['rater2_initial'] for x in subset)
        c1=Counter(x['rater1_initial'] for x in subset); c2=Counter(x['rater2_initial'] for x in subset)
        pe=sum(c1[k]*c2[k] for k in ('1','2','3'))/n**2
        check('audit:'+group+':agreement','initial responses',expected_match,match)
        check('audit:'+group+':kappa','initial responses',expected_kappa,(match/n-pe)/(1-pe),5e-6)
    check('audit:negative_techniques','final labels',44,sum(x['final_author_record']=='2' for x in [x for x in a if x['blind_id'].startswith('T-')]))
    strata=rows('results/audit/final_stratified_counts.csv')
    inter=json.loads((ROOT/'results/audit/interval_results.json').read_text())
    for g,N,n,est in [('A',8622,200,.7603503081817278),('C',14236,100,.6409525147513346)]:
        rr=[x for x in strata if x['stratum'].startswith(g+':')]
        check('audit:'+g+':population','strata',N,sum(int(x['N']) for x in rr))
        check('audit:'+g+':sample','strata',n,sum(int(x['n']) for x in rr))
        calc=sum(int(x['N'])/N*int(x['positive'])/int(x['n']) for x in rr)
        check('audit:'+g+':weighted','strata',est,calc,1e-12)
        check('audit:'+g+':stored_estimate','interval file',calc,inter[g]['weighted_estimate'],1e-12)
    b=rows('results/main/B0_L2_models.csv'); check('B0:rows','Table S11',15,len(b))
    for x in b:
        check('B0:'+x['scenario']+':'+x['replicate'],'main comparison','{R2}' if x['scenario']=='S0_FULL' else '{R0}',x['candidates'])
    f=rows('results/main/factorial_followup_180.csv');check('factorial:rows','Table S10',180,len(f))
    groups=Counter((x['scenario'],x['level'],x['input'],x['threshold']) for x in f)
    check('factorial:conditions','Table S10',36,len(groups));check('factorial:five_per_condition','Table S10',36,sum(v==5 for v in groups.values()))
    for j,x in enumerate(f):
        ic={m:float(x[m]) for m in ['R0','R1','R2']};minimum=min(ic.values())
        expected='{'+','.join(m for m in ic if ic[m]-minimum<=2)+'}'
        check('factorial:candidate:'+str(j),'IC scores',norm_set(expected),norm_set(x['candidates']))
    slopes=rows('results/main/figure8_slopes.csv')
    for rep in range(5):
        rr=[x for x in slopes if int(x['replicate'])==rep]
        check('slopes:sign_agreement:'+str(rep),'Figure 8',7,sum(float(x['R'])*float(x['W'])>0 for x in rr))
    budgets=rows('results/main/B2/B2_selection.csv');details=rows('results/main/B2/selection_details.csv')
    for j,x in enumerate(budgets):
        rr=[v for v in details if all(v[k]==x[k] for k in ['q_policy','scenario','lambda','replicate'])]
        check('budget:median:'+str(j),'transition budgets',float(x['median_budget']),statistics.median(float(v['budget']) for v in rr))
        check('budget:zero:'+str(j),'transition budgets',int(x['zero_transitions']),sum(float(v['budget'])==0 for v in rr))
    deps=rows('results/time_revision/rule_dependency_links.csv')
    check('dependencies:links','Section S5.7',4852,len(deps));check('dependencies:exclusive','Section S5.7',120,sum(x['exclusive'].lower()=='true' for x in deps))
    tracking=rows('results/time_revision/CVE85_tracking.csv')
    check('CVE:tracked','Section S5.6',85,len(tracking));check('CVE:excluded','Section S5.6',81,sum(x['reason']=='EX_CVE' for x in tracking))
    flow=rows('results/time_revision/time_flow.csv')
    check('time:original_adopted','Table S22',14252,sum(int(x['count']) for x in flow if x['original_adopted'].lower()=='true'))
    confirmed=rows('results/time_revision/confirmed_identifier_years.csv'); changed=rows('results/time_revision/residual_six/changed_weights.csv')
    check('residual:items','Section S5.6',6,len(confirmed));check('residual:weights','Section S5.6',5,len(changed))
    impact=rows('results/time_revision/residual_six/annual_impact.csv')
    check('residual:max_delta_W','Section S5.6',.0016065851758565175,max(float(x['max_abs_W_change']) for x in impact),1e-15)
    for rel,n in [('data/relation_universe.csv',28195),('data/top5_excluded_documents.csv',74),('results/time_revision/residual_six/revised_weights.csv',4017),('results/time_revision/v3_1/hold_both_weights.csv',4019)]:
        check('rows:'+rel,'preserved output',n,len(rows(rel)))


def check_audit():
    r = rows('results/audit/initial_and_final_labels.csv')
    if r is None:
        for cid in ('agreement', 'kappa', 'negative_final'):
            check(f'Audit:technique:{cid}', 'Section 3.2 / Table S20', '', None)
            check(f'Audit:time:{cid}', 'Section 3.3 / Table S21', '', None)
    else:
        def kappa(s):
            cats = sorted({x['rater1_initial'] for x in s} | {x['rater2_initial'] for x in s})
            po = sum(x['rater1_initial'] == x['rater2_initial'] for x in s) / len(s)
            pe = sum((sum(x['rater1_initial'] == c for x in s) / len(s)) * (sum(x['rater2_initial'] == c for x in s) / len(s)) for c in cats)
            return po, (po - pe) / (1 - pe)
        # blind_id prefix T = technique evidence items (200), M = time expressions (100)
        for pref, name, n, agree, kap, neg, src in (('T', 'technique', 200, 176, 0.708, 44, 'Section 3.2 / Table S20'), ('M', 'time', 100, 95, 0.900, None, 'Section 3.3 / Table S21')):
            s = [x for x in r if x['blind_id'].startswith(pref)]
            check(f'Audit:{name}:n', src, n, len(s))
            po, k = kappa(s) if s else (None, None)
            check(f'Audit:{name}:agreement', src, agree, sum(x['rater1_initial'] == x['rater2_initial'] for x in s) if s else None)
            check(f'Audit:{name}:kappa', src, kap, round(k, 3) if k is not None else None, 5e-4)
            if neg is not None:
                check(f'Audit:{name}:negative_final', src, neg, sum(x['final_author_record'] == '2' for x in s) if s else None)
            check(f'Audit:{name}:undecidable_final', src, 0, sum(x['final_author_record'] == '3' for x in s) if s else None)
    p = ROOT / 'results/audit/interval_results.json'
    if not p.exists():
        check('Audit:weighted_rates', 'Section 3.2–3.3', '76.0 / 64.1', None); return
    import json
    j = json.loads(p.read_text(encoding='utf-8'))
    for key, name, est, lo, hi, src in (('A', 'technique', 76.0, 61.2, 87.2, 'Section 3.2 / Table S19'), ('C', 'time', 64.1, 35.9, 86.1, 'Section 3.3 / Table S19')):
        g = j.get(key, {})
        check(f'Audit:{name}:weighted_rate_pct', src, est, round(100 * g.get('weighted_estimate', float('nan')), 1), 0.05)
        ci = g.get('conservative_95_interval', [None, None])
        check(f'Audit:{name}:conservative_interval_low_pct', src, lo, round(100 * ci[0], 1) if ci[0] is not None else None, 0.05)
        check(f'Audit:{name}:conservative_interval_high_pct', src, hi, round(100 * ci[1], 1) if ci[1] is not None else None, 0.05)
    fs = rows('results/audit/final_stratified_counts.csv')
    if fs is not None:
        tech = [x for x in fs if x['stratum'].startswith('A:')]
        check('Audit:technique:population_N', 'Table S18', 8622, sum(int(x['N']) for x in tech))
        check('Audit:technique:sample_n', 'Table S18', 200, sum(int(x['n']) for x in tech))

def check_inputs():
    cd = rows('data/canonical_documents.csv')
    if cd is None:
        check('Inputs:canonical_documents', 'Table 5', 1856, None); return
    final = {x['canonical_document_id'] for x in cd if x['included_in_analytical_corpus'] == 'True'}
    check('Inputs:canonical_documents', 'Table 5', 1856, len(cd)); check('Inputs:final_reports', 'Table 5', 1474, len(final))
    dt = rows('data/document_techniques.csv') or []
    check('Inputs:links', 'Table 5', 4852, len(dt)); check('Inputs:technique_ids', 'Table 5', 449, len({x['canonical_attack_id'] for x in dt}))
    check('Inputs:revoked_links', 'Table 5', 474, sum(x['revoked'] == 'True' for x in dt)); check('Inputs:deprecated_links', 'Table 5', 108, sum(x['deprecated'] == 'True' for x in dt))
    check('Inputs:subtechnique_share_pct', 'Table 5', 39.8, round(100 * sum(x['is_subtechnique'] == 'True' for x in dt) / len(dt), 1) if dt else None, 0.05)
    per = Counter(x['canonical_document_id'] for x in dt)
    check('Inputs:reports_with_techniques', 'Table 5', 941, len(per)); check('Inputs:reports_with_one', 'Table 5', 353, sum(v == 1 for v in per.values())); check('Inputs:reports_with_two_or_more', 'Table 5', 588, sum(v >= 2 for v in per.values()))
    check('Inputs:sum_combination_counts', 'Section 4.2', 66325, sum(v * (v - 1) // 2 for v in per.values()))
    te = rows('data/technique_evidence.csv') or []
    check('Inputs:evidence_items', 'Table 5', 9550, len(te)); check('Inputs:quarantined_items', 'Section 3.2', 313, sum(x['pair_conflict_flag'] == 'True' for x in te))
    check('Inputs:eligible_evidence_ids', 'Table 5', 459, len({x['canonical_attack_id'] for x in te if x['primary_pair_eligible'] == 'True'}))
    check('Inputs:eligible_links_full_scope', 'Section 4.1', 5258, len({(x['canonical_document_id'], x['canonical_attack_id']) for x in te if x['primary_pair_eligible'] == 'True'}))
    check('Inputs:eligible_evidence_final_scope', 'Section 3.2', 8622, sum(x['canonical_document_id'] in final and x['primary_pair_eligible'] == 'True' for x in te))
    rc = Counter(x['rule_id'] for x in te)
    for rule, n in (('P2_DIRECT_EXACT_CANONICAL_NAME', 6900), ('P2_DIRECT_EXPLICIT_EXTERNAL_ID', 2428), ('P2_DIRECT_UNIQUE_NORMALIZED_NAME', 122), ('P2_DIRECT_UNIQUE_BEHAVIOR_LEXICON', 100)):
        check(f'Inputs:rule:{rule}', 'Table 5', n, rc.get(rule))
    ta = rows('data/event_time_assignments.csv')
    check('Inputs:adopted_time_expressions', 'Table 5', 14252, len(ta) if ta is not None else None)
    check('Inputs:adopted_time_expressions_final_scope', 'Table 5', 14236, sum(x['canonical_document_id'] in final for x in ta) if ta is not None else None)
    w = rows('data/document_year_weights.csv')
    check('Inputs:report_year_weights', 'Table 5', 4060, len(w) if w is not None else None)
    check('Inputs:weight_sum_in_period', 'Table 5', 1429.197, round(sum(float(x['weight']) for x in w), 3) if w is not None else None, 0.0005)
    if w is not None:
        yc = Counter(min(v, 4) for v in Counter(x['canonical_document_id'] for x in w).values())
        check('Inputs:years_per_report', 'Table 5', '446/410/252/366', f"{yc[1]}/{yc[2]}/{yc[3]}/{yc[4]}")
    ru = rows('data/relation_universe.csv'); check('Inputs:relation_universe', 'Section 3.3', 28195, len(ru) if ru is not None else None)
    for f, n in (('data/top1_excluded_documents.csv', 15), ('data/top5_excluded_documents.csv', 74)):
        r = rows(f); check(f'Inputs:{f}', 'Section 4.5', n, len(r) if r is not None else None)
    rk = rows('results/initial/figure_05/rich_document_ranking.csv')
    if rk is None:
        check('Figure4:ranking', 'Section S3.4', 'file present', None); return
    v = sorted((int(x['pair_potential']) for x in rk), reverse=True); tot = sum(v); pos = [x for x in v if x > 0]
    check('Figure4:rows', 'Section S3.4', 1474, len(v)); check('Figure4:sum', 'Section S3.4', 66325, tot); check('Figure4:positive', 'Section S3.4', 588, len(pos))
    for k, e in ((15, 67.68), (74, 92.72), (148, 97.47)):
        check(f'Figure4:top{k}_share_pct', 'Section S3.4', e, round(100 * sum(v[:k]) / tot, 2), 0.005)
    for k, e in ((6, 46.87), (30, 80.24), (59, 89.85)):
        check(f'Figure4:positive_top{k}_share_pct', 'Section S3.4', e, round(100 * sum(pos[:k]) / tot, 2), 0.005)
    def gini(a):
        a = sorted(a); n = len(a); return (2 * sum((i + 1) * x for i, x in enumerate(a)) / (n * sum(a))) - (n + 1) / n
    check('Figure4:gini_all', 'Section S3.4', 0.9686, round(gini(v), 4), 0.00005); check('Figure4:gini_positive', 'Section S3.4', 0.9213, round(gini(pos), 4), 0.00005)

S10 = {('baseline', '0.0', 'L0_STAGE15_MATCHED', 'S0_FULL'): {'{R1}': 3, '{R2}': 2}, ('baseline', '0.0', 'L1_EXTENDED', 'S0_FULL'): {'{R2}': 5}, ('baseline', '0.0', 'L2_HIGH', 'S0_FULL'): {'{R2}': 5},
       ('baseline', '0.0', 'L0_STAGE15_MATCHED', 'S1_DROP_TOP1'): {'{R1}': 5}, ('baseline', '0.0', 'L1_EXTENDED', 'S1_DROP_TOP1'): {'{R1}': 5}, ('baseline', '0.0', 'L2_HIGH', 'S1_DROP_TOP1'): {'{R1}': 5},
       ('baseline', '0.0', 'L0_STAGE15_MATCHED', 'S2_DROP_TOP5'): {'{R0}': 5}, ('baseline', '0.0', 'L1_EXTENDED', 'S2_DROP_TOP5'): {'{R0}': 5}, ('baseline', '0.0', 'L2_HIGH', 'S2_DROP_TOP5'): {'{R0,R2}': 5},
       ('baseline', '1e-12', 'L0_STAGE15_MATCHED', 'S0_FULL'): {'{R2}': 5}, ('baseline', '1e-12', 'L1_EXTENDED', 'S0_FULL'): {'{R2}': 5}, ('baseline', '1e-12', 'L2_HIGH', 'S0_FULL'): {'{R2}': 5},
       ('baseline', '1e-12', 'L0_STAGE15_MATCHED', 'S1_DROP_TOP1'): {'{R0}': 4, '{R1}': 1}, ('baseline', '1e-12', 'L1_EXTENDED', 'S1_DROP_TOP1'): {'{R0}': 4, '{R0,R1}': 1}, ('baseline', '1e-12', 'L2_HIGH', 'S1_DROP_TOP1'): {'{R0}': 5},
       ('baseline', '1e-12', 'L0_STAGE15_MATCHED', 'S2_DROP_TOP5'): {'{R0}': 5}, ('baseline', '1e-12', 'L1_EXTENDED', 'S2_DROP_TOP5'): {'{R0}': 5}, ('baseline', '1e-12', 'L2_HIGH', 'S2_DROP_TOP5'): {'{R0}': 5}}

def check_more_tables():
    f = rows('results/main/factorial_followup_180.csv')
    check('TableS10:rows', 'Table S10', 180, len(f) if f is not None else None)
    for (i, t, l, s), e in S10.items():
        cid = f'TableS10:{i}:{t}:{l}:{s}'
        if f is None: check(cid, 'Table S10', str(e), None); continue
        got = Counter(norm_set(x['candidates']) for x in f if x['input'] == i and x['threshold'] == t and x['level'] == l and x['scenario'] == s)
        check(cid, 'Table S10', str(dict(sorted({norm_set(k): v for k, v in e.items()}.items()))), str(dict(sorted(got.items()))))
    b0 = rows('results/main/B0_L2_models.csv')
    for s, e in (('S0_FULL', '{R2}'), ('S1_DROP_TOP1', '{R0}'), ('S2_DROP_TOP5', '{R0}')):
        cid = f'TableS11:{s}'
        if b0 is None: check(cid, 'Table S11', e, None); continue
        got = Counter(norm_set(x['candidates']) for x in b0 if x['scenario'] == s); check(cid, 'Table S11', str({e: 5}), str(dict(got)))
    sl = rows('results/main/figure8_slopes.csv')
    if sl is None:
        check('TableS15:slopes', 'Figure 8 / Table S15', 'file present', None)
    else:
        check('TableS15:rows', 'Table S15', 45, len(sl))
        check('TableS15:same_sign_descriptors', 'Section 4.4', 7, sum(1 for d in {x['descriptor'] for x in sl} if all(x['same_sign'] == 'True' for x in sl if x['descriptor'] == d)))
        for d, wexp, rlo, rhi in (('component_share_death', -0.489, 0.262, 0.265), ('persistent_relation_rms', 0.527, -0.381, -0.322)):
            ws = {round(float(x['W']), 3) for x in sl if x['descriptor'] == d}; rs = [float(x['R']) for x in sl if x['descriptor'] == d]
            check(f'TableS15:{d}:W_slope', 'Section 4.4', wexp, ws.pop() if len(ws) == 1 else None, 0.0005)
            check(f'TableS15:{d}:R_slope_min', 'Section 4.4', rlo, round(min(rs), 3), 0.0005); check(f'TableS15:{d}:R_slope_max', 'Section 4.4', rhi, round(max(rs), 3), 0.0005)
    bs = rows('results/main/B2/B2_selection.csv')
    if bs is None:
        check('TableS16:B2_selection', 'Table S16', 'file present', None)
    else:
        check('TableS16:rows', 'Table S16', 90, len(bs))
        for qp, lam, e in (('reestimated', '1.0', (83, 20, 9)), ('legacy_fixed', '1.0', (723, 174, 86))):
            got = tuple(int(statistics.median(float(x['median_budget']) for x in bs if x['q_policy'] == qp and x['lambda'] == lam and x['scenario'] == s)) for s in SCEN)
            check(f'TableS16:median_budget:{qp}:lambda={lam}', 'Table S16 / Section 4.6', str(e), str(got))
    hb = rows('results/time_revision/v3_1/hold_both_time_assignments_final_scope.csv'); check('TableS22:revised_final_scope', 'Table S22', 14082, len(hb) if hb is not None else None)
    rv = rows('results/time_revision/residual_six/revised_time_assignments_final_scope.csv'); check('TableS22:residual_six_final_scope', 'Table S22', 14076, len(rv) if rv is not None else None)
    tf = rows('results/time_revision/time_flow.csv')
    if tf is not None:
        n = lambda oa, ad=None, rd=None: sum(int(x['count']) for x in tf if x['original_adopted'] == oa and (ad is None or x['automatic_decision'] == ad) and (rd is None or x['reviewed_decision'] == rd))
        check('TableS22:original_adopted', 'Table S22', 14252, n('True')); check('TableS22:removed_in_v1', 'Section S5.5', 93, n('True', 'NOT_ADOPTED_BASELINE'))
        check('TableS22:added_in_v1', 'Section S5.5', 40, n('False') - n('False', 'NOT_ADOPTED_BASELINE'))
        check('TableS22:intermediate_list', 'Section S5.5', 14199, n('True') - n('True', 'NOT_ADOPTED_BASELINE') + n('False') - n('False', 'NOT_ADOPTED_BASELINE'))
        check('TableS22:auto_retained', 'Section S5.5', 14091, n('True', 'RETAIN_BASELINE') + n('False', 'RETAIN_BASELINE'))
        check('TableS22:auto_excluded', 'Section S5.5', 62, n('True', 'EXCLUDE') + n('False', 'EXCLUDE')); check('TableS22:review', 'Section S5.5', 46, n('True', 'REVIEW') + n('False', 'REVIEW'))
    rd = rows('results/time_revision/rule_dependency_links.csv'); check('S5.7:rule_dependent_links', 'Section S5.7', 120, sum(x['exclusive'] == 'True' for x in rd) if rd is not None else None)
    cv = rows('results/time_revision/CVE85_tracking.csv'); check('S5.6:CVE85_rows', 'Section S5.6', 85, len(cv) if cv is not None else None)
    ci = rows('results/time_revision/confirmed_identifier_years.csv'); check('S5.6:confirmed_identifier_years', 'Section S5.6', 6, len(ci) if ci is not None else None)
    cw = rows('results/time_revision/residual_six/changed_weights.csv')
    check('S5.6:changed_weights', 'Section S5.6', 5, len(cw) if cw is not None else None); check('S5.6:reports_affected', 'Section S5.6', 2, len({x['canonical_document_id'] for x in cw}) if cw is not None else None)
    ai = rows('results/time_revision/residual_six/annual_impact.csv'); check('S5.6:max_abs_W_change', 'Section S5.6', 0.001606585, max(float(x['max_abs_W_change']) for x in ai) if ai is not None else None, 5e-10)

def main():
    check_hashes(); check_table7(); check_loto(); check_b2(); check_s14(); check_added(); check_audit(); check_inputs(); check_more_tables()
    w = max(len(r[0]) for r in RESULTS)
    for cid, src, exp, act, tol, st in RESULTS:
        print(f'{st:13s} {cid:{w}s}  expected={exp!s:<40.40} actual={act!s:<40.40} tol={tol}')
    c = Counter(r[5] for r in RESULTS)
    print(f"\nPASS {c['PASS']}  FAIL {c['FAIL']}  NOT_AVAILABLE {c['NOT_AVAILABLE']}")
    out = ROOT / 'docs' / 'verification_results.csv'
    with out.open('w', encoding='utf-8', newline='') as f:
        wr = csv.writer(f); wr.writerow(['check_id', 'source', 'expected_value', 'actual_value', 'tolerance', 'status']); wr.writerows(RESULTS)
    print('written', out.relative_to(ROOT))
    sys.exit(1 if c['FAIL'] or c['NOT_AVAILABLE'] else 0)


if __name__ == '__main__':
    main()
