#!/usr/bin/env python3
"""Purge the Cloudflare edge cache for this site.

Only needed when the zone is proxied (orange cloud) and a Cache Rule is
caching HTML at the edge: otherwise a new deploy stays invisible until
the edge TTL expires.

Env vars:
  CLOUDFLARE_API_TOKEN   required; token needs  Zone -> Cache Purge -> Purge
  CLOUDFLARE_ZONE_ID     optional; looked up from CLOUDFLARE_ZONE_NAME if absent
  CLOUDFLARE_ZONE_NAME   optional; defaults to aiqivy.com

Exit code 0 on success (or when no token is configured), 1 on failure.
Standard library only, so any Python 3 works.
"""

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"


def call(method, path, token, body=None):
    req = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def main():
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        print("CLOUDFLARE_API_TOKEN not set, skipping cache purge")
        return 0

    zid = os.environ.get("CLOUDFLARE_ZONE_ID")
    if not zid:
        name = os.environ.get("CLOUDFLARE_ZONE_NAME", "aiqivy.com")
        r = call("GET", "/zones?name=" + name, token)
        if not r.get("success") or not r.get("result"):
            print("zone %s not found: %s" % (name, r.get("errors")))
            return 1
        zid = r["result"][0]["id"]

    r = call("POST", "/zones/%s/purge_cache" % zid, token, {"purge_everything": True})
    if r.get("success"):
        print("Cloudflare cache purged")
        return 0
    print("purge failed: %s" % (r.get("errors"),))
    return 1


if __name__ == "__main__":
    sys.exit(main())
