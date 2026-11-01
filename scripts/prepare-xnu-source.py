#!/usr/bin/env python3
"""Restore the DriverKit and TrustCache headers newer xnu omits, without the API.

This overrides UniXNU's `scripts/prepare-xnu-source.py`. The original asks
api.github.com for a directory listing and then downloads every header from
raw.githubusercontent.com. Both are unreliable from CI and from the tablet:

  - on the tablet raw.githubusercontent.com resets every connection;
  - on GitHub Actions the unauthenticated API returns HTTP 403 "rate limit
    exceeded", because the runner's address is shared.

The header set is derivable from the pinned source itself, so this version uses
git only: it fetches the two older tags named by feeds.toml into the xnu feed
checkout, lists the files with `git ls-tree`, and writes each one out with
`git show`. Same inputs, same outputs, no network beyond github.com.

The destination paths and the tag defaults are the ones the original uses, so
nothing else in the build has to change.

Two details keep the fetch reliable, because more than one process restores these
headers in a single build: the unixnu driver runs this script before it applies
the patch series and build-xnu-4k-baseline.sh runs it again, in two branches. The
feed checkout is shared by both.

  - every missing tag is fetched in ONE git command, so .git/shallow is rewritten
    once instead of once per tag;
  - the fetch holds an exclusive lock on the feed and retries. git reports
    "fatal: shallow file has changed since we read it" when a second fetch
    rewrites .git/shallow under the first, which is a race, not a bad repository.
"""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time

# feeds.toml sets these for the driver; keep the same defaults.
DRIVERKIT_TAG = os.environ.get('UNIXNU_DRIVERKIT_TAG', 'xnu-10063.121.3')
TRUSTCACHE_TAG = os.environ.get('UNIXNU_TRUSTCACHE_TAG', 'xnu-8796.101.5')

# (tag, directory inside the repository, destination inside .cache/xnu-work)
RESTORES = [
    (DRIVERKIT_TAG, 'iokit/DriverKit', '.cache/xnu-work/iokit/DriverKit'),
    (DRIVERKIT_TAG, 'iokit/DriverKit/crypto', '.cache/xnu-work/iokit/DriverKit/crypto'),
    (TRUSTCACHE_TAG, 'EXTERNAL_HEADERS/TrustCache', '.cache/xnu-work/EXTERNAL_HEADERS/TrustCache'),
]
MANIFEST = Path('.cache/sources/xnu-header-restore.json')


def find_feed():
    """The xnu feed checkout: out/feeds/xnu-<hash>, above the tree at any nesting depth."""
    if not Path('.cache/xnu-work').is_dir():
        sys.exit('Create the local XNU work source before preparing headers')
    here = Path.cwd()
    for base in (here, *here.parents):
        feeds = sorted((base / 'feeds').glob('xnu-*'))
        if feeds:
            return feeds[0]
    sys.exit('no xnu feed checkout found')


def git(repo, *arguments, check=True):
    result = subprocess.run(['git', '-C', str(repo), *arguments], capture_output=True)
    if check and result.returncode != 0:
        sys.exit(f'git {" ".join(arguments)} failed: {result.stderr.decode()[:300]}')
    return result


def feed_lock(repo):
    """Hold the feed's shallow file against the other process that restores these headers."""
    handle = (repo / '.git' / 'unixnu-prepare-xnu-source.lock').open('w')
    fcntl.flock(handle, fcntl.LOCK_EX)
    return handle


def ensure_tags(repo, tags):
    """Fetch every missing tag in one command: one rewrite of .git/shallow, then retry a racy one."""
    missing = [tag for tag in tags
               if git(repo, 'rev-parse', '--verify', '-q', f'{tag}^{{commit}}', check=False).returncode != 0]
    if not missing:
        return
    print(f'  fetching tag{"s" if len(missing) > 1 else ""} {" ".join(missing)}')
    arguments = ['fetch', '-q', '--depth', '1', 'origin']
    for tag in missing:
        arguments += ['tag', tag]
    for attempt in range(1, 4):
        result = git(repo, *arguments, check=False)
        if result.returncode == 0:
            return
        message = result.stderr.decode().strip()[:300]
        if 'shallow file has changed' not in message or attempt == 3:
            sys.exit(f'git {" ".join(arguments)} failed: {message}')
        print(f'  shallow file changed under the fetch, retrying ({attempt}/3)')
        time.sleep(2 * attempt)


def list_headers(repo, tag, directory):
    names = git(repo, 'ls-tree', '-r', '--name-only', tag, directory).stdout.decode().splitlines()
    return [name for name in names if name.endswith('.h')]


def main():
    repo = find_feed()
    print(f'prepare-xnu-source: feed {repo}')
    held = feed_lock(repo)
    ensure_tags(repo, list(dict.fromkeys(tag for tag, _, _ in RESTORES)))
    restored = []
    for tag, directory, destination in RESTORES:
        headers = list_headers(repo, tag, directory)
        target_dir = Path(destination)
        written = 0
        for path in headers:
            name = path[len(directory) + 1:]
            target = target_dir / name
            if target.exists():
                continue
            data = git(repo, 'show', f'{tag}:{path}').stdout
            if not data:
                sys.exit(f'{tag}:{path} is empty')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            written += 1
            restored.append({
                'path': str(target),
                'source': f'{tag}:{path}',
                'sha256': hashlib.sha256(data).hexdigest(),
            })
        print(f'  {directory} @ {tag}: {len(headers)} headers, {written} written')

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({'headers': restored}, indent=2) + '\n')
    print(f'prepare-xnu-source: {len(restored)} headers restored, manifest {MANIFEST}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
