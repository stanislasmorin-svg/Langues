"""Tell Bing (and other IndexNow engines) about the newest lessons.

Run by the GitHub workflow after the site has been rebuilt and published.
It never fails the workflow: any error is only printed.
"""
import json
import os
import urllib.request

BASE = "https://masimera.com/"
KEY = "96fcd6d0bb466ca95c3279efa503f076"   # same as the file /<KEY>.txt at the root of the site
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = [("lessons.json", "grec/"), ("lessons_it.json", "it/")]


def latest_date(path):
    try:
        lessons = json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
        return max(l["date"] for l in lessons if l.get("date"))
    except Exception:
        return None


def main():
    urls = [BASE]
    for path, out in LANGS:
        d = latest_date(path)
        if d:
            urls += [f"{BASE}{out}cours/{d}.html", f"{BASE}{out}", f"{BASE}{out}mots.html"]
    body = json.dumps({"host": "masimera.com", "key": KEY,
                       "keyLocation": f"{BASE}{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow:", r.status, "-", len(urls), "URLs")
    except urllib.error.HTTPError as e:
        print("IndexNow: HTTP", e.code, e.read()[:300])
    except Exception as e:
        print("IndexNow: error", e)
    for u in urls:
        print("  ", u)


if __name__ == "__main__":
    main()
