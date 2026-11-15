"""Map raw Location text to the closest existing Notion locality dropdown option.

Standing rule (owner decision, 15 Nov 2026): raw Location text must be normalized
to the closest locality option instead of failing the listing. Text similarity is
tried first; Ola Maps geocoding resolves names that do not textually match any
option (for example a layout or society name that sits inside a listed locality).
"""
from __future__ import annotations

from dataclasses import dataclass
import difflib


@dataclass(frozen=True)
class LocalityNormalization:
    canonical: str = ""
    source: str = ""  # exact | similarity | ola_maps
    note: str = ""


def _similar(candidate: str, options: list[str], cutoff: float) -> tuple[str, str]:
    """Return (option, how) for a textual match, or ('', '') when none holds."""
    text = (candidate or "").strip()
    if not text:
        return "", ""
    folded = {option.casefold(): option for option in options}
    exact = folded.get(text.casefold())
    if exact:
        return exact, "exact"
    needle = text.casefold()
    for option in options:
        hay = option.casefold()
        if len(needle) >= 4 and len(hay) >= 4 and (needle in hay or hay in needle):
            return option, "similarity"
    close = difflib.get_close_matches(text, options, n=1, cutoff=cutoff)
    if close:
        return close[0], "similarity"
    return "", ""


def normalize_locality(
    locality: str,
    options: list[str],
    *,
    ola_client=None,
    context: tuple = (),
    city: str = "Bengaluru",
    cutoff: float = 0.75,
) -> LocalityNormalization:
    """Resolve raw location text to the closest dropdown option.

    Never invents a locality: only an existing option is ever returned, and an
    empty result means the caller must route the listing to Needs Review.
    """
    text = (locality or "").strip()
    opts = [str(option).strip() for option in options if str(option or "").strip()]
    if not text or not opts:
        return LocalityNormalization()
    hit, how = _similar(text, opts, cutoff)
    if hit:
        note = "" if hit == text else f"Location '{text}' matched locality option '{hit}'."
        return LocalityNormalization(hit, how, note)
    if ola_client is not None:
        queries = [f"{text}, {city}"]
        for extra in context:
            extra_text = str(extra or "").strip()
            if extra_text and extra_text.casefold() != text.casefold():
                queries.append(f"{extra_text}, {text}, {city}")
        for query in queries[:2]:
            try:
                result = ola_client.geocode(query)
            except Exception:
                continue
            if getattr(result, "confidence", "") != "OK":
                continue
            for candidate in getattr(result, "candidates", ()):
                hit, _ = _similar(str(candidate), opts, cutoff)
                if hit:
                    return LocalityNormalization(
                        hit,
                        "ola_maps",
                        f"Location '{text}' was not in the locality list; Ola Maps placed it at "
                        f"'{getattr(result, 'formatted_address', '')}', so it was mapped to the closest option '{hit}'.",
                    )
    return LocalityNormalization()
