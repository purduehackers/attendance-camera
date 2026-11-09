#!/usr/bin/env python3
"""Render the deployed camera configuration without committing device identity."""
import argparse
import ipaddress
from pathlib import Path
import re

TAILNET = ipaddress.ip_network('100.64.0.0/10')
PROJECT = Path(__file__).resolve().parents[1]
HERE = PROJECT / 'install'


def render(tailscale_ip, service_user):
    address = ipaddress.ip_address(tailscale_ip)
    if address.version != 4 or address not in TAILNET:
        raise ValueError('Use this Pi\'s Tailscale IPv4 address, not a LAN or wildcard address.')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}', service_user):
        raise ValueError('Invalid Linux service user name.')
    result = {}
    for name in ('mediamtx.yml', 'camera-feed.service'):
        text = (HERE / (name + '.in')).read_text()
        result[name] = text.replace('__TAILSCALE_IP__', str(address)).replace('__SERVICE_USER__', service_user)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tailscale-ip', required=True)
    parser.add_argument('--user', required=True, help='Existing local Linux account')
    parser.add_argument('--output', type=Path, default=HERE.parent / 'build' / 'config')
    args = parser.parse_args()
    files = render(args.tailscale_ip, args.user)
    args.output.mkdir(parents=True, exist_ok=True)
    args.output.chmod(0o700)
    for name, text in files.items():
        path = args.output / name
        path.write_text(text)
        path.chmod(0o600)
    print(f'Rendered {len(files)} files in {args.output}')


if __name__ == '__main__':
    main()
