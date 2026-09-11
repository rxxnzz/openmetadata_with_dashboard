import streamlit as st
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from utils import om_client, pg_client, theme, metrics
from utils.text_utils import clean_html

st.set_page_config(page_title="Discovery", page_icon="🔍", layout="wide")
theme.apply_theme()
theme.section_header("Catalog", "Dataset Discovery")


@st.cache_data(ttl=300, show_spinner="Menarik daftar dataset dari OpenMetadata...")
def load_all_datasets():
    return om_client.get_all_data_assets()


all_entities, browse_errors = load_all_datasets()
all_services = sorted({(e.get("fullyQualifiedName", "").split(".")[0] or "unknown") for e in all_entities})

user_id = st.sidebar.text_input("User ID (sementara, ganti dengan auth asli)", value="demo-user")

with st.sidebar:
    st.subheader("Filter")

    selected_services = st.multiselect(
        "🗄️ Database Service",
        options=all_services,
        default=all_services,
        help="Pilih satu atau beberapa database service (mis. Postgres A, Postgres B).",
    )

    try:
        classifications = om_client.get_classification_list()
        class_names = [c["name"] for c in classifications]
    except Exception as e:
        class_names = []
        st.warning(f"Gagal ambil classification dari OpenMetadata: {e}")

    selected_classification = st.selectbox("Classification", ["(none)"] + class_names)
    tag_options = []
    if selected_classification != "(none)":
        try:
            tags = om_client.get_tags_for_classification(selected_classification)
            tag_options = [t["fullyQualifiedName"] for t in tags]
        except Exception as e:
            st.warning(f"Gagal ambil tags: {e}")

    selected_tags = st.multiselect("Tags", tag_options)


def in_selected_services(fqn: str) -> bool:
    if not selected_services:
        return True
    return fqn.split(".")[0] in selected_services


