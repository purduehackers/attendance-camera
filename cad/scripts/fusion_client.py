#!/usr/bin/env python3
"""Small local Fusion MCP client; negotiates a session instead of storing one."""
import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.request

URL = os.environ.get('FUSION_MCP_URL', 'http://127.0.0.1:27182/mcp')
SESSION = os.environ.get('FUSION_MCP_SESSION')
COUNTER = 0


def rpc(method, params, notification=False):
    global SESSION, COUNTER
    COUNTER += 1
    payload = {'jsonrpc': '2.0', 'method': method, 'params': params}
    if not notification:
        payload['id'] = COUNTER
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if SESSION:
        headers['MCP-Session-Id'] = SESSION
    request = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        SESSION = response.headers.get('Mcp-Session-Id', SESSION)
        body = response.read().decode()
        if notification or not body.strip():
            return None
        if 'text/event-stream' in response.headers.get('Content-Type', ''):
            messages = [json.loads(line[5:].strip()) for line in body.splitlines() if line.startswith('data:')]
            result = next(message for message in messages if message.get('id') == COUNTER)
        else:
            result = json.loads(body)
    if 'error' in result:
        raise RuntimeError(result['error'])
    return result['result']


def initialize():
    if not SESSION:
        rpc('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'attendance-camera-cad', 'version': '1.0'}})
        rpc('notifications/initialized', {}, notification=True)


def call(name, args):
    initialize()
    return rpc('tools/call', {'name': name, 'arguments': args})


def execute(path, read_only=False):
    path = Path(path).resolve()
    # Import as a module so portable __file__ paths resolve inside Fusion.
    script = ('import importlib.util, sys\n'
              f'sys.path.insert(0, {str(path.parent)!r})\n'
              f'_spec = importlib.util.spec_from_file_location("attendance_camera_task", {str(path)!r})\n'
              '_module = importlib.util.module_from_spec(_spec)\n'
              '_spec.loader.exec_module(_module)\n'
              'def run(_context: str):\n    _module.run(_context)\n')
    return call('fusion_mcp_execute', {'featureType': 'script', 'object': {'script': script, 'readOnly': read_only}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    script = sub.add_parser('script')
    script.add_argument('path', type=Path)
    script.add_argument('--read-only', action='store_true')
    tool = sub.add_parser('call')
    tool.add_argument('name')
    tool.add_argument('arguments', help='JSON object')
    args = parser.parse_args()
    result = execute(args.path, args.read_only) if args.mode == 'script' else call(args.name, json.loads(args.arguments))
    for block in result.get('content', []):
        if block.get('type') == 'text':
            print(block['text'])
            # Fusion can report script failure inside a successful MCP envelope.
            try:
                parsed = json.loads(block['text'])
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict) and parsed.get('success') is False:
                result['isError'] = True
        elif block.get('type') == 'image':
            target = Path(__file__).parent / 'fusion-preview.png'
            target.write_bytes(base64.b64decode(block['data']))
            print('Image saved:', target)
    if result.get('isError'):
        sys.exit(1)


if __name__ == '__main__':
    main()
