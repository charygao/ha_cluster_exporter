#!/usr/bin/env python3

import argparse
import json
import sys
import textwrap
from urllib import request
import urllib.error
from datetime import datetime
from datetime import timezone
import tempfile

parser = argparse.ArgumentParser(description="Add a GitHub release to an RPM changelog", usage=argparse.SUPPRESS)
parser.add_argument("repo", help="GitHub repository (owner/name)")
parser.add_argument("-t", "--tag", help="A specific Git tag to get; if none, latest will be used")
parser.add_argument("-a", "--author", help="The author of the RPM changelog entry")
parser.add_argument("-f", "--file", help="Prepend the new changelog entry to file instead of printing in stdout")

if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()

releaseSegment = f"/tags/{args.tag}" if args.tag else "/latest"
url = f'https://api.github.com/repos/{args.repo}/releases{releaseSegment}'

try:
    response = request.urlopen(url)
except urllib.error.HTTPError as error:
    print(f"GitHub API responded with a {error.code} error!", file=sys.stderr)
    print("Url:", url, file=sys.stderr)
    print("Response:", json.dumps(json.load(error), indent=4), file=sys.stderr, sep="\n")
    sys.exit(1)

release = json.load(response)

releaseDate = datetime.strptime(release['published_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

with tempfile.TemporaryFile("r+") as temp:
    print("-------------------------------------------------------------------", file=temp)

    print(f"{releaseDate.strftime('%c')} {releaseDate.strftime('%Z')}", end="", file=temp)
    if args.author:
        print(f" - {args.author}", end="", file=temp)
    print("\n", file=temp)

    print(f"- Release {args.tag}", end="", file=temp)
    if release['name'] and release['name'] != args.tag:
        print(f" - {release['name']}", end="", file=temp)
    print("\n", file=temp)

    if release['body']:
        print(textwrap.indent(release['body'], "  "), file=temp, end="\n\n")
    temp.seek(0)

    if args.file:
        with open(args.file, "r") as prev:
            old = prev.read()
        with open(args.file, "w") as new:
            for line in temp:
                new.write(line)
            new.write(old)
        sys.exit(0)

    print(temp.read())
