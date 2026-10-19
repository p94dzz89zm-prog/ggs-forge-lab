"""Overlay fail-closed controller interception on the exact X-provenance engine."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from executable_delta import digest, publish

ROOT = Path(__file__).resolve().parent
BASE = 'b86b45e274b8515e9105b1ed3b63402c3c044ee9c5f65af0a04a9631b834af29'
EXPORTS = ['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED',
           '--add-exports=java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if digest(args.base) != BASE:
        raise ValueError('Exact verified X-provenance executable required')
    if args.output.exists() or Path('/workspace') in args.output.resolve().parents:
        raise ValueError('Fresh output outside synchronized workspace required')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output.parent) as temporary:
        root = Path(temporary)
        classes, inputs, overlay = root / 'classes', root / 'input', root / 'overlay'
        classes.mkdir(); inputs.mkdir(); overlay.mkdir()
        source = ROOT / 'pilot-src/forge/ai/bridge/DecisionReplay.java'
        subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', *EXPORTS,
                        '-cp', str(args.base), '-d', str(classes), str(source),
                        str(ROOT / 'EvidenceInstrumenter.java'), str(ROOT / 'DecisionReplayInstrumenter.java')], check=True)
        controllers = ['forge/ai/PlayerControllerAi.class', 'forge/ai/bridge/PlayerControllerBridge.class',
                       'forge/game/player/PlayerController.class']
        with zipfile.ZipFile(args.base) as archive:
            for name in controllers:
                path = inputs / name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(name))
        subprocess.run(['java', *EXPORTS, '-cp', str(classes) + ':' + str(args.base),
                        'DecisionReplayInstrumenter', str(inputs), str(overlay)], check=True)
        changes = {name: (overlay / name).read_bytes() for name in controllers}
        changes['forge/ai/bridge/DecisionReplay.class'] = (classes / 'forge/ai/bridge/DecisionReplay.class').read_bytes()
        staged = root / 'engine.jar'
        with zipfile.ZipFile(args.base) as old, zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED) as new:
            for entry in old.infolist():
                new.writestr(entry, changes.get(entry.filename, old.read(entry.filename)))
            new.writestr('forge/ai/bridge/DecisionReplay.class', changes['forge/ai/bridge/DecisionReplay.class'])
        publish(staged, args.output)
        hooks = (overlay / 'decision-hooks.txt').read_text()
        args.output.with_suffix('.hooks.txt').write_text(hooks)
    manifest = {'base_sha256': BASE, 'sha256': digest(args.output), 'classes': sorted(changes),
                'default_enabled': False, 'supported_families': ['bounded_number', 'cards_for_effect', 'priority_pass', 'replacement_choice', 'counter_choice', 'color_choice'],
                'unsupported_decisions': 'fatal; no AI fallback', 'full_game_replay': False,
                'source_sha256': digest(source)}
    args.output.with_suffix('.build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
