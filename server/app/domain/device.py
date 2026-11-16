from typing import Literal

Device = Literal["ios", "android", "desktop", "unknown"]

_ANDROID = ("android", "okhttp", "dalvik")
_IOS = ("iphone", "ipad", "ipod", "cfnetwork", "darwin")  # the last two are how the native app talks on an iPhone
_DESKTOP = ("windows", "macintosh", "x11", "linux", "cros")


def device_of(user_agent: str | None) -> Device:
    """A coarse class of the device behind a request, for the analytics only. The browser's own text is never
    kept or sent anywhere: just this label."""
    agent = (user_agent or "").lower()
    if any(marker in agent for marker in _ANDROID):
        return "android"
    if any(marker in agent for marker in _IOS):
        return "ios"
    if any(marker in agent for marker in _DESKTOP):
        return "desktop"
    return "unknown"
