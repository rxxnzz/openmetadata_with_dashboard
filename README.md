# Data Governance & Catalog Analytics Dashboard

Streamlit app dengan 2 halaman, tampilan bergaya SaaS (KPI cards, trust
score ring, card-based sections):
- **Discovery** — search/browse dataset dari OpenMetadata, plus tampilan
  metadata lengkap (owner, tags, domain, follower count) per dataset yang
  ditarik langsung dari OpenMetadata.
- **Governance Dashboard** — 11 metrik tata kelola data.


## 1. Generate Bot Token di OpenMetadata

1. Login OpenMetadata UI (admin) -> Settings -> Bots -> Add Bot.
2. Buka bot tsb -> tab Token -> Generate Token.
3. Pastikan bot punya role read-only yang mencakup semua asset yang mau dianalisis.
4. Isi ke `.env` (`OM_HOST_URL`, `OM_JWT_TOKEN`).

## 2. Setup Postgres analytics DB (untuk log search/view/favorite saja)

```bash
createdb governance_analytics
```
Isi `PG_*` di `.env`, lalu:
```bash
python -c "from utils.pg_client import init_schema; init_schema('sql/schema.sql')"
```

## 3. Install & jalankan

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run Home.py
```

## Troubleshooting cepat

- `RuntimeError: PG_PASSWORD kosong` -> cek file `.env`
  `.env` (bukan `.env.txt`), ada di root folder, tanpa kutip/spasi aneh.
- `Invalid field name owner`/`domain` -> versi OpenMetadata
- `python test_om_connection.py` -> jalankan untuk diagnosis koneksi
  OpenMetadata secara terpisah dari Streamlit.

## Struktur

```
Home.py
pages/1_Discovery.py          -> search + metadata lengkap per dataset
pages/2_Governance_Dashboard.py -> 11 metrik, dihitung live
test_om_connection.py         -> skrip diagnostic koneksi
utils/om_client.py            -> REST wrapper OpenMetadata
utils/pg_client.py            -> baca/tulis Postgres (search/view/favorite log saja)
utils/metrics.py              -> logic perhitungan metrik
utils/theme.py                -> design system (CSS, KPI card, trust ring)
sql/schema.sql                -> DDL search_log, dataset_view_log, dataset_favorite
.streamlit/config.toml        -> tema warna native Streamlit
```

## Mapping 11 metrik -> sumber data

| Metrik | Sumber |
|---|---|
| 1. Metadata completeness + alert | OpenMetadata API, live |
| 2. Dataset growth per bulan | OpenMetadata API, live |
| 3. Most used tags (search) | Postgres search_log.tags_filter  |
| 4. Top search keywords | Postgres search_log.keyword  |
| 5. Most viewed dataset | Postgres dataset_view_log  |
| 6. Most favorite/bookmarked | Postgres dataset_favorite  |
| 7. Popular data source | OpenMetadata API, live |
| 8. Populasi classification | OpenMetadata API, live |
| 9. Domain & category | OpenMetadata API, live |
| 10. Owner terbanyak | OpenMetadata API, live |
| 11. Dataset tanpa owner | OpenMetadata API, live |
