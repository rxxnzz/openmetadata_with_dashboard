import streamlit as st
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

from utils import om_client, pg_client, metrics, theme

st.set_page_config(page_title="Governance Dashboard", page_icon="📊", layout="wide")
theme.apply_theme()
@st.cache_data(ttl=300, show_spinner="Menarik metadata dari OpenMetadata...")
def load_entities():
    return om_client.get_all_data_assets()


col_title, col_btn = st.columns([4, 1])
with col_title:
    theme.section_header("Data Governance", "Catalog Analytics Overview")
    st.caption("📡 Live dari OpenMetadata API (di-cache 5 menit di memori, bukan disimpan ke database)")
with col_btn:
    st.write("")
    if st.button("🔄 Refresh sekarang", use_container_width=True):
        load_entities.clear()
        st.rerun()

entities, om_errors = load_entities()

if om_errors:
    with st.expander("⚠️ Sebagian data gagal diambil dari OpenMetadata", expanded=True):
        for err in om_errors:
            st.code(err)
        st.caption("Jalankan `python test_om_connection.py` dari terminal untuk diagnosis lebih detail.")

if not entities:
    st.error("Tidak ada data yang berhasil diambil dari OpenMetadata. Lihat detail error di atas.")
    st.stop()

all_services = sorted({(e.get("fullyQualifiedName", "").split(".")[0] or "unknown") for e in entities})
with st.container(border=True):
    selected_services = st.multiselect(
        "🗄️ Filter Database Service",
        options=all_services,
        default=all_services,
        help="Pilih satu atau beberapa database service. Kosongkan pilihan default untuk melihat semua.",
    )
if selected_services:
    entities = [e for e in entities if e.get("fullyQualifiedName", "").split(".")[0] in selected_services]

st.caption(f"Menganalisis {len(entities)} data asset" + (f" dari {len(selected_services)} service" if selected_services != all_services else ""))

completeness_df = metrics.compute_completeness_score(entities)
owner_df = metrics.compute_owner_distribution(entities)
no_owner_df = metrics.compute_no_owner(entities)
domain_df = metrics.compute_domain_distribution(entities)
service_df = metrics.compute_service_distribution(entities)
class_df = metrics.compute_classification_population(entities)
growth_df = metrics.compute_growth_by_month(entities)

total_datasets = len(completeness_df) if not completeness_df.empty else 0
avg_completeness = completeness_df["score"].mean() if not completeness_df.empty else 0
alert_count = int(completeness_df["needs_alert"].sum()) if not completeness_df.empty else 0
no_owner_count = len(no_owner_df) if not no_owner_df.empty else 0

ownership_coverage = (1 - (no_owner_count / total_datasets)) * 100 if total_datasets else 0
no_domain_count = (
    int(domain_df[domain_df["domain"] == "No Domain"]["dataset_count"].sum())
    if not domain_df.empty and "No Domain" in domain_df["domain"].values
    else 0
)
domain_coverage = (1 - (no_domain_count / total_datasets)) * 100 if total_datasets else 0
trust_score = (avg_completeness + ownership_coverage + domain_coverage) / 3 if total_datasets else 0

st.write("")

col_ring, col_kpi1, col_kpi2, col_kpi3 = st.columns([1.3, 1, 1, 1])
with col_ring:
    with st.container(border=True):
        theme.trust_ring(trust_score)
with col_kpi1:
    theme.kpi_card("Total Dataset", f"{total_datasets:,}")
with col_kpi2:
    badge = "Perlu perhatian" if alert_count > 0 else "Semua lengkap"
    kind = "warn" if alert_count > 0 else "success"
    theme.kpi_card("Metadata Belum Lengkap", f"{alert_count}", badge, kind)
with col_kpi3:
    badge = "Perlu owner" if no_owner_count > 0 else "Semua ada owner"
    kind = "danger" if no_owner_count > 0 else "success"
    theme.kpi_card("Dataset Tanpa Owner", f"{no_owner_count}", badge, kind)

st.write("")


