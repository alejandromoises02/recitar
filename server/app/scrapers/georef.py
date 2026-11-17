"""Georef, the Argentine government's geography API (apis.datos.gob.ar), for sources that give a
venue's coordinates or city but no province. Any failure answers None: the caller falls back."""

import httpx

GEOREF = "https://apis.datos.gob.ar/georef/api"


def _get(client: httpx.Client, path: str, params: dict) -> dict | None:
    try:
        response = client.get(f"{GEOREF}/{path}", params=params)
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    return data if response.status_code == 200 and isinstance(data, dict) else None


def province_at(client: httpx.Client, point: tuple[float, float]) -> str | None:
    """The province Georef places these coordinates in; None when it cannot say."""
    data = _get(client, "ubicacion", {"lat": point[0], "lon": point[1]}) or {}
    name = ((data.get("ubicacion") or {}).get("provincia") or {}).get("nombre")
    return name if isinstance(name, str) else None


def province_named(client: httpx.Client, city: str) -> str | None:
    """The province of every Argentine locality called `city`; None when there are several, or none."""
    data = _get(client, "localidades", {"nombre": city, "campos": "provincia.nombre", "max": 100}) or {}
    localities = data.get("localidades")
    names = {((l.get("provincia") or {}).get("nombre")) for l in localities if isinstance(l, dict)} if isinstance(localities, list) else set()
    return names.pop() if len(names) == 1 and None not in names else None
