#!/usr/bin/env python3
"""
Node-free UI self-test runner for Hatlier.

Serves the repo over a local HTTP port, opens hatlier.html in a headless
browser (Edge, then Chrome), runs window.__hatlierSelfTest() and reports.
Exit code is non-zero if any check fails, so it works in CI or a git hook.

Requires: selenium (`pip install selenium`) and Edge or Chrome installed.
Selenium 4 auto-manages the matching driver.

    python tests/selftest.py
"""
import functools
import http.server
import json
import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def serve(port: int) -> http.server.HTTPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = http.server.HTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def make_edge():
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--no-sandbox")
    return webdriver.Edge(options=o)


def make_chrome():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--no-sandbox")
    return webdriver.Chrome(options=o)


def run(url: str):
    last_err = None
    for maker, name in ((make_edge, "edge"), (make_chrome, "chrome")):
        try:
            d = maker()
        except Exception as e:  # driver/browser missing
            last_err = e
            print(f"[{name}] unavailable: {e}", file=sys.stderr)
            continue
        try:
            d.get(url)
            time.sleep(1.2)
            return name, d.execute_script("return window.__hatlierSelfTest();")
        finally:
            d.quit()
    raise SystemExit(f"No usable browser (Edge/Chrome). Last error: {last_err}")


def main():
    port = free_port()
    httpd = serve(port)
    try:
        browser, res = run(f"http://127.0.0.1:{port}/hatlier.html")
    finally:
        httpd.shutdown()

    total, failed = res["total"], res["failed"]
    print(f"[{browser}] Hatlier selftest: {total - failed}/{total} passed")
    for r in res["results"]:
        if not r["pass"]:
            detail = f" ({r['detail']})" if r.get("detail") else ""
            print(f"  FAIL  {r['name']}{detail}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
