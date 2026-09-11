import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils import theme

st.set_page_config(page_title="Data Governance Portal", page_icon="🗂️", layout="wide")
theme.apply_theme()

theme.section_header("Welcome", "Data Governance Portal")
st.write("")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("### 🔍 Discovery")
        st.markdown(
            "Cari dan telusuri dataset di catalog. Setiap pencarian, tampilan "
            "detail dataset, dan bookmark dicatat otomatis untuk keperluan "
            "analytics — karena OpenMetadata tidak mencatat perilaku pencarian "
            "dari portal eksternal secara native."
        )
with col2:
    with st.container(border=True):
        st.markdown("### 📊 Governance Dashboard")
        st.markdown(
            "Metrik tata kelola data: metadata completeness, ownership, "
            "klasifikasi sensitivitas, domain, dan insight penggunaan dari "
            "halaman Discovery — semua dalam satu tampilan."
        )

st.write("")
with st.expander("⚙️ Setup checklist (jalankan sekali di awal)"):
    st.markdown(
        """
1. Copy `.env.example` menjadi `.env`, isi `OM_HOST_URL` dan `OM_JWT_TOKEN`
   (lihat komentar di `utils/om_client.py` untuk cara generate bot token),
   serta kredensial `PG_*` untuk database analytics baru Anda.
2. Buat database baru di Postgres: `createdb governance_analytics`
3. Inisialisasi schema (sekali saja):
   ```
   python -c "from utils.pg_client import init_schema; init_schema('sql/schema.sql')"
   ```
4. Jalankan sync pertama kali: `python sync_metrics.py`
5. Jalankan: `streamlit run Home.py`
        """
    )
