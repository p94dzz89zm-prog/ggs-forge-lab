#!/usr/bin/env python3
"""Request-bound file client for the assisted Forge seat. Python 3, stdlib only."""
import argparse
import json
import os
from pathlib import Path
import time


def read_request(directory):
    return json.loads((directory / 'request.json').read_text(encoding='utf-8'))


def respond(directory, request_id, payload):
    current = read_request(directory)
    if current['request_id'] != request_id:
        raise ValueError('Request changed; inspect the new request before responding')
    if (directory / 'response.json').exists():
        raise ValueError('A response is already pending')
    if 'request_id' in payload and payload['request_id'] != request_id:
        raise ValueError('Payload belongs to another request')
    payload['request_id'] = request_id
    temporary = directory / 'client-response.tmp'
    temporary.write_text(json.dumps(payload), encoding='utf-8')
    os.replace(temporary, directory / 'response.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('show')
    answer = sub.add_parser('respond')
    answer.add_argument('request_id')
    answer.add_argument('json_payload')
    sub.add_parser('interactive')
    args = parser.parse_args()
    if args.command == 'show':
        print(json.dumps(read_request(args.directory), indent=2))
    elif args.command == 'respond':
        respond(args.directory, args.request_id, json.loads(args.json_payload))
    else:
        previous = None
        while True:
            try:
                q = read_request(args.directory)
            except FileNotFoundError:
                time.sleep(.1)
                continue
            if q['request_id'] == previous:
                time.sleep(.1)
                continue
            print(json.dumps(q, indent=2), flush=True)
            try:
                payload = json.loads(input('Response JSON (or {"auto":true} to delegate): '))
                respond(args.directory, q['request_id'], payload)
            except (ValueError, KeyError) as error:
                print(str(error), flush=True)
                continue
            previous = q['request_id']


if __name__ == '__main__':
    main()
