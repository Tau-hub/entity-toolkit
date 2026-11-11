"""Copies ``wiki/*.md`` to the project's GitHub wiki: ``python packaging/publish_wiki.py``.

The wiki is its own git repository. GitHub only creates it once a first page has been saved by hand on the website
(the Wiki tab of the repository, "Create the first page", Save): do that once, then this script replaces every page.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTE = "git@github.com:Tau-hub/entity-toolkit.wiki.git"


def git(*args, cwd):
    subprocess.check_call(["git", *args], cwd=str(cwd))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "wiki"
        try:
            git("clone", "--quiet", REMOTE, str(clone), cwd=tmp)
        except subprocess.CalledProcessError:
            print("The wiki does not exist yet: open the repository's Wiki tab, save a first page, then run this again.")
            return 1
        for old in clone.glob("*.md"):
            old.unlink()
        for page in sorted((ROOT / "wiki").glob("*.md")):
            if page.name != "README.md":  # the note for people editing wiki/ in the repository
                shutil.copy(page, clone / page.name)
        git("add", "-A", cwd=clone)
        if subprocess.call(["git", "diff", "--cached", "--quiet"], cwd=str(clone)) == 0:
            print("The wiki is already up to date.")
            return 0
        git("commit", "--quiet", "-m", "Update from the repository's wiki/ folder", cwd=clone)
        git("push", "--quiet", cwd=clone)
        print("Wiki updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
