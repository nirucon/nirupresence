"""Regression tests for D-Bus/MPRIS discovery failures."""
import subprocess
import unittest
from unittest.mock import patch

from nirupresence import legacy


class MprisDiscoveryTests(unittest.TestCase):
    @patch("nirupresence.legacy.shutil.which", return_value="/usr/bin/playerctl")
    @patch("nirupresence.legacy.subprocess.run")
    def test_disconnected_bus_is_unavailable(self, run, _which):
        run.return_value = subprocess.CompletedProcess(
            ["playerctl", "-l"], 1, "",
            "Cannot autolaunch D-Bus without X11 $DISPLAY",
        )
        result = legacy.playerctl_metadata()
        self.assertFalse(result["available"])
        self.assertFalse(result["playing"])

    @patch("nirupresence.legacy.shutil.which", return_value="/usr/bin/playerctl")
    @patch("nirupresence.legacy.subprocess.run")
    def test_no_players_is_not_bus_failure(self, run, _which):
        run.return_value = subprocess.CompletedProcess(["playerctl", "-l"], 0, "", "")
        result = legacy.playerctl_metadata()
        self.assertTrue(result["available"])
        self.assertFalse(result["playing"])


if __name__ == "__main__":
    unittest.main()
