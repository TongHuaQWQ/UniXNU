"""Target of objects linked into the kernel: architecture and iOS deployment of the kernel build.

The kernel build exports UNIXNU_XNU_ARCH and UNIXNU_IOS_VERSION from the selected profiles. Without them
the arm64 iOS 17.0 target is used.
"""
import os
import struct

ARCH = os.environ.get('UNIXNU_XNU_ARCH', 'arm64')
IOS_VERSION = os.environ.get('UNIXNU_IOS_VERSION', '17.0')
TRIPLE = f'{ARCH}-apple-ios{IOS_VERSION}'
# LC_BUILD_VERSION packs minos as major<<16 | minor<<8 | patch, and clang records all three from the
# -target triple (-target arm64e-apple-ios26.5.2 gives 26.5.2). Dropping the patch component made every
# object of a profile whose ios_version is not x.y.0 look wrong: uke-storage's archives were built at
# 26.5.2 and the check expected 26.5.0 — "deployment (2, 1705218), expected (2, 1705216)".
_parts = (IOS_VERSION.split('.') + ['0', '0'])[:3]
_major, _minor, _patch = (int(part) for part in _parts)
DEPLOYMENT = (2, _major << 16 | _minor << 8 | _patch)
_SUBTYPES = {'arm64': 0, 'arm64e': 2}
if ARCH not in _SUBTYPES:
    raise SystemExit(f'Unsupported kernel architecture {ARCH}')
SUBTYPE = _SUBTYPES[ARCH]


# Flags that turn a compile into LLVM bitcode instead of a native object. The archive builders replay
# the kernel's own compile records, and with XNU_BUILD_LTO=1 those records carry -flto: replaying them
# verbatim produced bitcode, and check_object then rejected it ("ArmDTPlatform: not an arm64e object").
# The archives must stay native -- ld links native objects beside the LTO kernel happily.
BITCODE_FLAGS = ('-flto', '-fno-lto', '-emit-llvm', '-fembed-bitcode')


def native_arguments(arguments):
    """The recorded compile flags with the ones that would emit bitcode removed."""
    return [value for value in arguments if not value.startswith(BITCODE_FLAGS)]


def check_object(data, what):
    """Refuse a relocatable object whose architecture or deployment differs from the kernel target."""
    magic, cpu, subtype, kind, count = struct.unpack_from('<5I', data)
    if (magic, cpu, subtype & 0xff, kind) != (0xfeedfacf, 0x100000c, SUBTYPE, 1):
        raise SystemExit(f'{what}: not an {ARCH} object')
    offset, deployment = 32, None
    for _ in range(count):
        command, length = struct.unpack_from('<II', data, offset)
        if command == 0x32:
            deployment = struct.unpack_from('<II', data, offset + 8)
        offset += length
    if deployment != DEPLOYMENT:
        raise SystemExit(f'{what}: deployment {deployment}, expected {DEPLOYMENT}')