def render_dataset_card(fqn: str, name: str, description: str, entity_type: str):

    detail = None
    fetch_error = None
    score_info = None
    fresh_info = None
    versions = []
    try:
        detail = om_client.get_entity_by_fqn(entity_type, fqn)
        score_info = metrics.score_single_entity(detail)
        fresh_info = metrics.compute_freshness(detail)
        entity_id = detail.get("id")
        if entity_id:
            versions = om_client.get_entity_versions(entity_type, entity_id)
    except Exception as e:
        fetch_error = str(e)

    with st.container(border=True):
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            st.markdown(f"**{name}**  \n`{fqn}`  \n{clean_html(description) or '_no description_'}")

        with col2:
            is_fav = False
            try:
                is_fav = pg_client.is_favorited(user_id, fqn)
            except Exception:
                pass
            label = "★ Unfavorite" if is_fav else "☆ Favorite"
            if st.button(label, key=f"fav_{fqn}"):
                try:
                    now_fav = pg_client.toggle_favorite(user_id, fqn, name, entity_type)
                    st.toast("Ditambahkan ke favorit" if now_fav else "Dihapus dari favorit")
                    st.rerun()
                except Exception as e:
                    st.warning(f"Gagal update favorite: {e}")

        with col3:
            if detail is not None:
                export_data = dict(detail)
                export_data["_freshness"] = {
                    "last_updated_readable": (
                        fresh_info["last_updated"].strftime("%Y-%m-%d %H:%M:%S")
                        if fresh_info and fresh_info["last_updated"] else None
                    ),
                    "days_since_update": fresh_info["days_since_update"] if fresh_info else None,
                    "status": fresh_info["status"] if fresh_info else None,
                }
                export_data["_trust_score"] = score_info
                export_data["_version_history"] = [
                    {
                        "version": v.get("version"),
                        "updated_at_readable": (
                            datetime.fromtimestamp(v["updatedAt"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                            if v.get("updatedAt") else None
                        ),
                        "updated_by": v.get("updatedBy"),
                        "changed_fields": [
                            f.get("name", "?")
                            for f in (v.get("changeDescription", {}).get("fieldsAdded") or [])
                            + (v.get("changeDescription", {}).get("fieldsUpdated") or [])
                            + (v.get("changeDescription", {}).get("fieldsDeleted") or [])
                        ],
                    }
                    for v in versions
                ]

                json_str = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
                st.download_button(
                    "⬇️ JSON",
                    data=json_str,
                    file_name=f"{name}.json",
                    mime="application/json",
                    key=f"dl_{fqn}",
                )
            else:
                st.button("⬇️ JSON", key=f"dl_{fqn}", disabled=True, help=f"Gagal ambil metadata: {fetch_error}")

        with st.expander("📋 Lihat metadata lengkap dari OpenMetadata"):
            if detail is None:
                st.warning(f"Gagal ambil metadata lengkap: {fetch_error}")
            else:
                owners = detail.get("owners") or []
                tags_list = detail.get("tags") or []
                domains = detail.get("domains") or []
                followers = detail.get("followers") or []

                col_score, col_fresh = st.columns([1, 1.4])
                with col_score:
                    theme.trust_ring(score_info["score"], label="Trust Score")
                    checklist = ""
                    for field, ok in score_info["breakdown"].items():
                        icon = "✅" if ok else "❌"
                        checklist += f"{icon} {metrics.FIELD_LABELS.get(field, field)}  \n"
                    st.markdown(checklist)

                with col_fresh:
                    st.markdown("**🕒 Freshness**")
                    if fresh_info["last_updated"]:
                        status = fresh_info["status"]
                        kind = "success" if status == "Fresh" else ("warn" if status == "Mulai usang" else "danger")
                        st.markdown(
                            f"Terakhir diperbarui: **{fresh_info['last_updated'].strftime('%d %b %Y, %H:%M')}**  \n"
                            f"({fresh_info['days_since_update']} hari yang lalu)",
                            unsafe_allow_html=True,
                        )
                        st.markdown(theme.badge_html(status, kind), unsafe_allow_html=True)
                        st.caption(
                            "Catatan: ini kapan METADATA terakhir diubah (deskripsi/owner/tag), "
                            "bukan kapan data di tabel sumbernya di-refresh."
                        )
                    else:
                        st.info("Tidak ada informasi kapan metadata terakhir diperbarui.")
                st.markdown("**📜 Riwayat perubahan metadata**")
                if versions:
                    history_rows = []
                    for v in versions[:10]:
                        ts = v.get("updatedAt")
                        when = "-"
                        if ts:
                            try:
                                when = datetime.fromtimestamp(ts / 1000).strftime("%d %b %Y, %H:%M")
                            except (TypeError, ValueError, OSError):
                                when = "-"
                        change = v.get("changeDescription") or {}
                        changed_fields = [
                            f.get("name", "?")
                            for f in (change.get("fieldsAdded") or [])
                            + (change.get("fieldsUpdated") or [])
                            + (change.get("fieldsDeleted") or [])
                        ]
                        history_rows.append(
                            {
                                "Versi": v.get("version"),
                                "Tanggal": when,
                                "Diubah oleh": v.get("updatedBy") or "-",
                                "Field yang berubah": ", ".join(changed_fields) or "-",
                            }
                        )
                    st.dataframe(history_rows, use_container_width=True, hide_index=True)
                else:
                    st.caption("Belum ada riwayat perubahan tercatat untuk dataset ini.")

                st.divider()

                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(f"**Deskripsi**  \n{clean_html(detail.get('description')) or '_belum ada deskripsi_'}")
                    st.markdown(
                        "**Owner**  \n"
                        + (", ".join(o.get("displayName") or o.get("name", "?") for o in owners) or "_belum ada owner_")
                    )
                    st.markdown(
                        "**Domain**  \n"
                        + (", ".join(d.get("displayName") or d.get("name", "?") for d in domains) or "_belum ada domain_")
                    )
                with m2:
                    st.markdown(
                        "**Tags**  \n"
                        + (", ".join(t.get("tagFQN", "?") for t in tags_list) or "_belum ada tag_")
                    )
                    st.markdown(f"**Tipe entity**  \n{entity_type}")
                    st.markdown(f"**Jumlah follower (di OpenMetadata)**  \n{len(followers)}")

                columns = detail.get("columns")
                if columns:
                    st.markdown("**Metadata kolom**")
                    col_rows = [
                        {
                            "Kolom": col.get("name"),
                            "Tipe data": col.get("dataType"),
                            "Deskripsi": clean_html(col.get("description")) or "_belum ada deskripsi_",
                            "Tags": ", ".join(t.get("tagFQN", "?") for t in (col.get("tags") or [])) or "-",
                        }
                        for col in columns
                    ]
                    st.dataframe(col_rows, use_container_width=True, hide_index=True)


with st.container(border=True):
    query = st.text_input("🔍 Cari dataset (nama, deskripsi, kolom, dll.)", value="")
    search_clicked = st.button("Search", type="primary")

if search_clicked or query:
    try:
        results = om_client.search_entities(query=query, tags=selected_tags)
        hits = results.get("hits", {}).get("hits", [])
        hits = [h for h in hits if in_selected_services(h.get("_source", {}).get("fullyQualifiedName", ""))]
    except Exception as e:
        hits = []
        st.error(f"Search gagal: {e}")

    try:
        pg_client.log_search(
            user_id=user_id,
            keyword=query or "(empty)",
            tags_filter=selected_tags,
            result_count=len(hits),
        )
    except Exception as e:
        st.warning(f"Search dijalankan tapi gagal dicatat ke analytics DB: {e}")

    st.caption(f"{len(hits)} hasil ditemukan")
    st.write("")

    for hit in hits:
        src = hit.get("_source", {})
        render_dataset_card(
            fqn=src.get("fullyQualifiedName", ""),
            name=src.get("name", src.get("fullyQualifiedName", "")),
            description=src.get("description", "-"),
            entity_type=src.get("entityType", "table"),
        )

else:
    st.write("")
    theme.section_header("Browse", "Semua Dataset di Catalog")

    if browse_errors:
        with st.expander("⚠️ Sebagian gagal diambil"):
            for err in browse_errors:
                st.code(err)

    filtered_entities = [e for e in all_entities if in_selected_services(e.get("fullyQualifiedName", ""))]

    if not filtered_entities:
        st.info("Belum ada dataset yang bisa ditampilkan untuk filter ini.")
    else:
        st.caption(f"{len(filtered_entities)} dataset tersedia -- klik untuk lihat detail")
        for e in filtered_entities:
            render_dataset_card(
                fqn=e.get("fullyQualifiedName", ""),
                name=e.get("name", e.get("fullyQualifiedName", "")),
                description=e.get("description", "-"),
                entity_type=e.get("_entityType", "table"),
            )
