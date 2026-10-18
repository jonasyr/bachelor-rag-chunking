"""MDX pages of the e2e documentation (Mintlify) to Markdown (ADR 0038).

nav_areas reads the navigation (docs.json).
"""


def nav_areas(nav: dict) -> dict[str, str]:
    """Page (path without suffix) -> area, in navigation order: the page's group, or the tab for
    pages listed directly under a tab."""
    areas: dict[str, str] = {}
    for tab in nav["navigation"]["tabs"]:
        entries = [(group["group"], group["pages"]) for group in tab.get("groups", [])]
        if "pages" in tab:
            entries.append((tab["tab"], tab["pages"]))
        for area, pages in entries:
            for page in pages:
                if not isinstance(page, str):
                    raise ValueError(f"nested navigation entry in {area!r}: {page!r}")
                if page in areas:
                    raise ValueError(f"page {page!r} listed twice in the navigation")
                areas[page] = area
    return areas
