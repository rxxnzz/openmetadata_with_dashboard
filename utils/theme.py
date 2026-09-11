import streamlit as st

COLORS = {
    "bg": "#F7F8FA",
    "surface": "#FFFFFF",
    "border": "#E5E8EC",
    "text": "#12181F",
    "text_soft": "#667085",
    "accent": "#0E7C7B",      
    "accent_soft": "#E6F4F3",
    "warn": "#B8720C",
    "warn_soft": "#FCF1DC",
    "danger": "#B23B24",
    "danger_soft": "#FAE7E2",
    "success": "#1B7A4F",
    "success_soft": "#E3F3EA",
}

PLOTLY_PALETTE = ["#0E7C7B", "#B8720C", "#3E6E8E", "#8A5FA8", "#B23B24", "#4C8C6B"]


def apply_theme():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: {COLORS['text']};
        }}
        h1, h2, h3, h4, .kpi-value, .ring-value {{
            font-family: 'Manrope', sans-serif;
        }}

        .stApp {{ background-color: {COLORS['bg']}; }}

        section[data-testid="stSidebar"] {{
            background-color: #0F1720;
        }}
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] .stMarkdown {{
            color: #E7EAEE !important;
        }}
        /* Teks di DALAM input/select tetap gelap -- kotaknya berlatar putih,
           jadi kalau ikut dipaksa terang jadi tidak kelihatan (putih di atas putih). */
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea,
        section[data-testid="stSidebar"] [data-baseweb="select"] * {{
            color: {COLORS['text']} !important;
        }}

        /* Bordered containers (st.container(border=True)) styled as cards */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']} !important;
            border-radius: 14px !important;
            padding: 4px 6px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }}

        .stButton > button {{
            background-color: {COLORS['accent']};
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            padding: 0.5rem 1.1rem;
        }}
        .stButton > button:hover {{
            background-color: #0B6362;
            color: white;
        }}

        .eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 12px;
            font-weight: 600;
            color: {COLORS['accent']};
            margin-bottom: 2px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 12px;
            margin-top: 4px;
        }}

        /* KPI card */
        .kpi-card {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }}
        .kpi-label {{
            font-size: 13px;
            color: {COLORS['text_soft']};
            font-weight: 500;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 30px;
            font-weight: 800;
            line-height: 1.1;
        }}
        .kpi-badge {{
            display: inline-block;
            margin-top: 8px;
            font-size: 12px;
            font-weight: 600;
            padding: 2px 10px;
            border-radius: 999px;
        }}

        /* Trust ring */
        .ring-wrap {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .ring-value {{
            font-size: 26px;
            font-weight: 800;
        }}
        .ring-caption {{
            font-size: 11px;
            color: {COLORS['text_soft']};
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge_html(text: str, kind: str = "neutral") -> str:
    bg = {
        "success": COLORS["success_soft"],
        "warn": COLORS["warn_soft"],
        "danger": COLORS["danger_soft"],
        "neutral": COLORS["accent_soft"],
    }[kind]
    fg = {
        "success": COLORS["success"],
        "warn": COLORS["warn"],
        "danger": COLORS["danger"],
        "neutral": COLORS["accent"],
    }[kind]
    return f'<span class="kpi-badge" style="background:{bg};color:{fg};">{text}</span>'


def kpi_card(label: str, value: str, badge_text: str | None = None, badge_kind: str = "neutral"):
    badge = badge_html(badge_text, badge_kind) if badge_text else ""

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {badge}
        </div>
        """,
        unsafe_allow_html=True,
    )


def trust_ring(score: float, label: str = "Trust Score"):
    score = max(0, min(100, score))
    degrees = score * 3.6
    color = COLORS["accent"] if score >= 70 else (COLORS["warn"] if score >= 40 else COLORS["danger"])

    st.markdown(
        f"""
        <div class="ring-wrap">
            <div style="
                width:120px;height:120px;border-radius:50%;
                background: conic-gradient({color} {degrees}deg, {COLORS['border']} 0deg);
                display:flex;align-items:center;justify-content:center;
                flex-shrink: 0;">
                <div style="
                    width:94px;height:94px;border-radius:50%;background:{COLORS['surface']};
                    display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <span class="ring-value">{score:.0f}%</span>
                </div>
            </div>
            <div>
                <div class="ring-caption">{label}</div>
                <div style="font-size:14px;color:{COLORS['text_soft']};max-width:260px;margin-top:4px;">
                    Gabungan metadata completeness, ownership coverage, dan domain assignment.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(eyebrow: str, title: str):
    st.markdown(
        f"""
        <div class="eyebrow">{eyebrow}</div>
        <div class="section-title">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def style_plotly(fig):
    fig.update_layout(
        font_family="Inter",
        colorway=PLOTLY_PALETTE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#EDEFF2")
    return fig
