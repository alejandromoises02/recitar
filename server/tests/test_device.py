import pytest

from app.domain.device import device_of


@pytest.mark.parametrize(
    "agent, expected",
    [
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1", "ios"),
        ("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148", "ios"),
        ("Expo/1.0.0 CFNetwork/1494.0.7 Darwin/23.4.0", "ios"),  # the native app on an iPhone
        ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36", "android"),
        ("okhttp/4.12.0", "android"),  # the native app on Android
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130.0 Safari/537.36", "desktop"),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36", "desktop"),
        ("Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0", "desktop"),
        ("something-unheard-of/1.0", "unknown"),
        ("", "unknown"),
        (None, "unknown"),
    ],
)
def test_the_device_is_told_from_the_browser_without_keeping_it(agent, expected):
    assert device_of(agent) == expected
