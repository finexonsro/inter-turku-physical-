import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Inter Turku · Physical Layer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── COLORS ────────────────────────────────────────────────────────────────────
TEAL   = "#00C9B1"
TEAL2  = "#009E8C"
DARK   = "#0A0F0F"
DARK2  = "#111818"
CARD   = "#151E1E"
CARD2  = "#1C2828"
WHITE  = "#F0FAF8"
MUTED  = "#5A7A77"

LAYER_COLORS = {
    "speed": "#FFD166",
    "burst": "#FF6B6B",
    "otip":  "#00C9B1",
    "bip":   "#A78BFA",
}

LAYER_LABELS = {
    "speed": "⚡ SPEED",
    "burst": "🚀 BURST",
    "otip":  "🏃 OTIP",
    "bip":   "💥 BIP",
}

LEVEL_LABELS = {
    (85, 101): ("🔥 Elite",       "#FFD166"),
    (65,  85): ("✅ Stark",        "#00C9B1"),
    (45,  65): ("🟡 Durchschnitt","#F0FAF8"),
    (25,  45): ("🔵 Entwicklung", "#A78BFA"),
    ( 0,  25): ("⚫ Darunter",    "#5A7A77"),
}

PROFILE_LABELS = [
    ("🔥 Komplettathlet",  lambda s,b,o,p: all(x >= 65 for x in [s,b,o,p])),
    ("🧱 Wrecking Ball",   lambda s,b,o,p: o >= 85 and b >= 65),
    ("⚡ Speed Demon",     lambda s,b,o,p: s >= 85),
    ("💪 Work Horse",      lambda s,b,o,p: p >= 85 and o >= 65),
    ("🚀 Raw Athlete",     lambda s,b,o,p: b >= 85 and s >= 65),
    ("👀 Emerging",        lambda s,b,o,p: max(s,b,o,p) >= 75),
    ("—",                  lambda s,b,o,p: True),
]

POS_MAP = {
    "Central Defender": "Central Defender",
    "Full Back":        "Fullback",
    "Midfield":         "Midfielder",
    "Wide Attacker":    "Winger",
    "Center Forward":   "Striker",
}

