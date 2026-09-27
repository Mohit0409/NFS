from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class NamedRuntimeRegressionTests(unittest.TestCase):
    def test_runtime_never_uses_quick_tunnel(self):
        source = (ROOT / "nfs-runtime.sh").read_text(encoding="utf-8")
        self.assertNotIn("trycloudflare.com", source)
        self.assertIn('TUNNEL_NAME="nfs-nmh"', source)
        self.assertIn('cloudflared --config "$TUNNEL_CONFIG" tunnel run "$TUNNEL_NAME"', source)

    def test_runtime_requires_owned_pids_and_a_single_release(self):
        source = (ROOT / "nfs-runtime.sh").read_text(encoding="utf-8")
        self.assertIn('refusing to stop unowned', source)
        self.assertIn('case "$cwd" in "$RELEASE"/*)', source)
        self.assertIn('port $4 is occupied; refusing to replace an unknown service', source)

    def test_installer_sets_only_permanent_domain_values(self):
        source = (ROOT / "install-named-runtime.sh").read_text(encoding="utf-8")
        for value in ("https://nfsnmh.com", "https://www.nfsnmh.com", "https://admin.nfsnmh.com"):
            self.assertIn(value, source)
        self.assertNotIn("trycloudflare.com", source)


if __name__ == "__main__":
    unittest.main()
