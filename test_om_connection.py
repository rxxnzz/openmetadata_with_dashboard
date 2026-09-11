"""
Jalankan skrip ini untuk memastikan koneksi ke OpenMetadata benar,
terlepas dari Streamlit/caching/dsb.

Usage:
    python test_om_connection.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

OM_HOST_URL = os.getenv("OM_HOST_URL", "")
OM_JWT_TOKEN = os.getenv("OM_JWT_TOKEN", "")

print("=" * 60)
print("DIAGNOSTIC: Koneksi ke OpenMetadata")
print("=" * 60)
print(f"OM_HOST_URL  = {OM_HOST_URL!r}")
print(f"OM_JWT_TOKEN = {'(terisi, ' + str(len(OM_JWT_TOKEN)) + ' karakter)' if OM_JWT_TOKEN else '(KOSONG!)'}")
print()

if not OM_HOST_URL:
    print("❌ OM_HOST_URL kosong. Cek file .env ada di folder ini dan terisi.")
    raise SystemExit(1)

if not OM_JWT_TOKEN:
    print("❌ OM_JWT_TOKEN kosong. Cek file .env.")
    raise SystemExit(1)

url = f"{OM_HOST_URL}/v1/tables"
headers = {"Authorization": f"Bearer {OM_JWT_TOKEN}"}

print(f"Mencoba GET {url} ...")
try:
    resp = requests.get(url, headers=headers, params={"limit": 1}, timeout=15)
except requests.exceptions.ConnectionError as e:
    print("❌ CONNECTION ERROR — server OpenMetadata tidak bisa dihubungi sama sekali.")
    print(f"   Detail: {e}")
    raise SystemExit(1)
except requests.exceptions.Timeout:
    print("❌ TIMEOUT — server tidak merespons dalam 15 detik.")
    raise SystemExit(1)

print(f"Status code: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    total = len(data.get("data", []))
    print(f"✅ SUKSES. Contoh response: {total} table(s) diterima.")
    if total > 0:
        print(f"   Contoh nama: {data['data'][0].get('fullyQualifiedName')}")
elif resp.status_code == 401:
    print("❌ 401 UNAUTHORIZED — token salah/expired/format salah.")
    print(f"   Response body: {resp.text[:500]}")
elif resp.status_code == 403:
    print("❌ 403 FORBIDDEN — token valid tapi bot tidak punya izin akses.")
    print(f"   Response body: {resp.text[:500]}")
elif resp.status_code == 404:
    print("❌ 404 NOT FOUND — kemungkinan OM_HOST_URL salah path (harus diakhiri /api).")
    print(f"   Response body: {resp.text[:500]}")
else:
    print(f"❌ Status tidak terduga: {resp.status_code}")
    print(f"   Response body: {resp.text[:500]}")