POS_DE = {
    "Central Defender": "Innenverteidiger",
    "Fullback":         "Außenverteidiger",
    "Midfielder":       "Mittelfeld",
    "Winger":           "Flügel",
    "Striker":          "Stürmer",
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{{
    font-family:'Space Grotesk',sans-serif;
    background:{DARK};color:{WHITE};
}}
.main{{background:{DARK};}}
.block-container{{padding-top:1.5rem !important;max-width:1400px;}}
[data-testid="stSidebar"]{{background:{DARK2};border-right:1px solid #1C2828;}}
[data-testid="stSidebar"] label{{color:{MUTED} !important;font-size:11px !important;
    letter-spacing:0.12em;text-transform:uppercase;font-weight:600 !important;}}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span{{color:{WHITE} !important;}}
.stButton>button{{background:{TEAL} !important;color:{DARK} !important;
    border:none !important;border-radius:4px !important;font-weight:700 !important;
    font-family:'Space Grotesk' !important;letter-spacing:0.05em;}}
[role="tab"]{{color:{MUTED} !important;font-size:12px;font-weight:600;
    letter-spacing:0.08em;text-transform:uppercase;}}
[role="tab"][aria-selected="true"]{{color:{TEAL} !important;
    border-bottom:2px solid {TEAL} !important;}}
.stTextInput input{{background:{CARD} !important;color:{WHITE} !important;
    border:1px solid #1C2828 !important;border-radius:4px !important;}}
.stSelectbox>div>div{{background:{CARD} !important;}}

/* Cards */
.layer-card{{
    background:{CARD};border:1px solid #1C2828;border-radius:8px;
    padding:16px;margin-bottom:8px;
}}
.layer-card .score{{
    font-family:'JetBrains Mono',monospace;font-size:36px;font-weight:600;
    line-height:1;
}}
.layer-card .label{{
    font-size:10px;color:{MUTED};letter-spacing:0.15em;
    text-transform:uppercase;margin-top:4px;
}}
.layer-card .level{{
    font-size:12px;font-weight:600;margin-top:8px;
}}

/* Metric rows */
.metric-row{{
    display:flex;align-items:center;padding:6px 0;
    border-bottom:1px solid #1C2828;gap:12px;font-size:12px;
}}
.metric-name{{color:{MUTED};min-width:200px;}}
.metric-bar-bg{{background:#1C2828;border-radius:3px;height:6px;flex:1;}}
.metric-bar-fill{{height:6px;border-radius:3px;}}
.metric-val{{font-family:'JetBrains Mono',monospace;font-size:11px;
    color:{WHITE};min-width:36px;text-align:right;}}
.metric-pct{{font-family:'JetBrains Mono',monospace;font-size:11px;
    color:{MUTED};min-width:36px;text-align:right;}}

/* Profile badge */
.profile-badge{{
    display:inline-block;padding:6px 14px;border-radius:4px;
    font-size:13px;font-weight:700;letter-spacing:0.05em;
    background:rgba(0,201,177,0.15);border:1px solid {TEAL};color:{TEAL};
}}

/* Section headers */
.sec{{
    font-size:10px;color:{TEAL};letter-spacing:0.18em;
    text-transform:uppercase;font-weight:700;
    border-bottom:1px solid #1C2828;padding-bottom:6px;margin-bottom:12px;
}}
.divider{{height:1px;background:linear-gradient(90deg,{TEAL}44,#1C2828);margin:12px 0;}}
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    vk = pd.read_csv("veikkausliiga.csv", sep=';', decimal=',')
    t5 = pd.read_csv("top5.csv", sep=';', decimal=',') if __import__('os').path.exists("top5.csv") else None

    # Position mapping
    vk['position'] = vk['Position Group'].map(POS_MAP)
    vk['season']   = vk['Season'].str[:4]

    # Fix Minutes decimal
    for df in [vk] + ([t5] if t5 is not None else []):
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='ignore')
                except:
                    pass

    return vk, t5

def get_layer_metrics():
    return {
        "speed": [
            ("PSV-99",              "PSV-99",             "km/h", True),
            ("TOP 5 PSV-99",        "Top 5 PSV-99",       "km/h", True),
            ("Sprint Distance P90", "Sprint Dist P90",    "m",    True),
            ("HSR Distance P90",    "HSR Dist P90",       "m",    True),
        ],
        "burst": [
            ("Explosive Acceleration to Sprint Count", "Exp Acc → Sprint", "/90", True),
            ("Explosive Acceleration to HSR Count",   "Exp Acc → HSR",   "/90", True),
            ("TOP 3 Time to Sprint", "Time to Sprint",  "s",   False),
            ("TOP 3 Time to HSR",    "Time to HSR",     "s",   False),
        ],
        "otip": [
            ("Sprint Distance OTIP P30OTIP",                      "Sprint Dist P30OTIP",  "m",   True),
            ("HSR Distance OTIP P30OTIP",                         "HSR Dist P30OTIP",     "m",   True),
            ("HSR Count OTIP P30OTIP",                            "HSR Count P30OTIP",    "#",   True),
            ("Explosive Acceleration to Sprint Count OTIP P30OTIP","Exp Acc Sprint OTIP", "#",   True),
        ],
        "bip": [
            ("Sprint Distance P60BIP",                      "Sprint Dist P60BIP",  "m",   True),
            ("HSR Distance P60BIP",                         "HSR Dist P60BIP",     "m",   True),
            ("HSR Count P60BIP",                            "HSR Count P60BIP",    "#",   True),
            ("Explosive Acceleration to Sprint Count P60BIP","Exp Acc Sprint BIP", "#",   True),
        ],
    }

def calc_percentiles(df, benchmark_df, position, season=None):
    """Calculate percentiles for a player against benchmark population"""
    metrics = get_layer_metrics()
    results = {}

    bench = benchmark_df[benchmark_df['position'] == position].copy()
    if season:
        bench = bench[bench['season'] == season]

    for layer, cols in metrics.items():
        layer_pcts = []
        for col, name, unit, higher_better in cols:
            if col not in bench.columns or col not in df.columns:
                continue
            bench_vals = pd.to_numeric(bench[col], errors='coerce').dropna()
            player_val = pd.to_numeric(df[col], errors='coerce').iloc[0] if len(df) > 0 else np.nan
            if pd.isna(player_val) or len(bench_vals) < 5:
                continue
            if higher_better:
                pct = (bench_vals < player_val).sum() / len(bench_vals) * 100
            else:
                pct = (bench_vals > player_val).sum() / len(bench_vals) * 100
            layer_pcts.append((col, name, unit, player_val, round(pct, 1), higher_better))
        results[layer] = layer_pcts

    return results

def layer_score(layer_pcts):
    """Average percentile for a layer"""
    if not layer_pcts:
        return np.nan
    vals = [p[4] for p in layer_pcts]
    return round(np.mean(vals), 1)

def get_level(pct):
    for (lo, hi), (label, color) in LEVEL_LABELS.items():
        if lo <= pct < hi:
            return label, color
    return "—", MUTED

def get_profile(s, b, o, p):
    for label, fn in PROFILE_LABELS:
        try:
            if fn(s, b, o, p):
                return label
        except:
            continue
    return "—"

def render_layer_bar(name, val, pct, unit, color):
    return f"""<div class="metric-row">
        <div class="metric-name">{name}</div>
        <div class="metric-bar-bg">
            <div class="metric-bar-fill" style="width:{pct:.0f}%;background:{color};"></div>
        </div>
        <div class="metric-val">{val:.2f} {unit}</div>
        <div class="metric-pct">{pct:.0f}%</div>
    </div>"""

# ── LOAD ──────────────────────────────────────────────────────────────────────
try:
    vk, t5 = load_data()
except Exception as e:
    st.error(f"Fehler beim Laden: {e}")
    st.stop()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:20px 0 16px;text-align:center;">
        <div style="font-size:28px;font-weight:800;color:{TEAL};letter-spacing:-0.02em;">
            INTER TURKU
        </div>
        <div style="font-size:10px;color:{MUTED};letter-spacing:0.2em;
            text-transform:uppercase;margin-top:4px;">
            Physical Layer Framework
        </div>
    </div>
    <div class="divider"></div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="sec">Filter</div>', unsafe_allow_html=True)

    seasons = sorted(vk['season'].dropna().unique().tolist(), reverse=True)
    sel_season = st.selectbox("Saison", ["Alle"] + seasons)

    positions = sorted(vk['position'].dropna().unique().tolist())
    sel_pos = st.selectbox("Position", ["Alle"] + positions,
        format_func=lambda x: POS_DE.get(x, x) if x != "Alle" else "Alle")

    teams = sorted(vk['Team'].dropna().unique().tolist())
    sel_team = st.selectbox("Team", ["Alle"] + teams)

    min_min = st.slider("Mindestminuten", 0, 2000, 200, 50)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec">Benchmark</div>', unsafe_allow_html=True)
    bench_season = st.selectbox("Benchmark Saison", ["2025", "Alle"])

# ── FILTER ────────────────────────────────────────────────────────────────────
df_f = vk.copy()
if sel_season != "Alle":
    df_f = df_f[df_f['season'] == sel_season]
if sel_pos != "Alle":
    df_f = df_f[df_f['position'] == sel_pos]
if sel_team != "Alle":
    df_f = df_f[df_f['Team'] == sel_team]
df_f = df_f[pd.to_numeric(df_f['Minutes'], errors='coerce') >= min_min]

# Benchmark population
bench_vk = vk[vk['season'] == bench_season] if bench_season != "Alle" else vk

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:20px;margin-bottom:20px;">
    <div>
        <div style="font-size:24px;font-weight:800;color:{WHITE};letter-spacing:-0.02em;">
            Physical Layer Dashboard
        </div>
        <div style="font-size:12px;color:{MUTED};margin-top:2px;">
            Veikkausliiga · Benchmark: {bench_season} · 
            <span style="color:{TEAL};font-weight:600;">{len(df_f)} Spieler</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏟️ Team Overview",
    "👤 Spieler-Profil",
    "⚖️ Vergleich",
    "📤 Ad-hoc Upload"
])

# ── TAB 1: TEAM OVERVIEW ──────────────────────────────────────────────────────
with tab1:
    st.markdown(f'<div class="sec">Layer Scores — {sel_team if sel_team != "Alle" else "Alle Teams"}</div>',
                unsafe_allow_html=True)

    if df_f.empty:
        st.info("Keine Spieler mit diesen Filtern.")
    else:
        # Calculate scores for all filtered players
        rows = []
        metrics = get_layer_metrics()

        for _, player in df_f.iterrows():
            pos = player.get('position')
            if not pos: continue
            bench = bench_vk[bench_vk['position'] == pos]
            scores = {}
            for layer, cols in metrics.items():
                pcts = []
                for col, name, unit, higher_better in cols:
                    if col not in bench.columns: continue
                    bench_vals = pd.to_numeric(bench[col], errors='coerce').dropna()
                    val = pd.to_numeric(player.get(col, np.nan), errors='coerce')
                    if pd.isna(val) or len(bench_vals) < 3: continue
                    pct = (bench_vals < val).sum()/len(bench_vals)*100 if higher_better \
                          else (bench_vals > val).sum()/len(bench_vals)*100
                    pcts.append(pct)
                scores[layer] = round(np.mean(pcts), 1) if pcts else np.nan

            s,b,o,p = (scores.get(k, np.nan) for k in ['speed','burst','otip','bip'])
            profile = get_profile(
                s if pd.notna(s) else 0,
                b if pd.notna(b) else 0,
                o if pd.notna(o) else 0,
                p if pd.notna(p) else 0
            )
            rows.append({
                'Spieler':   player.get('Player','—'),
                'Team':      player.get('Team','—'),
                'Position':  POS_DE.get(pos, pos),
                'Saison':    player.get('season','—'),
                'Min':       int(pd.to_numeric(player.get('Minutes',0), errors='coerce') or 0),
                '⚡ Speed':  s,
                '🚀 Burst':  b,
                '🏃 OTIP':   o,
                '💥 BIP':    p,
                'Profil':    profile,
            })

        result_df = pd.DataFrame(rows)
        if not result_df.empty:
            # Style
            def color_score(val):
                if pd.isna(val): return 'color:#5A7A77'
                if val >= 85:    return 'color:#FFD166;font-weight:700'
                if val >= 65:    return 'color:#00C9B1;font-weight:600'
                if val >= 45:    return f'color:{WHITE}'
                if val >= 25:    return 'color:#A78BFA'
                return 'color:#5A7A77'

            styled = result_df.style
            for col in ['⚡ Speed','🚀 Burst','🏃 OTIP','💥 BIP']:
                if col in result_df.columns:
                    styled = styled.map(color_score, subset=[col])
            styled = styled.format({
                '⚡ Speed': '{:.0f}', '🚀 Burst': '{:.0f}',
                '🏃 OTIP':  '{:.0f}', '💥 BIP':   '{:.0f}',
            }, na_rep='—')

            event = st.dataframe(styled, use_container_width=True, height=500,
                                 on_select="rerun", selection_mode="single-row")

            # Show selected player
            if event and event.selection and event.selection.rows:
                idx = event.selection.rows[0]
                if idx < len(result_df):
                    st.session_state['selected_player'] = result_df.iloc[idx]['Spieler']
                    st.session_state['selected_season'] = str(result_df.iloc[idx]['Saison'])

# ── TAB 2: SPIELER-PROFIL ─────────────────────────────────────────────────────
with tab2:
    all_players = sorted(vk['Player'].dropna().unique().tolist())
    default_idx = 0
    if 'selected_player' in st.session_state:
        try:
            default_idx = all_players.index(st.session_state['selected_player'])
        except: pass

    col_search, col_season = st.columns([3,1])
    with col_search:
        sel_player = st.selectbox("Spieler", all_players, index=default_idx)
    with col_season:
        player_seasons = sorted(vk[vk['Player']==sel_player]['season'].unique().tolist(), reverse=True)
        sel_p_season = st.selectbox("Saison", player_seasons) if player_seasons else None

    if sel_player and sel_p_season:
        player_df = vk[(vk['Player']==sel_player) & (vk['season']==sel_p_season)]
        if player_df.empty:
            st.info("Keine Daten für diesen Spieler.")
        else:
            player_row = player_df.iloc[0]
            pos        = player_row.get('position')
            bench      = bench_vk[bench_vk['position']==pos] if pos else bench_vk

            # Calculate all layer scores
            metrics   = get_layer_metrics()
            all_pcts  = {}
            for layer, cols in metrics.items():
                layer_data = []
                for col, name, unit, higher_better in cols:
                    if col not in bench.columns: continue
                    bench_vals = pd.to_numeric(bench[col], errors='coerce').dropna()
                    val = pd.to_numeric(player_row.get(col, np.nan), errors='coerce')
                    if pd.isna(val) or len(bench_vals) < 3: continue
                    pct = (bench_vals < val).sum()/len(bench_vals)*100 if higher_better \
                          else (bench_vals > val).sum()/len(bench_vals)*100
                    layer_data.append((col, name, unit, val, round(pct,1), higher_better))
                all_pcts[layer] = layer_data

            scores = {layer: layer_score(data) for layer, data in all_pcts.items()}
            s = scores.get('speed', 0) or 0
            b = scores.get('burst', 0) or 0
            o = scores.get('otip',  0) or 0
            p = scores.get('bip',   0) or 0
            profile = get_profile(s, b, o, p)

            # Header
            mins = int(pd.to_numeric(player_row.get('Minutes', 0), errors='coerce') or 0)
            st.markdown(f"""
            <div style="background:{CARD};border:1px solid #1C2828;border-left:4px solid {TEAL};
                        border-radius:8px;padding:16px 20px;margin-bottom:20px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:22px;font-weight:800;color:{WHITE};letter-spacing:-0.02em;">
                            {sel_player}
                        </div>
                        <div style="font-size:12px;color:{MUTED};margin-top:4px;">
                            {player_row.get('Team','—')} · {player_row.get('Competition','—')} ·
                            {POS_DE.get(pos, pos or '—')} · {mins} min · {sel_p_season}
                        </div>
                    </div>
                    <div class="profile-badge">{profile}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 4 Layer Score Cards
            c1, c2, c3, c4 = st.columns(4)
            for col, layer, score in zip([c1,c2,c3,c4],
                ['speed','burst','otip','bip'], [s,b,o,p]):
                with col:
                    lbl, clr = get_level(score) if pd.notna(score) and score > 0 else ("—", MUTED)
                    color = LAYER_COLORS[layer]
                    st.markdown(f"""
                    <div class="layer-card" style="border-top:3px solid {color};">
                        <div class="label">{LAYER_LABELS[layer]}</div>
                        <div class="score" style="color:{color};">
                            {score:.0f}<span style="font-size:16px;color:{MUTED};">%</span>
                        </div>
                        <div class="level" style="color:{clr};">{lbl}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Layer Details
            lc1, lc2 = st.columns(2)
            for col_idx, (layer, label) in enumerate([
                ('speed','⚡ SPEED — Athletic Ceiling'),
                ('burst','🚀 BURST — Access to Athleticism'),
                ('otip', '🏃 OTIP — Defensive Athleticism'),
                ('bip',  '💥 BIP — Active Game Athleticism'),
            ]):
                target_col = lc1 if col_idx % 2 == 0 else lc2
                with target_col:
                    color = LAYER_COLORS[layer]
                    data  = all_pcts.get(layer, [])
                    score = scores.get(layer, 0) or 0
                    bars  = ''.join(render_layer_bar(n, v, p, u, color)
                                    for _, n, u, v, p, _ in data)
                    st.markdown(f"""
                    <div class="layer-card" style="border-top:2px solid {color};">
                        <div style="display:flex;justify-content:space-between;
                                    align-items:center;margin-bottom:10px;">
                            <div style="font-size:11px;color:{color};font-weight:700;
                                        letter-spacing:0.1em;">{label}</div>
                            <div style="font-family:'JetBrains Mono',monospace;
                                        font-size:18px;font-weight:600;color:{color};">
                                {score:.0f}%</div>
                        </div>
                        {bars}
                    </div>
                    """, unsafe_allow_html=True)

            # Radar
            if any(v > 0 for v in [s,b,o,p]):
                radar_vals = [s,b,o,p,s]
                radar_lbls = ['Speed','Burst','OTIP','BIP','Speed']
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=[50,50,50,50,50], theta=radar_lbls,
                    mode='lines', line=dict(color=MUTED, width=1, dash='dot'),
                    showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatterpolar(
                    r=radar_vals, theta=radar_lbls, fill='toself',
                    fillcolor='rgba(0,201,177,0.15)',
                    line=dict(color=TEAL, width=2.5),
                    name=sel_player,
                    hovertemplate='%{theta}: <b>%{r:.0f}%</b><extra></extra>'))
                fig.update_layout(
                    polar=dict(bgcolor=CARD,
                        radialaxis=dict(visible=True, range=[0,100],
                            tickvals=[25,50,75,100],
                            ticktext=['25%','50%','75%','100%'],
                            tickfont=dict(color=MUTED, size=9),
                            gridcolor='#1C2828', linecolor='#1C2828'),
                        angularaxis=dict(tickfont=dict(color=WHITE, size=11),
                            gridcolor='#1C2828', linecolor='#1C2828')),
                    paper_bgcolor=DARK, font=dict(color=WHITE),
                    showlegend=False, margin=dict(l=60,r=60,t=40,b=40), height=350)
                st.plotly_chart(fig, use_container_width=True)

# ── TAB 3: VERGLEICH ──────────────────────────────────────────────────────────
with tab3:
    st.markdown(f'<div class="sec">Spieler vergleichen (max. 6)</div>', unsafe_allow_html=True)

    all_players_list = vk['Player'].dropna().unique().tolist()
    sel_compare = st.multiselect("Spieler auswählen", sorted(all_players_list),
        max_selections=6, placeholder="Spieler suchen...")

    comp_season = st.selectbox("Saison für Vergleich", seasons, key="comp_season")

    if sel_compare:
        comp_data = []
        for player in sel_compare:
            p_df = vk[(vk['Player']==player) & (vk['season']==comp_season)]
            if p_df.empty:
                p_df = vk[vk['Player']==player].sort_values('season', ascending=False)
            if p_df.empty: continue
            p_row = p_df.iloc[0]
            pos   = p_row.get('position')
            bench = bench_vk[bench_vk['position']==pos] if pos else bench_vk

            layer_scores = {}
            for layer, cols in get_layer_metrics().items():
                pcts = []
                for col, name, unit, higher_better in cols:
                    if col not in bench.columns: continue
                    bench_vals = pd.to_numeric(bench[col], errors='coerce').dropna()
                    val = pd.to_numeric(p_row.get(col, np.nan), errors='coerce')
                    if pd.isna(val) or len(bench_vals) < 3: continue
                    pct = (bench_vals < val).sum()/len(bench_vals)*100 if higher_better \
                          else (bench_vals > val).sum()/len(bench_vals)*100
                    pcts.append(pct)
                layer_scores[layer] = round(np.mean(pcts),1) if pcts else np.nan
            layer_scores['player'] = player
            layer_scores['team']   = p_row.get('Team','—')
            layer_scores['pos']    = POS_DE.get(pos, pos or '—')
            comp_data.append(layer_scores)

        if comp_data:
            # Radar comparison
            colors_list = [TEAL, "#FFD166", "#FF6B6B", "#A78BFA", "#00E5FF", "#FF9F43"]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=[50,50,50,50,50],
                theta=['Speed','Burst','OTIP','BIP','Speed'],
                mode='lines', line=dict(color=MUTED, width=1, dash='dot'),
                showlegend=False, hoverinfo='skip'))

            for i, row in enumerate(comp_data):
                vals = [row.get(k,0) or 0 for k in ['speed','burst','otip','bip']]
                vals_c = vals + [vals[0]]
                fig.add_trace(go.Scatterpolar(
                    r=vals_c,
                    theta=['Speed','Burst','OTIP','BIP','Speed'],
                    fill='toself',
                    fillcolor=f'rgba({int(colors_list[i][1:3],16)},'
                               f'{int(colors_list[i][3:5],16)},'
                               f'{int(colors_list[i][5:7],16)},0.08)',
                    line=dict(color=colors_list[i], width=2),
                    name=f"{row['player']} ({row['pos']})",
                    hovertemplate='%{theta}: <b>%{r:.0f}%</b><extra></extra>'))

            fig.update_layout(
                polar=dict(bgcolor=CARD,
                    radialaxis=dict(visible=True, range=[0,100],
                        tickvals=[25,50,75,100],
                        ticktext=['25%','50%','75%','100%'],
                        tickfont=dict(color=MUTED, size=9),
                        gridcolor='#1C2828', linecolor='#1C2828'),
                    angularaxis=dict(tickfont=dict(color=WHITE, size=12),
                        gridcolor='#1C2828')),
                paper_bgcolor=DARK, font=dict(color=WHITE),
                legend=dict(bgcolor=CARD, bordercolor='#1C2828', borderwidth=1,
                    font=dict(size=11), orientation='h', y=-0.15, x=0.5, xanchor='center'),
                margin=dict(l=60,r=60,t=40,b=80), height=450)
            st.plotly_chart(fig, use_container_width=True)

            # Bar comparison
            comp_df = pd.DataFrame(comp_data)
            comp_df['name'] = comp_df.apply(
                lambda r: f"{r['player']}\n({r['pos']})", axis=1)

            fig2 = go.Figure()
            for layer, color in LAYER_COLORS.items():
                if layer in comp_df.columns:
                    fig2.add_trace(go.Bar(
                        name=LAYER_LABELS[layer],
                        x=comp_df['name'],
                        y=comp_df[layer],
                        marker_color=color,
                        marker_line_width=0))

            fig2.add_hline(y=50, line_dash='dot', line_color=MUTED,
                annotation_text='Liga-Median', annotation_font_color=MUTED)
            fig2.update_layout(
                barmode='group', paper_bgcolor=DARK, plot_bgcolor=CARD,
                font=dict(color=WHITE, family='Space Grotesk'),
                xaxis=dict(gridcolor='#1C2828', tickfont=dict(size=10)),
                yaxis=dict(gridcolor='#1C2828', range=[0,100],
                    title='Veikkausliiga Perzentil'),
                legend=dict(bgcolor=CARD, bordercolor='#1C2828'),
                margin=dict(l=40,r=20,t=20,b=40), height=350)
            st.plotly_chart(fig2, use_container_width=True)

# ── TAB 4: AD-HOC UPLOAD ──────────────────────────────────────────────────────
with tab4:
    st.markdown(f'<div class="sec">Ad-hoc Spieler analysieren</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:12px;color:{MUTED};margin-bottom:16px;">SkillCorner CSV hochladen — Spieler wird sofort gegen Veikkausliiga Benchmark eingeordnet.</div>',
                unsafe_allow_html=True)

    uploaded = st.file_uploader("SkillCorner CSV hochladen", type=['csv'])
    if uploaded:
        try:
            adhoc = pd.read_csv(uploaded, sep=';', decimal=',')
            adhoc['position'] = adhoc['Position Group'].map(POS_MAP)

            st.success(f"✅ {len(adhoc)} Spieler geladen")
            sel_adhoc = st.selectbox("Spieler auswählen", adhoc['Player'].tolist())

            if sel_adhoc:
                a_row = adhoc[adhoc['Player']==sel_adhoc].iloc[0]
                pos   = a_row.get('position')
                bench = bench_vk[bench_vk['position']==pos] if pos else bench_vk

                all_pcts = {}
                for layer, cols in get_layer_metrics().items():
                    layer_data = []
                    for col, name, unit, higher_better in cols:
                        if col not in bench.columns: continue
                        bench_vals = pd.to_numeric(bench[col], errors='coerce').dropna()
                        val = pd.to_numeric(a_row.get(col, np.nan), errors='coerce')
                        if pd.isna(val) or len(bench_vals) < 3: continue
                        pct = (bench_vals < val).sum()/len(bench_vals)*100 if higher_better \
                              else (bench_vals > val).sum()/len(bench_vals)*100
                        layer_data.append((col, name, unit, val, round(pct,1), higher_better))
                    all_pcts[layer] = layer_data

                scores  = {l: layer_score(d) for l, d in all_pcts.items()}
                s,b,o,p = (scores.get(k,0) or 0 for k in ['speed','burst','otip','bip'])
                profile = get_profile(s,b,o,p)

                st.markdown(f"""
                <div style="background:{CARD};border:1px solid #1C2828;border-left:4px solid {TEAL};
                            border-radius:8px;padding:16px;margin:16px 0;">
                    <div style="font-size:18px;font-weight:700;">{sel_adhoc}</div>
                    <div style="font-size:12px;color:{MUTED};">{a_row.get('Team','—')} ·
                    {a_row.get('Competition','—')} · {POS_DE.get(pos,pos or '—')}</div>
                    <div style="margin-top:10px;"><span class="profile-badge">{profile}</span></div>
                </div>
                """, unsafe_allow_html=True)

                c1,c2,c3,c4 = st.columns(4)
                for col, layer, score in zip([c1,c2,c3,c4],
                    ['speed','burst','otip','bip'],[s,b,o,p]):
                    with col:
                        lbl, clr = get_level(score)
                        color    = LAYER_COLORS[layer]
                        st.markdown(f"""
                        <div class="layer-card" style="border-top:3px solid {color};">
                            <div class="label">{LAYER_LABELS[layer]}</div>
                            <div class="score" style="color:{color};">{score:.0f}%</div>
                            <div class="level" style="color:{clr};">{lbl}</div>
                        </div>
                        """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Fehler: {e}")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:{MUTED};font-size:10px;
            letter-spacing:0.15em;text-transform:uppercase;margin-top:40px;
            border-top:1px solid #1C2828;padding-top:16px;">
    Inter Turku · Physical Layer Framework · {datetime.now().strftime('%Y')}
</div>
""", unsafe_allow_html=True)
