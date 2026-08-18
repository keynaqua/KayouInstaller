from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from resourcepacks.runtime import MOD_PACK_IDS, _arrange_packs, _write_override_config


class ResourcePackOrderingTests(unittest.TestCase):
    def test_mod_resources_stay_below_external_packs_in_options_order(self) -> None:
        ordered = _arrange_packs(
            [
                "file/Extra Flowery GUI.zip",
                "mod_resources",
                "file/Colourful Containers.zip",
                "vanilla",
                "file/Overgrown Flowery GUI.zip",
            ],
            "flowery",
        )

        self.assertLess(ordered.index("mod_resources"), ordered.index("file/Colourful Containers.zip"))

    def test_override_defaults_reverse_options_order(self) -> None:
        ordered = ["vanilla", "mod_resources", "file/Base.zip", "file/Overlay.zip"]
        with tempfile.TemporaryDirectory() as directory:
            game_dir = Path(directory)
            _write_override_config(game_dir, ordered)
            path = game_dir / "config" / "resourcepackoverrides.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            mode = path.stat().st_mode

        self.assertEqual(data["default_packs"], list(reversed(ordered)))
        self.assertEqual(data["schema_version"], "2")
        if os.name == "nt":
            self.assertFalse(mode & stat.S_IWRITE)
        for identifier in MOD_PACK_IDS:
            self.assertEqual(data["pack_overrides"][identifier]["default_position"], "BOTTOM")


if __name__ == "__main__":
    unittest.main()
