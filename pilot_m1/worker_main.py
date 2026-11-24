"""Process entry for a single trusted policy."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot_m1.policy import Pilot, encode


if __name__ == '__main__':
    pilot = Pilot(**json.loads(sys.stdin.readline()))
    for line in sys.stdin:
        print(encode(pilot.decide(json.loads(line))),flush=True)
