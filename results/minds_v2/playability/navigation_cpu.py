#!/usr/bin/env python3
"""Reproduce actual movement CPU measurements, without HTTP or a browser.

Every timed call is the shipped RebirthWorld.move revision1 or revision2,
including its route validation, resulting world-time advance and ledger/memory
work. The identical boot-state deepcopy, source hashing, setup and result
serialization occur outside the timer. This is not isolated pathfinding time,
HTTP latency, a rendering benchmark, or a human playtest.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from kalends.pompeii.district import LOCATIONS, PompeiiConfig
from kalends_rebirth.navigation_v2 import path_distance, point_walkable, segment_walkable
from kalends_rebirth.world import RebirthWorld


def room_start(name):
    room = next(r for r in LOCATIONS if r['id'] == name)
    return [room['x']+room['w']*.5, room['y']+room['h']*.85]


def queries():
    common = [
        {'id':'horizontal_260', 'start':[650,415], 'current':'street', 'body':{'x':910,'y':415}},
        {'id':'corridor_vertical_26', 'start':[770,650], 'current':'street', 'body':{'x':770,'y':676}},
        {'id':'corridor_diagonal', 'start':[770,650], 'current':'street', 'body':{'x':800,'y':676}},
        {'id':'concave_corner', 'start':[385,480], 'current':'street', 'body':{'x':770,'y':790}},
    ]
    for origin, target in [('bakery','household'), ('household','thermopolium'),
                           ('thermopolium','fullery'), ('fullery','bakery')]:
        common.append({'id':origin+'_to_'+target, 'start':room_start(origin),
                       'current':origin, 'body':{'location':target}})
    return common


def percentile(values, percentile):
    ordered = sorted(values)
    # Explicit nearest-rank rule, applied equally to all samples.
    return ordered[max(0, min(len(ordered)-1, math.ceil(len(ordered)*percentile)-1))]


def summary(values):
    return {'n':len(values), 'p50':percentile(values,.5), 'p95':percentile(values,.95),
            'p99':percentile(values,.99), 'min':min(values), 'max':max(values),
            'mean':statistics.fmean(values)}


def sources():
    files = [*ROOT.joinpath('kalends').rglob('*.py'), *ROOT.joinpath('kalends_rebirth').rglob('*.py')]
    files.append(Path(__file__).resolve())
    hashes = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    digest = hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'hash_algorithm':'sha256 of compact sorted JSON file-hash mapping', 'composite_sha256':digest, 'files':hashes}


def execute(template, query, revision):
    world = copy.deepcopy(template)
    # Identical fixture setup, deliberately outside the timer. No user journal
    # or operational memory is imported. Both modes receive the exact same
    # valid starting floor and request.
    world.positions['Player'] = tuple(query['start'])
    world.state.agent_locations['Player'] = query['current']
    world.player_path = []
    world._movement_revision = revision
    before = world.minute
    started = time.perf_counter_ns()
    receipt = world.move(**query['body'])
    elapsed = time.perf_counter_ns()-started
    path = receipt['payload']['path']
    destination = world.state.agent_locations['Player']
    named_rooms = tuple(name for name in (query['current'], destination) if name != 'street')
    record = {
        'path':path, 'distance':path_distance(path), 'world_minutes':world.minute-before,
        'end':list(world.positions['Player']), 'location':destination,
        'start_on_declared_floor':point_walkable(query['start'],query['current']),
        'end_on_declared_floor':point_walkable(world.positions['Player'],destination),
        'complete_segments_on_authored_floor':all(segment_walkable(a,b,rooms=named_rooms) for a,b in zip(path,path[1:])),
        'ledger_hash':world.ledger.content_hash(),
    }
    return elapsed, record


def run(iterations, warmups):
    template = RebirthWorld(PompeiiConfig(seed=79), optimized=True)
    query_list = queries()
    samples = {q['id']:{'v1':[], 'v2':[]} for q in query_list}
    outcomes = {q['id']:{} for q in query_list}
    started = time.perf_counter()
    for phase, count in [('warmup',warmups),('measured',iterations)]:
        for repetition in range(count):
            # Rotate query position and alternate paired arm order, limiting
            # systematic first-arm and late-run effects without a random seed.
            rotated = query_list[repetition % len(query_list):]+query_list[:repetition % len(query_list)]
            for offset, query in enumerate(rotated):
                order = (1,2) if (repetition+offset)%2 == 0 else (2,1)
                for revision in order:
                    elapsed, result = execute(template,query,revision)
                    name = 'v'+str(revision)
                    if name in outcomes[query['id']]:
                        if result != outcomes[query['id']][name]:
                            raise AssertionError('Non-deterministic outcome: '+query['id']+'/'+name)
                    else: outcomes[query['id']][name] = result
                    if phase == 'measured': samples[query['id']][name].append(elapsed)
    elapsed_seconds = time.perf_counter()-started
    try: commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except (OSError, subprocess.CalledProcessError): commit = None
    results = []
    for query in query_list:
        arms = {}
        for arm in ('v1','v2'):
            durations = samples[query['id']][arm]
            arms[arm] = {'outcome':outcomes[query['id']][arm], 'cpu_duration_ns':summary(durations), 'raw_duration_ns':durations}
        results.append({'query':query, 'arms':arms})
    return {
        'schema_version':1, 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'method':'Actual RebirthWorld.move revision1 versus revision2, route plus induced simulation/event/memory CPU; fresh identical copied boot state per call.',
        'excluded_from_timer':['world construction','deepcopy and fixture setup','hashing and outcome validation','HTTP','snapshot serialization','journal IO','browser and rendering'],
        'limits':['Eight fixed common valid routes, not an exhaustive map or workload.',
                  'V1 and V2 can advance different world minutes, so different amounts of consequence work are included.',
                  'perf_counter_ns measures elapsed monotonic wall duration of the synchronous CPU call; OS scheduling can contribute noise.',
                  'No confidence interval, significance claim, browser FPS inference or human playability conclusion is supplied.'],
        'runtime':{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
                   'machine':platform.machine(),'processor':platform.processor(),'cpu_count':os.cpu_count()},
        'source':{'git_head':commit, **sources()},
        'protocol':{'iterations_per_query_arm':iterations,'warmups_per_query_arm':warmups,'queries':len(query_list),
                    'timed_calls':iterations*len(query_list)*2,'warmup_calls':warmups*len(query_list)*2,
                    'order':'rotate query order each repetition; alternate paired arm order by repetition plus offset',
                    'quantiles':'nearest-rank, ceil(p*n)-1; nanoseconds','seed':79,'optimized':True,
                    'gc':'normal Python GC left enabled','minds':'unactivated; movement revisions only'},
        'total_run_seconds_including_setup':elapsed_seconds, 'results':results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iterations',type=int,default=200)
    parser.add_argument('--warmups',type=int,default=20)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('navigation_cpu.json'))
    args = parser.parse_args()
    if args.iterations < 100 or args.warmups < 1: parser.error('Use at least100 measured repetitions and one warmup per query arm')
    result = run(args.iterations,args.warmups)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':str(args.output.resolve()), 'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
                      'timed_calls':result['protocol']['timed_calls'], 'source_sha256':result['source']['composite_sha256']},indent=2))
    for row in result['results']:
        a,b = row['arms']['v1'],row['arms']['v2']
        print(row['query']['id'],
              'p50 us',round(a['cpu_duration_ns']['p50']/1000,1),'->',round(b['cpu_duration_ns']['p50']/1000,1),
              'distance',round(a['outcome']['distance'],2),'->',round(b['outcome']['distance'],2),
              'world minutes',a['outcome']['world_minutes'],'->',b['outcome']['world_minutes'])

if __name__ == '__main__':main()
