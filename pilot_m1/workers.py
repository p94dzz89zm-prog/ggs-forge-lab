"""One private pipe, process, policy snapshot and journal per pilot."""
from contextlib import ExitStack
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from .policy import Pilot, Policy, encode, fingerprint, unpack


def save_version(root, identity, snapshot):
    """Append an immutable version in this identity's own store. Loading an older ID rolls back."""
    Policy.restore(snapshot)
    directory = Path(root)/('pilot-%d' % identity)
    directory.mkdir(parents=True,exist_ok=True)
    key = fingerprint(snapshot)
    with sqlite3.connect(directory/'policies.sqlite3') as db:
        db.execute('CREATE TABLE IF NOT EXISTS policies (id TEXT PRIMARY KEY, snapshot TEXT NOT NULL)')
        if snapshot['parent'] is not None:
            load_version(root,identity,snapshot['parent'])
        db.execute('INSERT OR IGNORE INTO policies VALUES (?,?)',(key,encode(snapshot)))
    load_version(root,identity,key)
    return key


def load_version(root, identity, key):
    path = Path(root)/('pilot-%d' % identity)/'policies.sqlite3'
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as db:
        row = db.execute('SELECT snapshot FROM policies WHERE id=?',(key,)).fetchone()
    if not row or fingerprint(json.loads(row[0])) != key:
        raise ValueError('Unknown or corrupt pilot checkpoint')
    checkpoint = json.loads(row[0])
    Policy.restore(checkpoint)
    return checkpoint


class Pod:
    def __init__(self, configurations, directory):
        if (len(configurations) != 4 or {c['seat'] for c in configurations} != set(range(4))
                or {c['identity'] for c in configurations} != set(range(4))
                or len({c['mode'] for c in configurations}) != 1):
            raise ValueError('Four independent seats and equal evaluation mode required')
        for cfg in configurations:
            Pilot(**cfg)
        self.config = {c['seat']: json.loads(encode(c)) for c in configurations}
        self.directory = Path(directory)
        self.children = {}
        self.journals = {}
        self.stack = ExitStack()

    def __enter__(self):
        self.directory.mkdir(exist_ok=False,parents=True)
        try:
            for seat, cfg in self.config.items():
                sub = self.directory/('pilot-%s' % cfg['identity'])
                sub.mkdir()
                log = self.stack.enter_context((sub/'decisions.jsonl').open('x'))
                (sub/'config.json').write_text(encode(cfg)+'\n')
                err = self.stack.enter_context((sub/'worker.stderr').open('x'))
                # A fresh interpreter imports only this implementation and reads this seat's pipe.
                child = subprocess.Popen([sys.executable,'-I','-u',
                          str(Path(__file__).with_name('worker_main.py').resolve())],
                          cwd=sub,env={},stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                          stderr=err,text=True)
                self.stack.callback(self._stop,child)
                self.children[seat], self.journals[seat] = child, log
                child.stdin.write(encode(cfg)+'\n')
                child.stdin.flush()
            return self
        except BaseException:
            self.stack.close()
            raise

    @staticmethod
    def _stop(child):
        try:
            child.stdin.close()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        finally:
            child.stdout.close()

    def __exit__(self,*exc):
        self.stack.close()

    def choose(self, raw):
        _, offer = unpack(raw)
        cfg = self.config[raw['seat']]
        child = self.children[raw['seat']]
        child.stdin.write(encode(raw)+'\n')
        child.stdin.flush()
        line = child.stdout.readline()
        if not line:
            raise RuntimeError('Pilot stopped without a decision')
        record = json.loads(line)
        selection = record['selection']
        if (selection['actor'] != offer.actor or selection['game'] != offer.game
                or selection['revision'] != offer.revision or selection['token'] not in raw['actions']
                or record['offer'] != raw or record['policy'] != fingerprint(cfg['checkpoint'])
                or record['pilot'] != cfg['identity']):
            raise ValueError('Unbound pilot selection')
        log = self.journals[raw['seat']]
        log.write(encode(record)+'\n')
        log.flush()
        return selection
