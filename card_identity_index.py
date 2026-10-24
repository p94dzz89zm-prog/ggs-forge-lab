"""Explicit reviewed card-name bindings; never guess by splitting a name.

A partial identity index does not establish full Oracle or format coverage.
"""
from collections import Counter
import hashlib
import json
from urllib.parse import urlparse

class IdentityIndex:
    def __init__(self,manifest):
        if manifest.get('format')!=1 or not isinstance(manifest.get('cards'),list) or not manifest['cards']:
            raise ValueError('Missing reviewed identity records')
        self.names={};self.canonical=set()
        for c in manifest['cards']:
            canonical=c.get('canonical_name');names=c.get('names');sources=c.get('primary_sources')
            if not isinstance(canonical,str) or not canonical or canonical in self.canonical or not isinstance(names,list) or len(names)<2 or any(not isinstance(n,str) or not n for n in names) or canonical not in names or len(set(names))!=len(names):
                raise ValueError('Ambiguous canonical identity or names')
            if not isinstance(sources,list) or not sources or any(not isinstance(u,str) or urlparse(u).scheme!='https' or urlparse(u).hostname not in {'magic.wizards.com','media.wizards.com','gatherer.wizards.com'} for u in sources):
                raise ValueError('Missing primary identity provenance')
            self.canonical.add(canonical)
            for n in names:
                if n in self.names:raise ValueError('Ambiguous alias shared by identities')
                self.names[n]=canonical
        self.sha256=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def normalize(self,counts):
        result=Counter();bindings=[]
        for name,n in counts.items():
            if not isinstance(name,str) or type(n) is not int or n<1:raise ValueError('Malformed identity multiset')
            canonical=self.names.get(name,name);result[canonical]+=n
            if canonical!=name:bindings.append(dict(recorded_name=name,canonical_name=canonical,count=n))
        return result,bindings
