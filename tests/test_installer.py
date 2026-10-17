import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "install.sh"


class InstallerSandboxTests(unittest.TestCase):
    def run_installer(
        self,
        distro,
        id_like="",
        systemd=False,
        nirupi=False,
        xinit=False,
        systemctl_ok=True,
    ):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        home = root / "home"
        home.mkdir()
        bin_dir = root / "bin"
        bin_dir.mkdir()
        os_release = root / "os-release"
        os_release.write_text(f'ID={distro}\nID_LIKE="{id_like}"\n')
        systemd_runtime = root / "systemd-runtime"
        if systemd:
            systemd_runtime.mkdir()
        systemctl_log = root / "systemctl.log"

        for name in ("playerctl", "flock"):
            tool = bin_dir / name
            tool.write_text("#!/bin/sh\nexit 0\n")
            tool.chmod(0o755)
        systemctl = bin_dir / "systemctl"
        systemctl.write_text(
            f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{systemctl_log}"\n'
            f"exit {0 if systemctl_ok else 1}\n"
        )
        systemctl.chmod(0o755)
        sudo = bin_dir / "sudo"
        sudo.write_text("#!/bin/sh\nexit 99\n")
        sudo.chmod(0o755)

        if nirupi:
            local_bin = home / ".local/bin"
            local_bin.mkdir(parents=True)
            entry = local_bin / "nirupi-autostart.sh"
            entry.write_text("#!/bin/sh\ntrue\n")
            entry.chmod(0o755)
        if xinit:
            (home / ".config/xinitrc.d").mkdir(parents=True)
            (home / ".xinitrc").write_text(
                'for f in "$HOME/.config/xinitrc.d/"*.sh; do . "$f"; done\n'
            )
            autostart = home / ".config/autostart"
            autostart.mkdir(parents=True)
            disabled = autostart / "nirupresence.desktop.disabled"
            disabled.write_text("[Desktop Entry]\nName=NIRUPRESENCE\n")

        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "NIRUPRESENCE_OS_RELEASE": str(os_release),
                "NIRUPRESENCE_SYSTEMD_RUNTIME": str(systemd_runtime),
                "PATH": ":".join(
                    [
                        str(bin_dir),
                        str(Path(sys.executable).parent),
                        "/usr/local/bin",
                        "/usr/bin",
                        "/bin",
                    ]
                ),
            }
        )
        result = subprocess.run(
            ["bash", str(INSTALL)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        return result, home, systemctl_log

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_debian_uses_systemd(self):
        result, home, systemctl_log = self.run_installer("debian", systemd=True)
        self.assert_ok(result)
        self.assertTrue((home / ".config/systemd/user/nirupresence.service").is_file())
        self.assertIn("enable --now nirupresence.service", systemctl_log.read_text())
        self.assertFalse((home / ".config/autostart/nirupresence.desktop").exists())

    def test_arch_and_arch_derivatives_use_systemd(self):
        for distro, id_like in (("arch", ""), ("endeavouros", "arch")):
            with self.subTest(distro=distro):
                result, home, systemctl_log = self.run_installer(
                    distro, id_like=id_like, systemd=True
                )
                self.assert_ok(result)
                self.assertTrue(
                    (home / ".config/systemd/user/nirupresence.service").is_file()
                )
                self.assertIn(
                    "enable --now nirupresence.service", systemctl_log.read_text()
                )

    def test_systemd_failure_falls_back_to_graphical_autostart(self):
        result, home, _ = self.run_installer(
            "debian", systemd=True, systemctl_ok=False
        )
        self.assert_ok(result)
        self.assertTrue((home / ".config/autostart/nirupresence.desktop").is_file())
        self.assertIn("Graphical-session autostart installed", result.stdout)

    def test_void_installs_every_applicable_session_hook(self):
        result, home, _ = self.run_installer(
            "void", nirupi=True, xinit=True
        )
        self.assert_ok(result)
        self.assertTrue(
            (home / ".config/nirupi/autostart/50-nirupresence.sh").is_file()
        )
        self.assertTrue(
            (home / ".config/xinitrc.d/80-nirupresence.sh").is_file()
        )
        self.assertTrue((home / ".config/autostart/nirupresence.desktop").is_file())
        self.assertFalse(
            (home / ".config/autostart/nirupresence.desktop.disabled").exists()
        )

    def test_void_without_session_specific_hooks_uses_xdg(self):
        result, home, _ = self.run_installer("void")
        self.assert_ok(result)
        self.assertTrue((home / ".config/autostart/nirupresence.desktop").is_file())
        self.assertFalse((home / ".config/nirupi/autostart/50-nirupresence.sh").exists())
        self.assertFalse((home / ".config/xinitrc.d/80-nirupresence.sh").exists())

    def test_unsupported_distro_fails_cleanly(self):
        result, home, _ = self.run_installer("fedora")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported distro fedora", result.stderr)
        self.assertFalse((home / ".local/share/nirupresence/app").exists())


if __name__ == "__main__":
    unittest.main()
