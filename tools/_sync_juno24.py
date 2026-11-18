"""One-time, auditable merge of the supplied Juno v1.3 24-game branch.

The payload is the locally-tested Juno source merged with the existing web
responsive layout, Web Crypto shuffling, and browser display-resize support.
No bundled artwork, sounds, or browser input bridge is replaced.
"""
from __future__ import annotations
import base64
import hashlib
import json
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = [ROOT / "tools" / f"_juno24_source_{i}.b64" for i in range(1, 4)]
EXPECTED_HASH = "a2380e4fbff029baab63ebb0ab136075ca0adc3708c99f1b0a0d3e67efde6b15"
EXPECTED_FILES = {
    "CHANGELOG_v1_3.md", "README.md", "game/extra_board.py",
    "game/extra_games.py", "game/layout.py", "game/more_games.py",
    "game/novel_board.py", "game/novel_games.py", "game/play.py",
    "game/quick_rules.py", "game/rules.py", "game/table.py",
    "tests/test_new_variants.py", "tests/test_special_rules.py",
    "tests/test_v130.py", "tests/test_v24_web_integration.py",
}
STEP = (
    "      - name: Sync Juno v1.3 and commit merged 24-game code\n"
    "        run: python tools/_sync_juno24.py\n"
)

def command(*args):
    subprocess.run(args, cwd=ROOT, check=True)

def replace_exact(path, before, after):
    source = path.read_text(encoding="utf-8")
    if before not in source:
        raise ValueError(f"Expected old text not found in {path}: {before!r}")
    path.write_text(source.replace(before, after), encoding="utf-8")

def main():
    encoded = "".join(p.read_text(encoding="ascii").strip() for p in PARTS)
    digest = hashlib.sha256(encoded.encode("ascii")).hexdigest()
    if digest != EXPECTED_HASH:
        raise RuntimeError(f"Source archive SHA256 mismatch: {digest}")
    changes = json.loads(zlib.decompress(base64.b64decode(encoded)).decode("utf-8"))
    if set(changes) != EXPECTED_FILES:
        raise RuntimeError(f"Unexpected files: {sorted(set(changes) ^ EXPECTED_FILES)}")
    for name, text in changes.items():
        target = ROOT / name
        assert target.parent.is_dir(), name
        target.write_text(text, encoding="utf-8", newline="\n")
        print("Updated", name, len(text), "chars", flush=True)

    # Keep web entry-point and PWA behavior intact; update product metadata.
    replace_exact(ROOT / "main.py", "Solitaire - 18 Games", "Solitaire - 24 Games")
    replace_exact(ROOT / "tools" / "prepare_web.py",
                  "Solitaire Collection — 18 Games", "Solitaire Collection — 24 Games")
    replace_exact(ROOT / "tools" / "prepare_web.py",
                  "solitaire-v1.4.2", "solitaire-v1.5.0")
    workflow = ROOT / ".github" / "workflows" / "deploy.yml"
    replace_exact(workflow, "grep -q 'solitaire-v1.4.2' build/web/sw.js",
                  "grep -q 'solitaire-v1.5.0' build/web/sw.js")
    replace_exact(workflow,
                  "          test -f game/play.py\n",
                  "          test -f game/play.py\n"
                  "          test -f game/novel_games.py\n"
                  "          test -f game/novel_board.py\n")
    replace_exact(workflow, STEP, "")
    replace_exact(workflow, "  contents: write\n", "  contents: read\n")
    from game.rules import VARIANTS, SPECIAL_VARIANTS
    if len(VARIANTS + SPECIAL_VARIANTS) != 24:
        raise RuntimeError("Merged game registry does not contain 24 variants")
    for suite in ("test_v130.py", "test_new_variants.py", "test_special_rules.py"):
        command(sys.executable, "-m", "unittest", "discover",
                "-s", "tests", "-p", suite, "-q")
    command(sys.executable, "-m", "compileall", "-q", "game", "main.py", "tools")
    for part in PARTS:
        part.unlink()
    (ROOT / "tools" / "_sync_juno24.py").unlink()
    command("git", "config", "user.name", "github-actions[bot]")
    command("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    command("git", "add", "-A")
    command("git", "commit", "-m",
            "Merge 24-game Juno v1.3 into family PWA; retain mobile fixes [skip ci]")
    command("git", "push", "origin", "HEAD:main")
    print("JUNO_24_MERGE_COMMITTED", flush=True)

if __name__ == "__main__":
    main()
