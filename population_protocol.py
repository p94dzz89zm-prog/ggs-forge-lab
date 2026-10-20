"""Real Forge personalities; archetypes not implemented are explicitly pending."""
import hashlib
from pathlib import Path

POPULATIONS={
 'stock':('Default','Default','Default','Default'),
 'diverse_training':('Default','Reckless','Cautious','Default'),
 'unseen_evaluation':('Default','Experimental','Experimental','Experimental'),
}

def specification(engine,name):
    if name not in POPULATIONS:raise ValueError('Unknown opponent population')
    profiles=POPULATIONS[name];hashes={}
    for profile in profiles:
        path=Path(engine)/'res/ai'/(profile+'.ai')
        if not path.is_file():raise ValueError('Missing actual Forge personality: '+profile)
        hashes[profile]=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'name':name,'profiles_by_unrotated_deck':list(profiles),'profile_sha256':hashes,
        'implementation':'Forge native heuristic personalities; selected GGS pilot remains separate',
        'coverage_limit':'No verified combo/control/tempo specialist or learned opponent population yet'}

def seat_profiles(profiles,rotation):
    if len(profiles)!=4 or any(not isinstance(x,str) or not x or not x.replace('-','').replace('_','').isalnum() for x in profiles):raise ValueError('Four plain personality names required')
    if type(rotation) is not int or rotation not in range(4):raise ValueError('Invalid seat rotation')
    return list(profiles[rotation:])+list(profiles[:rotation])
