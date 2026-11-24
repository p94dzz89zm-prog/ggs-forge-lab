"""Replay one actor's calculations and print a short position lesson."""
import argparse
import json
from pathlib import Path
from .policy import Pilot


def replay(config, records):
    agent = Pilot(**config)
    for row in records:
        if agent.decide(row['offer']) != row:
            raise ValueError('Recorded calculations diverge')
        yield row


def lesson(row):
    h = row['offer']['observation']
    calc = row['calculations']
    return (f"Seat {row['offer']['seat']} saw {h['lands']} land options and "
            f"{h['early']} early spells. Cheap commander available: {h['cheap_commander']}. "
            f"The keep score was {calc['scores']['keep']} with contributions "
            f"{calc['keep_terms']}. The redraw score was {calc['scores']['redraw']}. "
            f"The pilot chose {row['selection']['token']} and rejected {', '.join(row['rejected'])}. "
            f"Exploration margin: {calc['margin']}. The scores are heuristic estimates. "
            "Game outcome and subsequent strategic assessment are unknown.")


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pilot_directory',type=Path)
    a=parser.parse_args().pilot_directory
    with (a/'decisions.jsonl').open() as stream:
        for r in replay(json.loads((a/'config.json').read_text()),map(json.loads,stream)):
            print(lesson(r))
