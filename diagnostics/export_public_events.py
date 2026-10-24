"""Export only public game-event categories; retain raw logs separately."""
import argparse
from pathlib import Path
PREFIXES=('Turn: ','Phase: ','Add To Stack: ','Damage: ','Game Result: ','DragonMind Result: ','Match Result: ')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
    a.destination.write_text('\n'.join(line.rstrip() for line in a.source.read_text().splitlines() if line.startswith(PREFIXES))+'\n')
