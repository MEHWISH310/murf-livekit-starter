from schemes_data import SCHEMES


def find_schemes(query: str) -> list[dict]:
    """Search local scheme dataset by keyword match against name, category, or description.

    Returns a list of matching schemes (can be empty).
    """
    query_lower = query.lower().strip()
    matches = []

    for scheme in SCHEMES:
        searchable = " ".join(
            [scheme["name"], scheme["full_name"], scheme["category"], scheme["description"]]
        ).lower()
        if query_lower in searchable:
            matches.append(scheme)

    return matches


def list_all_schemes() -> list[dict]:
    return SCHEMES