with st.container(border=True):
    theme.section_header("01 · Coverage", "Metadata Completeness Score")
    c1, c2 = st.columns(2)
    c1.metric("Rata-rata completeness score", f"{avg_completeness:.1f}%")
    c2.metric("Dataset butuh perhatian", alert_count)
    if alert_count > 0:
        st.warning(
            f"⚠️ {alert_count} dataset belum lengkap field wajibnya (deskripsi/owner/tags/domain). "
            "User berisiko tidak bisa trust terhadap data ini."
        )
    if not completeness_df.empty:
        with st.expander("Lihat dataset yang perlu dilengkapi"):
            st.dataframe(
                completeness_df[completeness_df["needs_alert"]].sort_values("score"),
                use_container_width=True,
            )

st.write("")

with st.container(border=True):
    theme.section_header("02 · Coverage", "Dataset Growth per Bulan")
    if not growth_df.empty:
        fig = theme.style_plotly(px.bar(growth_df, x="month", y="count"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data timestamp yang bisa dipakai untuk growth chart.")

st.write("")

col_a, col_b = st.columns(2)
with col_a:
    with st.container(border=True):
        theme.section_header("03 · Adoption", "Most Used Tags (Search)")
        try:
            tag_rows = pg_client.get_most_used_search_tags()
            if tag_rows:
                fig = theme.style_plotly(px.bar(tag_rows, x="tag", y="cnt", labels={"cnt": "jumlah pencarian"}))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada log pencarian dengan tag filter.")
        except Exception as e:
            st.error(f"Gagal ambil data dari analytics DB: {e}")

with col_b:
    with st.container(border=True):
        theme.section_header("04 · Adoption", "Top Search Keywords")
        try:
            kw_rows = pg_client.get_top_search_keywords()
            if kw_rows:
                fig = theme.style_plotly(px.bar(kw_rows, x="keyword", y="cnt", labels={"cnt": "jumlah pencarian"}))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada log pencarian.")
        except Exception as e:
            st.error(f"Gagal ambil data dari analytics DB: {e}")

st.write("")

col_c, col_d = st.columns(2)
with col_c:
    with st.container(border=True):
        theme.section_header("05 · Adoption", "Most Viewed Dataset")
        try:
            view_rows = pg_client.get_most_viewed()
            st.dataframe(view_rows, use_container_width=True)
        except Exception as e:
            st.error(f"Gagal ambil data views: {e}")

with col_d:
    with st.container(border=True):
        theme.section_header("06 · Adoption", "Most Favorite / Bookmarked")
        try:
            fav_rows = pg_client.get_most_favorited()
            st.dataframe(fav_rows, use_container_width=True)
        except Exception as e:
            st.error(f"Gagal ambil data favorites: {e}")

st.write("")

with st.container(border=True):
    theme.section_header("07 · Adoption", "Popular Data Source")
    if not service_df.empty:
        fig = theme.style_plotly(px.pie(service_df, names="service", values="dataset_count", hole=0.55))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data.")

st.write("")

col_e, col_f = st.columns(2)
with col_e:
    with st.container(border=True):
        theme.section_header("08 · Trust", "Populasi Klasifikasi")
        if not class_df.empty:
            fig = theme.style_plotly(px.bar(class_df, x="classification", y="dataset_count"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada dataset yang diberi tag classification.")

with col_f:
    with st.container(border=True):
        theme.section_header("09 · Trust", "Domain & Category")
        if not domain_df.empty:
            fig = theme.style_plotly(px.bar(domain_df, x="domain", y="dataset_count"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data.")

st.write("")

col_g, col_h = st.columns(2)
with col_g:
    with st.container(border=True):
        theme.section_header("10 · Trust", "Owner dengan Dataset Terbanyak")
        st.dataframe(owner_df.head(10), use_container_width=True)

with col_h:
    with st.container(border=True):
        theme.section_header("11 · Trust", "Dataset Tanpa Owner")
        st.metric("Jumlah dataset tanpa owner", no_owner_count)
        with st.expander("Lihat daftar"):
            st.dataframe(no_owner_df, use_container_width=True)
