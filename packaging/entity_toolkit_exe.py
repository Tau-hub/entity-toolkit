"""Entry point of the packaged EntityToolkit.exe (PyInstaller needs a script, not ``python -m entity_toolkit``)."""
import sys

from entity_toolkit.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
