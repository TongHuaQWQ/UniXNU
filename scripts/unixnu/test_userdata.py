#!/usr/bin/env python3
"""Offline tests of the root manifest's data objects: board declarations, --object, and the refusals.

A board declares its data objects so that a checkout reproduces the userdata image with no command-line
state; --object stays the one-off escape hatch. Both feed collect_objects(), which places each object 1 MiB
aligned after the windows and returns the entries the manifest is written from.

    python3 scripts/unixnu/test_userdata.py
"""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unixnu import userdata

MIB = 1 << 20


class CollectObjects(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.tree = Path(self.directory.name)
        self.ctx = SimpleNamespace(tree=self.tree)

    def write(self, name, size):
        path = self.tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(size))
        return path

    def test_board_declaration_places_objects_after_the_windows(self):
        self.write('scripts/policies/26C5035r/OS/hashes.bin', 4096)
        self.write('scripts/policies/26C5035r/App/hashes.bin', 512)
        spec = {'objects': [{'name': 'OS.vroot', 'path': '{tree}/scripts/policies/26C5035r/OS/hashes.bin'},
                            {'name': 'App.vroot', 'path': '{tree}/scripts/policies/26C5035r/App/hashes.bin'}]}
        objects, cursor = userdata.collect_objects(self.ctx, spec, 5 * MIB, [])
        self.assertEqual([entry[0] for entry in objects], ['OS.vroot', 'App.vroot'])
        self.assertEqual([entry[1] for entry in objects], [5 * MIB, 5 * MIB + MIB])
        self.assertEqual([entry[2] for entry in objects], [4096, 512])
        self.assertEqual(cursor, 7 * MIB)

    def test_offset_skips_the_front_of_the_file(self):
        self.write('firmware.bin', 0x3000)
        spec = {'objects': [{'name': 'firmware', 'path': '{tree}/firmware.bin', 'offset': '0x1000'}]}
        objects, cursor = userdata.collect_objects(self.ctx, spec, MIB, [])
        self.assertEqual(objects[0][2], 0x2000)
        self.assertEqual(objects[0][4], 0x1000)
        self.assertEqual(cursor, 2 * MIB)

    def test_command_line_object_still_works_and_follows_the_board_ones(self):
        self.write('a.bin', 16)
        self.write('b.bin', 16)
        spec = {'objects': [{'name': 'board', 'path': '{tree}/a.bin'}]}
        objects, cursor = userdata.collect_objects(self.ctx, spec, MIB, [f'cli={self.tree / "b.bin"}:8'])
        self.assertEqual([entry[0] for entry in objects], ['board', 'cli'])
        self.assertEqual(objects[1][2], 8)
        self.assertEqual(cursor, 3 * MIB)

    def test_a_name_declared_twice_is_refused(self):
        self.write('a.bin', 16)
        spec = {'objects': [{'name': 'both', 'path': '{tree}/a.bin'}]}
        with self.assertRaises(userdata.Error):
            userdata.collect_objects(self.ctx, spec, MIB, [f'both={self.tree / "a.bin"}'])

    def test_a_missing_file_is_refused(self):
        spec = {'objects': [{'name': 'gone', 'path': '{tree}/absent.bin'}]}
        with self.assertRaises(userdata.Error):
            userdata.collect_objects(self.ctx, spec, MIB, [])

    def test_a_name_too_long_for_the_manifest_is_refused(self):
        self.write('a.bin', 16)
        spec = {'objects': [{'name': 'n' * 32, 'path': '{tree}/a.bin'}]}
        with self.assertRaises(userdata.Error):
            userdata.collect_objects(self.ctx, spec, MIB, [])

    def test_an_entry_that_is_not_a_table_is_refused(self):
        with self.assertRaises(userdata.Error):
            userdata.collect_objects(self.ctx, {'objects': ['OS.vroot=x']}, MIB, [])

    def test_a_malformed_command_line_object_is_refused(self):
        with self.assertRaises(userdata.Error):
            userdata.collect_objects(self.ctx, {}, MIB, ['no-separator'])

    def test_an_offset_past_the_end_is_refused(self):
        self.write('a.bin', 16)
        with self.assertRaises(userdata.Error):
            userdata.collect_objects(self.ctx, {}, MIB, [f'past={self.tree / "a.bin"}:16'])

    def test_no_objects_keeps_the_cursor(self):
        objects, cursor = userdata.collect_objects(self.ctx, {}, 3 * MIB, [])
        self.assertEqual(objects, [])
        self.assertEqual(cursor, 3 * MIB)


if __name__ == '__main__':
    unittest.main()
