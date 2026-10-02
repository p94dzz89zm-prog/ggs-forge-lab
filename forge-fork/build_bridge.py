#!/usr/bin/env python3
"""Clone pinned upstream Forge, apply our GPL patch, and build/test it."""
import argparse
from pathlib import Path
import subprocess
import shutil

PIN = '4ec5f1a2c32fa90ecb983a72b9eb47aa5c5d7676'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path, help='New directory for the source checkout')
    parser.add_argument('--maven', default='mvn')
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    if checkout.exists():
        raise SystemExit('Choose a new directory; existing checkouts are not overwritten')
    subprocess.run(['git', 'clone', '--depth', '1', '--branch', 'forge-2.0.15',
                    'https://github.com/Card-Forge/forge.git', str(checkout)], check=True)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
    if actual != PIN:
        raise SystemExit('Upstream tag differs from audited commit; stopping')
    subprocess.run(['git', 'switch', '-c', 'ggs-assisted-bridge'], cwd=checkout, check=True)
    patch = Path(__file__).with_name('forge.patch').resolve()
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=checkout, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=checkout, check=True)
    followup = Path(__file__).with_name('commander-identity-followup.patch').resolve()
    subprocess.run(['git', 'apply', '--check', str(followup)], cwd=checkout, check=True)
    subprocess.run(['git', 'apply', str(followup)], cwd=checkout, check=True)
    performance = Path(__file__).with_name('dragonmind-performance.patch').resolve()
    subprocess.run(['git', 'apply', '--check', str(performance)], cwd=checkout, check=True)
    subprocess.run(['git', 'apply', str(performance)], cwd=checkout, check=True)
    v2 = Path(__file__).with_name('dragonmind-rules-performance-v2.patch').resolve()
    subprocess.run(['git', 'apply', '--check', str(v2)], cwd=checkout, check=True)
    subprocess.run(['git', 'apply', str(v2)], cwd=checkout, check=True)
    v3 = Path(__file__).with_name('dragonmind-performance-v3.patch').resolve()
    subprocess.run(['git', 'apply', '--check', str(v3)], cwd=checkout, check=True)
    subprocess.run(['git', 'apply', str(v3)], cwd=checkout, check=True)
    subprocess.run([args.maven, '-pl', 'forge-gui-desktop', '-am', 'test',
                    '-Dtest=BridgeEngineTest,GgsPilotTest,DragonMindPerformanceTest', '-Dsurefire.failIfNoSpecifiedTests=false',
                    '-Djava.awt.headless=true'], cwd=checkout, check=True)
    subprocess.run([args.maven, '-pl', 'forge-gui-desktop', '-am', 'package', '-DskipTests'],
                   cwd=checkout, check=True)
    target = checkout / 'forge-gui-desktop' / 'target'
    shutil.copy2(target / 'forge-gui-desktop-2.0.15-jar-with-dependencies.jar', target / 'dragonmind.jar')
    print('Built DragonMind at', target / 'dragonmind.jar')


if __name__ == '__main__':
    main()
