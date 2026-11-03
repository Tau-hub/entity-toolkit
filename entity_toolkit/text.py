"""Text helpers shared by the recognition modules."""
import re
import unicodedata


def norm(s):
    """Lower-case, accent-free, letters and digits only: the form used to compare names."""
    s = unicodedata.normalize("NFD", s.lower().replace("&", "and"))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))
