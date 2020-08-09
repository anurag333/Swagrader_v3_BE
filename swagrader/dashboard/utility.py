from .models import *
import random

def get_probes(subs, strategy='random'):
    if strategy == 'random':
        sub_ids = set()
        for sub in subs:
            sub_ids.add(sub.sub_id)
        probes = []
        for _ in range(assign.assignment_peergrading_profile.n_probes):
            id = random.choice(tuple(sub_ids))
            sub = subs.objects.get(sub_id=id)
            probe = ProbeSubmission.objects.create(parent_sub=sub)
            sub_ids.remove(id)
            probes.append({'probe_id': probe.probe_id})
        
        return probes

