"""Apple App Site Association and Android Asset Links for deep linking"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/.well-known/apple-app-site-association")
def apple_app_site_association():
    """
    Defining Associated Domain for Universal Links on iOS.

    https://developer.apple.com/documentation/safariservices/supporting_associated_domains
    """
    return {
        "applinks": {
            "details": [
                {
                    "appIDs": [
                        "JR2KLJR86L.co.juli.mobile.ios",
                        "JR2KLJR86L.co.juli.mobile.ios.staging",
                    ],
                    "components": [
                        {"/": "/links/*"},
                    ],
                },
                {
                    "appIDs": [
                        "JR2KLJR86L.co.juli.mobile.ios.noven",
                        "JR2KLJR86L.co.juli.mobile.ios.noven.staging",
                    ],
                    "components": [
                        {"/": "/noven-links/*"},
                    ],
                },
                {
                    "appIDs": [
                        "JR2KLJR86L.co.juli.mobile.ios.flutter.staging",
                    ],
                    "components": [
                        {"/": "/app/*"},
                    ],
                },
            ]
        },
        "webcredentials": {
            "apps": [],
        },
        "appclips": {
            "apps": [],
        },
    }


@router.get("/.well-known/assetlinks.json")
def android_asset_links():
    """
    Defining Associated Domain for App Links on Android.

    https://developer.android.com/training/app-links/verify-site-associations
    """
    return [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "co.juli.mobile.android",
                "sha256_cert_fingerprints": [
                    "DC:59:4E:72:DA:F3:55:4D:55:80:06:9F:90:58:FE:35:AC:53:D6:6E:07:B1:A1:17:03:D4:4E:32:DA:CE:C0:60",
                    "D8:B9:78:62:98:E5:A8:FD:09:FE:7B:71:61:30:B4:7A:F4:A1:E0:F4:E6:9C:25:19:CB:94:C3:62:4E:63:0E:57",
                ],
            },
        },
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "co.juli.mobile.android.develop",
                "sha256_cert_fingerprints": [
                    "DC:59:4E:72:DA:F3:55:4D:55:80:06:9F:90:58:FE:35:AC:53:D6:6E:07:B1:A1:17:03:D4:4E:32:DA:CE:C0:60"
                ],
            },
        },
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "co.mypatch.mobile.android.develop",
                "sha256_cert_fingerprints": [
                    "19:82:49:31:B4:D2:36:38:12:CF:81:FF:2B:A5:1E:14:E5:F1:20:E0:1D:29:7E:BA:36:90:23:D2:D6:B6:8A:93"
                ],
            },
        },
    ]
