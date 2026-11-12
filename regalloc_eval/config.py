import os

from .paths import ROOT


def load_env():
    """Read KEY=VALUE lines from .env into os.environ (real environment variables win)."""
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))
