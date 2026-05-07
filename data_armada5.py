import streamlit as st
import sqlite3, uuid, io, random, string
from datetime import datetime
import pandas as pd

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DB_FILE = "lpg_internal.db"
ADMIN_PASSWORD = "pertamina2025"


# ─── DB ───────────────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def gen_password(n=8):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=n))


def init_db():
    with get_conn() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS agen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sold_to TEXT UNIQUE,
            nama TEXT,
            password TEXT
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS kendaraan_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT UNIQUE
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS tipe_agen_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT UNIQUE
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS armada (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agen_id INTEGER,
            region TEXT, sales_area TEXT, tipe_agen TEXT, kendaraan TEXT,
            kapasitas INTEGER, jumlah_kendaraan INTEGER, utilisasi INTEGER, load_factor INTEGER,
            created_at TEXT
        )""")
        if con.execute("SELECT COUNT(*) FROM kendaraan_master").fetchone()[0] == 0:
            for k in ["SKID TANK", "TANKI", "TRUK", "TRUK COLT DIESEL"]:
                con.execute(
                    "INSERT OR IGNORE INTO kendaraan_master(nama) VALUES(?)", (k,)
                )
        if con.execute("SELECT COUNT(*) FROM tipe_agen_master").fetchone()[0] == 0:
            for t in ["HAP", "INDUSTRI", "MUSICOOL", "NPSO", "PSO"]:
                con.execute(
                    "INSERT OR IGNORE INTO tipe_agen_master(nama) VALUES(?)", (t,)
                )
        con.commit()


# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Pendataan Armada LPG", layout="wide", page_icon="⛽")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
*, *::before, *::after { font-family: 'Plus Jakarta Sans', sans-serif !important; box-sizing: border-box; }
header, #MainMenu, footer { visibility: hidden; }

.stApp { background: #f0f4fb; min-height: 100vh; }

/* ── HERO ── */
.hero {
    background: linear-gradient(120deg, #002e6e 0%, #004b9e 60%, #0060c8 100%);
    border-radius: 18px; padding: 2.2rem 3rem 2rem;
    margin-bottom: 2rem; position: relative; overflow: hidden;
    box-shadow: 0 12px 35px rgba(0,46,110,.28);
}
.hero::after {
    content: '⛽'; position: absolute; right: 2.5rem; top: 50%;
    transform: translateY(-50%); font-size: 6rem; opacity: 0.10; pointer-events: none;
}
.hero-bar { width: 50px; height: 4px; background: #ed1c24; border-radius: 3px; margin-bottom: .9rem; }
.hero h1  { color:#fff !important; font-size:2rem !important; font-weight:900 !important; margin:0 0 .35rem !important; letter-spacing:-.5px; }
.hero p   { color:rgba(255,255,255,.75) !important; font-size:1rem !important; margin:0 !important; }

/* ── CARD ── */
.card {
    background: #ffffff; border-radius: 14px; padding: 1.8rem 2rem;
    margin-bottom: 1.4rem; box-shadow: 0 2px 16px rgba(0,46,110,.07);
    border: 1px solid #dde6f5;
}
.card-hdr {
    font-size: 1rem; font-weight: 800; color: #002e6e; letter-spacing: .2px;
    margin-bottom: 1.1rem; padding-bottom: .7rem; border-bottom: 2px solid #e8eef8;
}

/* ── ELEGANT DIVIDER ── */
.el-divider { border: none; border-top: 1px solid #e4eaf5; margin: 1.2rem 0; }

/* ── LABELS ── */
div[data-testid="stTextInput"]   label,
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"]   label {
    font-size: .93rem !important; font-weight: 700 !important;
    color: #1a3260 !important; margin-bottom: 5px !important;
}

/* ── TEXT INPUT ── */
div[data-testid="stTextInput"] input {
    background: #fff !important; color: #0c1a30 !important;
    border: 2px solid #c4d4ef !important; border-radius: 10px !important;
    font-size: 1.02rem !important; font-weight: 500 !important;
    height: 50px !important; padding: 0 14px !important;
    transition: border .18s, box-shadow .18s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #004b9e !important; box-shadow: 0 0 0 3px rgba(0,75,158,.13) !important; outline: none !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #aab8d0 !important; font-style: italic; }

/* ── NUMBER INPUT ── */
div[data-testid="stNumberInput"] input {
    background: #fff !important; color: #0c1a30 !important;
    border: 2px solid #c4d4ef !important; border-radius: 10px !important;
    font-size: 1.05rem !important; font-weight: 600 !important; height: 50px !important;
}
div[data-testid="stNumberInput"] input:focus {
    border-color: #004b9e !important; box-shadow: 0 0 0 3px rgba(0,75,158,.13) !important;
}

/* ── SELECTBOX ── */
div[data-testid="stSelectbox"] > div > div {
    background: #fff !important; color: #0c1a30 !important;
    border: 2px solid #c4d4ef !important; border-radius: 10px !important;
    font-size: 1.02rem !important; font-weight: 500 !important; min-height: 50px !important;
}
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #004b9e !important; box-shadow: 0 0 0 3px rgba(0,75,158,.13) !important;
}
div[data-testid="stSelectbox"] span { color: #0c1a30 !important; font-size: 1.02rem !important; }

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #002e6e, #004b9e) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    font-size: .97rem !important; font-weight: 700 !important; height: 50px !important;
    box-shadow: 0 3px 10px rgba(0,46,110,.25) !important; transition: all .18s !important;
    white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #003f96, #0060c8) !important;
    box-shadow: 0 5px 16px rgba(0,46,110,.35) !important; transform: translateY(-1px);
}

/* ── FORM SUBMIT (red) ── */
div[data-testid="stForm"] .stButton > button {
    background: linear-gradient(135deg, #c0141b, #ed1c24) !important;
    box-shadow: 0 3px 14px rgba(237,28,36,.30) !important;
    height: 58px !important; font-size: 1.05rem !important; width: 100%; letter-spacing: .4px;
}
div[data-testid="stForm"] .stButton > button:hover {
    background: linear-gradient(135deg, #d41920, #f52d35) !important;
    box-shadow: 0 5px 18px rgba(237,28,36,.40) !important;
}

/* ── AGEN ROW ── */
.agen-row {
    background: #f6f9ff; border: 1.5px solid #d5e3f7;
    border-radius: 11px; padding: 14px 18px; margin: 8px 0;
}
.agen-name { font-size: 1.08rem; font-weight: 800; color: #002e6e; }
.agen-sub  { font-size: .85rem; color: #5b78a8; font-weight: 500; margin-top: 3px; }

/* ── SUCCESS / PASSWORD BOX ── */
.success-box {
    background: linear-gradient(135deg, #ecfdf5, #d1fae5);
    border: 2px solid #6ee7b7; border-radius: 16px;
    padding: 2rem; text-align: center; margin-bottom: 1.4rem;
}
.success-box h2 { color: #065f46 !important; font-size: 1.5rem !important; margin: .5rem 0 0 !important; }
.pwd-box {
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border: 2px solid #fcd34d; border-radius: 14px;
    padding: 1.5rem 2rem; margin: 1rem 0; text-align: center;
}
.pwd-code {
    font-size: 2.2rem; font-weight: 900; letter-spacing: 6px; color: #92400e;
    background: #fef9ee; border-radius: 8px; padding: .3rem 1.2rem;
    display: inline-block; margin-top: .6rem; border: 1.5px dashed #f59e0b;
}

/* ── INFO STRIP ── */
.info-strip {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 1.5px solid #93c5fd; border-radius: 12px;
    padding: .9rem 1.4rem; margin-bottom: 1.4rem;
    display: flex; align-items: center; gap: 1rem;
}
.info-strip .is-name { font-size: 1.08rem; font-weight: 800; color: #1e3a8a; }
.info-strip .is-sub  { font-size: .85rem; color: #3b82f6; font-weight: 600; }

/* ── BADGE ── */
.badge     { display:inline-block; background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; border-radius:20px; padding:3px 12px; font-size:.8rem; font-weight:700; }
.badge-red { background:#fff1f2; color:#be123c; border-color:#fecdd3; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#002060 0%,#003a7a 100%) !important;
}
section[data-testid="stSidebar"] *, section[data-testid="stSidebar"] label { color:#fff !important; }
section[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,.12) !important; border: 1.5px solid rgba(255,255,255,.3) !important;
    color: #fff !important; border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,.15) !important; border: 1px solid rgba(255,255,255,.3) !important;
    color: #fff !important; box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,.26) !important; }

/* ── TABS ── */
.stTabs [data-baseweb="tab"] { border-radius: 8px !important; font-weight: 600 !important; color: #475569 !important; }
.stTabs [aria-selected="true"] { background: #eff6ff !important; color: #002e6e !important; }

/* ── METRIC ── */
div[data-testid="stMetric"] { background:#f6f9ff; border-radius:10px; padding:.7rem 1rem; border:1px solid #dde6f5; }
div[data-testid="stMetricLabel"] { font-weight:700 !important; color:#475569 !important; }
div[data-testid="stMetricValue"] { color:#002e6e !important; font-weight:800 !important; }

/* ── ALERTS ── */
div[data-testid="stAlert"] { border-radius: 10px !important; font-weight: 500 !important; }

/* ── RESET PWD BOX ── */
.resetpwd-box {
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border: 2px solid #fcd34d; border-radius: 12px;
    padding: 1.2rem 1.5rem; margin: .5rem 0 1rem;
}
.resetpwd-box .rpwd-label { font-size:.8rem; font-weight:700; color:#92400e; text-transform:uppercase; letter-spacing:1px; }
.resetpwd-box .rpwd-code  { font-size:1.6rem; font-weight:900; letter-spacing:5px; color:#92400e; margin-top:.3rem; }

/* ── FIX OVERLAPPING: Login row layout ── */
.login-row-container { margin-bottom: 1.2rem; }
.stTextInput { margin-bottom: 0 !important; }

/* ── FIX: Column alignment in login rows ── */
div[data-testid="column"] { overflow: visible !important; }

/* ── Admin access denied box ── */
.access-denied {
    background: linear-gradient(135deg, #fff1f2, #fecdd3);
    border: 2px solid #f87171; border-radius: 14px;
    padding: 2rem; text-align: center; margin: 2rem 0;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
init_db()

# ─── SESSION STATE ────────────────────────────────────────────────────────────
for k, v in [
    ("step", "login"),
    ("last_id", None),
    ("admin_mode", False),
    ("edit_id", None),
    ("selected_agen", None),
    ("logged_in_agen", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── SIDEBAR ADMIN ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔐 Panel Admin")
    st.markdown(
        "<hr style='border:1px solid rgba(255,255,255,.2);margin:.5rem 0 1rem'>",
        unsafe_allow_html=True,
    )
    if not st.session_state.admin_mode:
        pwd = st.text_input(
            "Password Admin", type="password", placeholder="Masukkan password..."
        )
        if st.button("🔓 Masuk Admin", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_mode = True
                st.rerun()
            else:
                st.error("❌ Password salah!")
    else:
        st.success("✅ Mode Admin Aktif")
        st.markdown(
            "<hr style='border:1px solid rgba(255,255,255,.2);margin:.6rem 0'>",
            unsafe_allow_html=True,
        )
        if st.button("📊 Dashboard Admin", use_container_width=True):
            st.session_state.step = "admin_view"
            st.rerun()
        if st.button("🏠 Menu Input User", use_container_width=True):
            st.session_state.step = "login"
            st.rerun()
        st.markdown(
            "<hr style='border:1px solid rgba(255,255,255,.2);margin:.6rem 0'>",
            unsafe_allow_html=True,
        )
        if st.button("🚪 Logout Admin", use_container_width=True):
            st.session_state.admin_mode = False
            st.session_state.step = "login"
            st.rerun()

# ─── HERO ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <div class="hero-bar"></div>
  <h1>⛽ Sistem Pendataan Armada LPG</h1>
  <p>Pastikan data yang diinput sudah sesuai dengan kondisi fisik kendaraan di lapangan</p>
</div>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# STEP: LOGIN
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "login":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-hdr">🔍 Masuk ke Sistem — Cari Agen Anda</div>',
        unsafe_allow_html=True,
    )

    q = st.text_input(
        "Nomor Sold To Party atau Nama Agen",
        placeholder="Contoh: 73001234  atau  PT DELI JAYA",
        key="login_q",
    )

    if q:
        with get_conn() as con:
            rows = con.execute(
                "SELECT id, sold_to, nama, password FROM agen WHERE sold_to LIKE ? OR nama LIKE ? LIMIT 6",
                (f"%{q}%", f"%{q}%"),
            ).fetchall()

        if rows:
            st.markdown(
                f'<p style="color:#5b78a8;font-weight:600;font-size:.9rem;margin:.6rem 0 .4rem">Ditemukan {len(rows)} agen:</p>',
                unsafe_allow_html=True,
            )
            for aid, sto, nama, db_pwd in rows:
                # Cek apakah agen ini sudah punya password (dari generate)
                pwd_ready = (
                    bool(db_pwd)  # sudah ada password di DB
                    or st.session_state.get(f"show_pwd_{aid}")
                    or st.session_state.get(f"pwd_generated_{aid}")
                )

                st.markdown(
                    f"""
                <div class="agen-row">
                    <div class="agen-name">{nama}</div>
                    <div class="agen-sub">📋 Sold To: <b>{sto}</b></div>
                </div>""",
                    unsafe_allow_html=True,
                )

                if not pwd_ready:
                    # ── STEP 1: Tampilkan tombol Generate Password dulu ──
                    st.markdown(
                        '<p style="color:#92400e;font-size:.85rem;font-weight:600;margin:.5rem 0 .3rem;">'
                        "🔑 Generate password untuk login ke sistem ini:"
                        "</p>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        f"🔄 Generate Password untuk {nama}",
                        key=f"gen_{aid}",
                        use_container_width=False,
                    ):
                        new_pwd = gen_password()
                        with get_conn() as con:
                            con.execute(
                                "UPDATE agen SET password=? WHERE id=?", (new_pwd, aid)
                            )
                            con.commit()
                        st.session_state[f"show_pwd_{aid}"] = new_pwd
                        st.rerun()
                else:
                    # ── STEP 2: Password sudah di-generate, tampilkan password dan form login ──
                    npwd_show = st.session_state.get(f"show_pwd_{aid}", "")
                    if npwd_show:
                        st.markdown(
                            f"""
                        <div class="resetpwd-box">
                            <div class="rpwd-label">🔑 Password untuk <b>{nama}</b> — Catat sebelum login!</div>
                            <div class="rpwd-code">{npwd_show}</div>
                            <div style="font-size:.78rem;color:#b45309;margin-top:.5rem;">
                                ⚠️ Salin password ini sekarang, lalu gunakan untuk login di bawah.
                            </div>
                        </div>""",
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        '<p style="color:#1a3260;font-size:.9rem;font-weight:700;margin:.6rem 0 .2rem;">Masukkan password untuk login:</p>',
                        unsafe_allow_html=True,
                    )
                    col_p, col_b = st.columns([5, 1])
                    with col_p:
                        pwd_in = st.text_input(
                            "Password",
                            type="password",
                            placeholder="Masukkan password...",
                            key=f"pwd_{aid}",
                            label_visibility="collapsed",
                        )
                    with col_b:
                        login_btn = st.button(
                            "Masuk →", key=f"login_{aid}", use_container_width=True
                        )

                    if login_btn:
                        # Reload password terbaru dari DB
                        with get_conn() as con:
                            latest_pwd = con.execute(
                                "SELECT password FROM agen WHERE id=?", (aid,)
                            ).fetchone()[0]
                        if pwd_in == latest_pwd:
                            st.session_state.logged_in_agen = {
                                "id": aid,
                                "nama": nama,
                                "sto": sto,
                            }
                            st.session_state.selected_agen = {
                                "id": aid,
                                "nama": nama,
                                "sto": sto,
                            }
                            # Bersihkan session password display
                            for k in [f"show_pwd_{aid}", f"pwd_generated_{aid}"]:
                                if k in st.session_state:
                                    del st.session_state[k]
                            st.session_state.step = "input"
                            st.rerun()
                        else:
                            st.error(f"❌ Password salah untuk agen {nama}.")

                st.markdown('<hr class="el-divider">', unsafe_allow_html=True)

        else:
            st.warning("⚠️ Agen tidak ditemukan dalam database.")
            st.markdown('<hr class="el-divider">', unsafe_allow_html=True)
            if st.button(
                "➕ Tambah Sold To Party & Nama Agen Baru", use_container_width=False
            ):
                st.session_state.step = "register_agen"
                st.rerun()
    else:
        st.markdown(
            """
        <div style="text-align:center;padding:2rem 0;color:#b0bdd4;">
            <div style="font-size:3rem">🔎</div>
            <div style="font-size:1rem;font-weight:500;margin-top:.5rem">
                Ketik Sold To Party atau nama agen untuk memulai
            </div>
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP: REGISTER AGEN BARU
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "register_agen":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-hdr">➕ Pendaftaran Sold To Party & Agen Baru</div>',
        unsafe_allow_html=True,
    )

    with st.form("form_register"):
        sold_to_new = st.text_input(
            "Nomor Sold To Party *", placeholder="Contoh: 7300XXXX"
        )
        nama_new = st.text_input(
            "Nama Agen / Perusahaan *", placeholder="Contoh: PT DELI JAYA ABADI"
        )
        submitted = st.form_submit_button(
            "🔐 Daftarkan & Generate Password", use_container_width=True
        )

        if submitted:
            if not sold_to_new.strip() or not nama_new.strip():
                st.error("❌ Nomor Sold To dan Nama Agen wajib diisi.")
            else:
                with get_conn() as con:
                    exist = con.execute(
                        "SELECT id FROM agen WHERE sold_to=?", (sold_to_new.strip(),)
                    ).fetchone()
                if exist:
                    st.error("❌ Sold To Party ini sudah terdaftar.")
                else:
                    new_pwd = gen_password()
                    with get_conn() as con:
                        cur = con.execute(
                            "INSERT INTO agen(sold_to, nama, password) VALUES(?,?,?)",
                            (
                                sold_to_new.strip().upper(),
                                nama_new.strip().upper(),
                                new_pwd,
                            ),
                        )
                        new_id = cur.lastrowid
                        con.commit()
                    st.session_state.logged_in_agen = {
                        "id": new_id,
                        "nama": nama_new.strip().upper(),
                        "sto": sold_to_new.strip().upper(),
                    }
                    st.session_state.selected_agen = st.session_state.logged_in_agen
                    st.session_state["new_pwd_display"] = new_pwd
                    st.session_state.step = "show_password"
                    st.rerun()

    st.markdown('<hr class="el-divider">', unsafe_allow_html=True)
    if st.button("← Kembali ke Pencarian", use_container_width=False):
        st.session_state.step = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP: TAMPIL PASSWORD BARU
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "show_password":
    agen = st.session_state.logged_in_agen
    npwd = st.session_state.get("new_pwd_display", "")

    st.markdown(
        f"""
    <div class="success-box">
        <div style="font-size:3rem">🎉</div>
        <h2>Pendaftaran Berhasil!</h2>
        <p style="color:#065f46;font-size:.95rem;margin-top:.4rem">
            Agen <b>{agen['nama']}</b> &nbsp;({agen['sto']})&nbsp; berhasil didaftarkan.
        </p>
    </div>
    <div class="pwd-box">
        <div style="font-size:.88rem;font-weight:700;color:#92400e;text-transform:uppercase;letter-spacing:1px;">
            🔑 Password Login Agen Anda
        </div>
        <div class="pwd-code">{npwd}</div>
        <div style="margin-top:.8rem;font-size:.82rem;color:#b45309;">
            ⚠️ Catat dan simpan password ini sekarang. Password hanya ditampilkan satu kali dan tidak dapat dilihat kembali.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#002e6e;font-weight:600;">Password sudah dicatat? Lanjutkan untuk mengisi data armada.</p>',
        unsafe_allow_html=True,
    )
    if st.button("✅ Lanjutkan Input Data Armada →", use_container_width=True):
        st.session_state.step = "input"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP: INPUT FORM ARMADA
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "input":
    target_id = st.session_state.edit_id
    is_edit = target_id is not None
    agen = st.session_state.selected_agen or st.session_state.logged_in_agen

    defaults = {
        "reg": "Sumbagut",
        "sa": "Medan",
        "tipe": "PSO",
        "kend": "TRUK",
        "jml": 1,
        "kap": 1,
        "util": 0,
        "lf": 100,
    }

    if is_edit:
        with get_conn() as con:
            d = con.execute(
                "SELECT region,sales_area,tipe_agen,kendaraan,kapasitas,jumlah_kendaraan,utilisasi,load_factor FROM armada WHERE id=?",
                (target_id,),
            ).fetchone()
            if d:
                defaults = {
                    "reg": d[0],
                    "sa": d[1],
                    "tipe": d[2],
                    "kend": d[3],
                    "kap": d[4],
                    "jml": d[5],
                    "util": d[6],
                    "lf": d[7],
                }

    st.markdown(
        f"""
    <div class="info-strip">
        <div style="font-size:2rem">🏢</div>
        <div>
            <div class="is-name">{agen['nama']}</div>
            <div class="is-sub">Sold To: {agen['sto']}</div>
        </div>
        <div style="margin-left:auto">
            <span class="badge {'badge-red' if is_edit else ''}">
                {'✏️ MODE EDIT' if is_edit else '➕ INPUT BARU'}
            </span>
        </div>
    </div>""",
        unsafe_allow_html=True,
    )
    if st.button("📋 Lihat Semua Data Saya", use_container_width=False):
        st.session_state.step = "my_data"
        st.rerun()
    with st.form("form_utama"):
        st.markdown(
            '<div class="card"><div class="card-hdr">📍 Informasi Wilayah</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            reg_opts = [
                "Sumbagut",
                "Sumbagsel",
                "JBB",
                "JBT",
                "Jatimbalinus",
                "Kalimantan",
                "Sulawesi",
            ]
            reg = st.selectbox(
                "Wilayah Region",
                reg_opts,
                index=(
                    reg_opts.index(defaults["reg"])
                    if defaults["reg"] in reg_opts
                    else 0
                ),
            )
        with c2:
            sa_opts = ["Aceh", "Medan", "Sibolga", "Sumbar", "Riau", "Kepri"]
            sa = st.selectbox(
                "Sales Area Retail",
                sa_opts,
                index=sa_opts.index(defaults["sa"]) if defaults["sa"] in sa_opts else 0,
            )
        with c3:
            with get_conn() as con:
                t_opts = [
                    r[0]
                    for r in con.execute(
                        "SELECT nama FROM tipe_agen_master ORDER BY nama"
                    ).fetchall()
                ]
            tipe = st.selectbox(
                "Tipe Agen LPG",
                t_opts,
                index=(
                    t_opts.index(defaults["tipe"]) if defaults["tipe"] in t_opts else 0
                ),
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div class="card"><div class="card-hdr">🚛 Data Kendaraan Armada</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            with get_conn() as con:
                k_opts = [
                    r[0]
                    for r in con.execute(
                        "SELECT nama FROM kendaraan_master ORDER BY nama"
                    ).fetchall()
                ]
            kend = st.selectbox(
                "Jenis Kendaraan",
                k_opts,
                index=(
                    k_opts.index(defaults["kend"]) if defaults["kend"] in k_opts else 0
                ),
            )
        with c2:
            jml = st.number_input(
                "Jumlah Kendaraan (Unit)",
                min_value=1,
                value=int(defaults["jml"]),
                step=1,
                format="%d",
            )
        with c3:
            kap = st.number_input(
                "Kapasitas Angkut (Misal: 560 Tbg) atau (1 MT)",
                min_value=1,
                value=int(defaults["kap"]),
                step=1,
                format="%d",
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div class="card"><div class="card-hdr">📈 Performa Operasional</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            util = st.number_input(
                "Rata-Rata Utilisasi (Trip/Hari)",
                min_value=0,
                value=int(defaults["util"]),
                step=1,
                format="%d",
            )
        with c2:
            lf = st.number_input(
                "Load Factor (%) (Persentase beban per kendaraan agen)",
                min_value=0,
                max_value=100,
                value=int(defaults["lf"]),
                step=1,
                format="%d",
            )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.form_submit_button(
            "💾  KONFIRMASI & SIMPAN DATA", use_container_width=True
        ):
            with get_conn() as con:
                if is_edit:
                    con.execute(
                        "UPDATE armada SET region=?,sales_area=?,tipe_agen=?,kendaraan=?,kapasitas=?,jumlah_kendaraan=?,utilisasi=?,load_factor=? WHERE id=?",
                        (reg, sa, tipe, kend, kap, jml, util, lf, target_id),
                    )
                    st.session_state.last_id = target_id
                else:
                    cur = con.execute(
                        "INSERT INTO armada(agen_id,region,sales_area,tipe_agen,kendaraan,kapasitas,jumlah_kendaraan,utilisasi,load_factor,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (
                            agen["id"],
                            reg,
                            sa,
                            tipe,
                            kend,
                            kap,
                            jml,
                            util,
                            lf,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                    st.session_state.last_id = cur.lastrowid
                con.commit()
            st.session_state.edit_id = None
            st.session_state.step = "success"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP: SUCCESS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "success":
    with get_conn() as con:
        d = con.execute(
            "SELECT a.id,g.nama,g.sold_to FROM armada a JOIN agen g ON a.agen_id=g.id WHERE a.id=?",
            (st.session_state.last_id,),
        ).fetchone()

    st.markdown(
        """
    <div class="success-box">
        <div style="font-size:3.2rem">✅</div>
        <h2>Data Berhasil Tersimpan!</h2>
        <p style="color:#065f46;font-size:.95rem;margin-top:.4rem">
            Data armada telah dicatat ke dalam database sistem.
        </p>
    </div>""",
        unsafe_allow_html=True,
    )

    if d:
        st.markdown(
            f"""
        <div class="card">
            <div class="card-hdr">📋 Ringkasan Data</div>
            <div style="display:flex;gap:2.5rem;flex-wrap:wrap;margin-top:.5rem">
                <div>
                    <div style="font-size:.75rem;color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:1px">Nama Agen</div>
                    <div style="font-size:1.15rem;font-weight:800;color:#002e6e">{d[1]}</div>
                </div>
                <div>
                    <div style="font-size:.75rem;color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:1px">Sold To</div>
                    <div style="font-size:1.15rem;font-weight:700;color:#1e40af">{d[2]}</div>
                </div>
                <div>
                    <div style="font-size:.75rem;color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:1px">ID Record</div>
                    <div style="font-size:1.15rem;font-weight:700;color:#475569">#{d[0]}</div>
                </div>
            </div>
        </div>""",
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✏️ Edit Data Ini", use_container_width=True):
            st.session_state.edit_id = st.session_state.last_id
            st.session_state.step = "input"
            st.rerun()
    with c2:
        if st.button("➕ Input Data Armada Lain", use_container_width=True):
            st.session_state.edit_id = None
            st.session_state.step = "input"
            st.rerun()
    with c3:
        if st.button("📋 Lihat Semua Data Saya", use_container_width=True):
            st.session_state.step = "my_data"
            st.rerun()

    st.markdown('<hr class="el-divider">', unsafe_allow_html=True)
    if st.button("🔒 Logout & Kembali ke Halaman Utama", use_container_width=False):
        st.session_state.logged_in_agen = None
        st.session_state.selected_agen = None
        st.session_state.edit_id = None
        st.session_state.step = "login"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP: MY DATA — Data Armada Milik Agen yang Login
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "my_data":
    agen = st.session_state.logged_in_agen
    if not agen:
        st.session_state.step = "login"
        st.rerun()

    st.markdown(
        f"""
    <div class="info-strip">
        <div style="font-size:2rem">🏢</div>
        <div>
            <div class="is-name">{agen['nama']}</div>
            <div class="is-sub">Sold To: {agen['sto']}</div>
        </div>
        <div style="margin-left:auto">
            <span class="badge">📋 DATA ARMADA SAYA</span>
        </div>
    </div>""",
        unsafe_allow_html=True,
    )

    with get_conn() as con:
        df_my = pd.read_sql_query(
            """SELECT id, region, sales_area, tipe_agen, kendaraan,
               kapasitas, jumlah_kendaraan, utilisasi, load_factor, created_at
               FROM armada WHERE agen_id=? ORDER BY id DESC""",
            con,
            params=(agen["id"],),
        )

    if len(df_my) == 0:
        st.info("Belum ada data armada yang diinput. Silakan input data baru.")
    else:
        st.markdown(
            f'<p style="color:#5b78a8;font-weight:600;font-size:.9rem;margin:.3rem 0 .8rem">'
            f"Total {len(df_my)} record armada ditemukan</p>",
            unsafe_allow_html=True,
        )
        for _, row in df_my.iterrows():
            with st.expander(
                f"🚛  {row['kendaraan']}  ×{row['jumlah_kendaraan']} unit  —  {row['sales_area']}  |  {row['created_at']}"
            ):
                cc1, cc2, cc3, cc4 = st.columns(4)
                cc1.metric("Kapasitas", f"{row['kapasitas']} Tbg")
                cc2.metric("Utilisasi", f"{row['utilisasi']} trip/hr")
                cc3.metric("Load Factor", f"{row['load_factor']}%")
                cc4.metric("Tipe Agen", row["tipe_agen"])
                st.markdown(
                    f"**Region:** {row['region']}  &nbsp;|&nbsp;  **Sales Area:** {row['sales_area']}"
                )
                st.markdown('<hr class="el-divider">', unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button(
                    "✏️ Edit", key=f"my_edit_{row['id']}", use_container_width=True
                ):
                    st.session_state.edit_id = row["id"]
                    st.session_state.step = "input"
                    st.rerun()
                if b2.button(
                    "🗑️ Hapus", key=f"my_del_{row['id']}", use_container_width=True
                ):
                    with get_conn() as con:
                        con.execute("DELETE FROM armada WHERE id=?", (row["id"],))
                        con.commit()
                    st.success(f"✅ Record berhasil dihapus.")
                    st.rerun()

    st.markdown('<hr class="el-divider">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Input Data Baru", use_container_width=True):
            st.session_state.edit_id = None
            st.session_state.step = "input"
            st.rerun()
    with c2:
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.logged_in_agen = None
            st.session_state.selected_agen = None
            st.session_state.step = "login"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP: ADMIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "admin_view":

    # ── GUARD: wajib login admin ───────────────────────────────────────────────
    if not st.session_state.admin_mode:
        st.markdown(
            """
        <div class="access-denied">
            <div style="font-size:3rem">⛔</div>
            <div style="font-size:1.3rem;font-weight:800;color:#be123c;margin:.5rem 0">Akses Ditolak</div>
            <div style="color:#9f1239;font-size:.95rem;">Silakan login sebagai Admin melalui sidebar terlebih dahulu.</div>
        </div>""",
            unsafe_allow_html=True,
        )
        st.stop()

    st.markdown(
        '<div style="font-size:1.4rem;font-weight:900;color:#002e6e;margin-bottom:1.2rem">📊 Dashboard Admin — Pengelolaan Data Armada</div>',
        unsafe_allow_html=True,
    )

    # ── Load semua data ────────────────────────────────────────────────────────
    with get_conn() as con:
        df = pd.read_sql_query(
            """SELECT a.id, g.nama AS Agen, g.sold_to AS Sold_To,
               a.region, a.sales_area, a.tipe_agen, a.kendaraan,
               a.kapasitas, a.jumlah_kendaraan, a.utilisasi, a.load_factor, a.created_at
               FROM armada a JOIN agen g ON a.agen_id=g.id ORDER BY a.id DESC""",
            con,
        )
        df_agen = pd.read_sql_query(
            "SELECT id, sold_to, nama, password FROM agen ORDER BY nama", con
        )

    # ── METRICS ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Record Armada", len(df))
    c2.metric("Total Agen Terdaftar", len(df_agen))
    c3.metric("Agen Punya Data", df["Agen"].nunique() if len(df) > 0 else 0)
    c4.metric(
        "Total Unit Kendaraan", int(df["jumlah_kendaraan"].sum()) if len(df) > 0 else 0
    )

    st.markdown('<hr class="el-divider">', unsafe_allow_html=True)

    # ── EXPORT EXCEL ──────────────────────────────────────────────────────────
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data Armada", index=False)
        df_agen_export = df_agen[["id", "sold_to", "nama"]].copy()
        df_agen_export.columns = ["ID", "Sold To Party", "Nama Agen"]
        df_agen_export.to_excel(writer, sheet_name="Daftar Agen", index=False)
        with get_conn() as con:
            df_kend = pd.read_sql_query(
                "SELECT nama FROM kendaraan_master ORDER BY nama", con
            )
            df_tipe = pd.read_sql_query(
                "SELECT nama FROM tipe_agen_master ORDER BY nama", con
            )
        df_kend.to_excel(writer, sheet_name="Master Kendaraan", index=False)
        df_tipe.to_excel(writer, sheet_name="Master Tipe Agen", index=False)

    st.download_button(
        "📥 Download Laporan Excel (Semua Sheet)",
        buf.getvalue(),
        f"Laporan_Armada_LPG_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        "application/vnd.ms-excel",
        use_container_width=False,
    )

    st.markdown('<hr class="el-divider">', unsafe_allow_html=True)

    tab_armada, tab_agen, tab_master = st.tabs(
        ["📋 Data Armada", "🏢 Manajemen Agen", "🔧 Master Data"]
    )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: Data Armada — CRUD lengkap
    # ══════════════════════════════════════════════════════════════════════════
    with tab_armada:
        if len(df) == 0:
            st.info("Belum ada data armada yang diinput.")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filter_agen = st.text_input(
                    "🔍 Filter Nama Agen",
                    placeholder="Ketik nama agen...",
                    key="f_agen",
                )
            with col_f2:
                region_list = ["Semua"] + sorted(df["region"].unique().tolist())
                filter_reg = st.selectbox("Filter Region", region_list, key="f_reg")
            with col_f3:
                tipe_list = ["Semua"] + sorted(df["tipe_agen"].unique().tolist())
                filter_tipe = st.selectbox("Filter Tipe Agen", tipe_list, key="f_tipe")

            df_view = df.copy()
            if filter_agen:
                df_view = df_view[
                    df_view["Agen"].str.contains(filter_agen, case=False, na=False)
                ]
            if filter_reg != "Semua":
                df_view = df_view[df_view["region"] == filter_reg]
            if filter_tipe != "Semua":
                df_view = df_view[df_view["tipe_agen"] == filter_tipe]

            st.markdown(
                f'<p style="color:#5b78a8;font-weight:600;font-size:.9rem;margin:.3rem 0 .8rem">'
                f"Menampilkan {len(df_view)} dari {len(df)} record</p>",
                unsafe_allow_html=True,
            )

            for _, row in df_view.iterrows():
                with st.expander(
                    f"🚛  {row['Agen']}  ({row['Sold_To']})  —  {row['kendaraan']}  ×{row['jumlah_kendaraan']} unit  |  {row['created_at']}"
                ):
                    cc1, cc2, cc3, cc4 = st.columns(4)
                    cc1.metric("Kapasitas", f"{row['kapasitas']} Tbg")
                    cc2.metric("Utilisasi", f"{row['utilisasi']} trip/hr")
                    cc3.metric("Load Factor", f"{row['load_factor']}%")
                    cc4.metric("Tipe Agen", row["tipe_agen"])
                    st.markdown(
                        f"**Region:** {row['region']}  &nbsp;|&nbsp;  **Sales Area:** {row['sales_area']}"
                    )
                    st.markdown('<hr class="el-divider">', unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
                    if b1.button(
                        "✏️ Edit Record",
                        key=f"ae_{row['id']}",
                        use_container_width=True,
                    ):
                        matched = df_agen[df_agen["sold_to"] == row["Sold_To"]]
                        agen_id = (
                            int(matched["id"].values[0]) if len(matched) > 0 else 0
                        )
                        st.session_state.edit_id = row["id"]
                        st.session_state.selected_agen = {
                            "id": agen_id,
                            "nama": row["Agen"],
                            "sto": row["Sold_To"],
                        }
                        st.session_state.step = "input"
                        st.rerun()
                    if b2.button(
                        "🗑️ Hapus Record",
                        key=f"ad_{row['id']}",
                        use_container_width=True,
                    ):
                        with get_conn() as con:
                            con.execute("DELETE FROM armada WHERE id=?", (row["id"],))
                            con.commit()
                        st.success(f"✅ Record #{row['id']} berhasil dihapus.")
                        st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: Manajemen Agen — CRUD lengkap + reset password
    # ══════════════════════════════════════════════════════════════════════════
    with tab_agen:
        # ── Tambah Agen Baru ─────────────────────────────────────────────────
        st.markdown(
            '<div class="card"><div class="card-hdr">➕ Tambah Agen Baru (Manual)</div>',
            unsafe_allow_html=True,
        )
        with st.form("admin_add_agen"):
            ca1, ca2 = st.columns(2)
            new_sto = ca1.text_input("Sold To Party", placeholder="73001234")
            new_nama = ca2.text_input("Nama Agen", placeholder="PT CONTOH JAYA")
            if st.form_submit_button(
                "➕ Tambah & Generate Password", use_container_width=True
            ):
                if new_sto.strip() and new_nama.strip():
                    npwd = gen_password()
                    try:
                        with get_conn() as con:
                            con.execute(
                                "INSERT INTO agen(sold_to,nama,password) VALUES(?,?,?)",
                                (
                                    new_sto.strip().upper(),
                                    new_nama.strip().upper(),
                                    npwd,
                                ),
                            )
                            con.commit()
                        st.success(f"✅ Agen ditambahkan. Password: **`{npwd}`**")
                        st.rerun()
                    except Exception:
                        st.error("❌ Sold To Party sudah terdaftar.")
                else:
                    st.error("Lengkapi semua field.")
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Daftar Agen + Edit + Reset Password + Hapus ───────────────────────
        st.markdown(
            '<div class="card"><div class="card-hdr">📋 Daftar Agen Terdaftar</div>',
            unsafe_allow_html=True,
        )
        with get_conn() as con:
            df_agen2 = pd.read_sql_query(
                "SELECT id, sold_to, nama, password FROM agen ORDER BY nama", con
            )

        if len(df_agen2) == 0:
            st.info("Belum ada agen terdaftar.")
        else:
            search_agen = st.text_input(
                "🔍 Cari Agen",
                placeholder="Ketik nama atau sold to...",
                key="srch_agen",
            )
            df_agen_show = df_agen2.copy()
            if search_agen:
                df_agen_show = df_agen_show[
                    df_agen_show["nama"].str.contains(search_agen, case=False, na=False)
                    | df_agen_show["sold_to"].str.contains(
                        search_agen, case=False, na=False
                    )
                ]

            for _, row in df_agen_show.iterrows():
                with st.expander(f"🏢  {row['nama']}  —  Sold To: {row['sold_to']}"):
                    ec1, ec2 = st.columns(2)
                    new_nm = ec1.text_input(
                        "Nama Agen", value=row["nama"], key=f"enm_{row['id']}"
                    )
                    ec2.markdown(
                        f"**Password saat ini:** `{row['password']}`",
                        unsafe_allow_html=False,
                    )

                    st.markdown('<hr class="el-divider">', unsafe_allow_html=True)

                    b1, b2, b3 = st.columns(3)

                    if b1.button(
                        "💾 Simpan Nama",
                        key=f"esv_{row['id']}",
                        use_container_width=True,
                    ):
                        with get_conn() as con:
                            con.execute(
                                "UPDATE agen SET nama=? WHERE id=?",
                                (new_nm.strip().upper(), row["id"]),
                            )
                            con.commit()
                        st.success(
                            f"✅ Nama agen diperbarui menjadi {new_nm.strip().upper()}."
                        )
                        st.rerun()

                    if b2.button(
                        "🔄 Reset Password",
                        key=f"erpw_{row['id']}",
                        use_container_width=True,
                    ):
                        new_rpwd = gen_password()
                        with get_conn() as con:
                            con.execute(
                                "UPDATE agen SET password=? WHERE id=?",
                                (new_rpwd, row["id"]),
                            )
                            con.commit()
                        st.session_state[f"admin_rpwd_{row['id']}"] = new_rpwd
                        st.rerun()

                    if b3.button(
                        "🗑️ Hapus Agen",
                        key=f"edl_{row['id']}",
                        use_container_width=True,
                    ):
                        with get_conn() as con:
                            con.execute("DELETE FROM agen WHERE id=?", (row["id"],))
                            con.commit()
                        st.success(f"✅ Agen {row['nama']} dihapus.")
                        st.rerun()

                    if st.session_state.get(f"admin_rpwd_{row['id']}"):
                        rpwd_val = st.session_state[f"admin_rpwd_{row['id']}"]
                        st.markdown(
                            f"""
                        <div class="resetpwd-box">
                            <div class="rpwd-label">🔑 Password Baru untuk <b>{row['nama']}</b></div>
                            <div class="rpwd-code">{rpwd_val}</div>
                            <div style="font-size:.78rem;color:#b45309;margin-top:.5rem;">
                                Catat dan berikan ke agen. Klik tombol di bawah setelah dicatat.
                            </div>
                        </div>""",
                            unsafe_allow_html=True,
                        )
                        if st.button("✅ Sudah Dicatat", key=f"close_rpwd_{row['id']}"):
                            del st.session_state[f"admin_rpwd_{row['id']}"]
                            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: Master Data — CRUD Jenis Kendaraan & Tipe Agen
    # ══════════════════════════════════════════════════════════════════════════
    with tab_master:
        cm1, cm2 = st.columns(2)

        # ── Master Kendaraan ──────────────────────────────────────────────────
        with cm1:
            st.markdown(
                '<div class="card"><div class="card-hdr">🚛 Master Jenis Kendaraan</div>',
                unsafe_allow_html=True,
            )
            with get_conn() as con:
                ki = con.execute(
                    "SELECT id,nama FROM kendaraan_master ORDER BY nama"
                ).fetchall()

            if not ki:
                st.info("Belum ada data jenis kendaraan.")
            else:
                for kid, knm in ki:
                    kc1, kc2, kc3 = st.columns([4, 1, 1])
                    new_knm = kc1.text_input(
                        "nama",
                        value=knm,
                        key=f"knm_{kid}",
                        label_visibility="collapsed",
                    )
                    if kc2.button("💾", key=f"ksv_{kid}", help="Simpan perubahan"):
                        if new_knm.strip() and new_knm.strip().upper() != knm:
                            try:
                                with get_conn() as con:
                                    con.execute(
                                        "UPDATE kendaraan_master SET nama=? WHERE id=?",
                                        (new_knm.strip().upper(), kid),
                                    )
                                    con.commit()
                                st.success(f"✅ Diperbarui: {new_knm.strip().upper()}")
                                st.rerun()
                            except Exception:
                                st.error("❌ Nama sudah ada.")
                    if kc3.button("🗑️", key=f"dkd_{kid}", help="Hapus"):
                        with get_conn() as con:
                            con.execute(
                                "DELETE FROM kendaraan_master WHERE id=?", (kid,)
                            )
                            con.commit()
                        st.rerun()

            st.markdown('<hr class="el-divider">', unsafe_allow_html=True)
            with st.form("fm_kend"):
                nk = st.text_input(
                    "Tambah Jenis Kendaraan Baru", placeholder="Contoh: MOBIL BOX"
                )
                if st.form_submit_button("+ Tambah", use_container_width=True):
                    if nk.strip():
                        try:
                            with get_conn() as con:
                                con.execute(
                                    "INSERT INTO kendaraan_master(nama) VALUES(?)",
                                    (nk.strip().upper(),),
                                )
                                con.commit()
                            st.success(
                                f"✅ Kendaraan '{nk.strip().upper()}' ditambahkan."
                            )
                            st.rerun()
                        except Exception:
                            st.error("❌ Nama kendaraan sudah ada.")
                    else:
                        st.error("Nama tidak boleh kosong.")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Master Tipe Agen ──────────────────────────────────────────────────
        with cm2:
            st.markdown(
                '<div class="card"><div class="card-hdr">🏷️ Master Tipe Agen</div>',
                unsafe_allow_html=True,
            )
            with get_conn() as con:
                ti = con.execute(
                    "SELECT id,nama FROM tipe_agen_master ORDER BY nama"
                ).fetchall()

            if not ti:
                st.info("Belum ada data tipe agen.")
            else:
                for tid, tnm in ti:
                    tc1, tc2, tc3 = st.columns([4, 1, 1])
                    new_tnm = tc1.text_input(
                        "nama",
                        value=tnm,
                        key=f"tnm_{tid}",
                        label_visibility="collapsed",
                    )
                    if tc2.button("💾", key=f"tsv_{tid}", help="Simpan perubahan"):
                        if new_tnm.strip() and new_tnm.strip().upper() != tnm:
                            try:
                                with get_conn() as con:
                                    con.execute(
                                        "UPDATE tipe_agen_master SET nama=? WHERE id=?",
                                        (new_tnm.strip().upper(), tid),
                                    )
                                    con.commit()
                                st.success(f"✅ Diperbarui: {new_tnm.strip().upper()}")
                                st.rerun()
                            except Exception:
                                st.error("❌ Nama sudah ada.")
                    if tc3.button("🗑️", key=f"dtd_{tid}", help="Hapus"):
                        with get_conn() as con:
                            con.execute(
                                "DELETE FROM tipe_agen_master WHERE id=?", (tid,)
                            )
                            con.commit()
                        st.rerun()

            st.markdown('<hr class="el-divider">', unsafe_allow_html=True)
            with st.form("fm_tipe"):
                nt = st.text_input(
                    "Tambah Tipe Agen Baru", placeholder="Contoh: RETAIL"
                )
                if st.form_submit_button("+ Tambah", use_container_width=True):
                    if nt.strip():
                        try:
                            with get_conn() as con:
                                con.execute(
                                    "INSERT INTO tipe_agen_master(nama) VALUES(?)",
                                    (nt.strip().upper(),),
                                )
                                con.commit()
                            st.success(
                                f"✅ Tipe agen '{nt.strip().upper()}' ditambahkan."
                            )
                            st.rerun()
                        except Exception:
                            st.error("❌ Nama tipe agen sudah ada.")
                    else:
                        st.error("Nama tidak boleh kosong.")
            st.markdown("</div>", unsafe_allow_html=True)
