import streamlit as st
import json
import io
import requests

try:
    import fitz
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

st.set_page_config(
    page_title="PolicyAI — Healthcare Policy Analyzer",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #f0f2f6 !important; }
.main .block-container { background: #f0f2f6 !important; padding: 1.5rem 2rem 4rem 2rem !important; max-width: 1200px; }

[data-testid="stSidebar"] { background: #0f172a !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(99,102,241,0.15) !important;
    border: 1px solid rgba(99,102,241,0.4) !important;
    color: #a5b4fc !important;
    border-radius: 8px !important;
    width: 100% !important;
    font-size: 12px !important;
    text-align: left !important;
    padding: 8px 12px !important;
    margin-bottom: 3px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.3) !important;
}
.stTabs [data-baseweb="tab"] { font-size: 14px !important; font-weight: 500 !important; color: #64748b !important; }
.stTabs [aria-selected="true"] { color: #0f172a !important; font-weight: 600 !important; }

/* Cards */
.white-card {
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.card-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f1f5f9;
}

/* Policy hero */
.policy-hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 20px;
    color: white;
}
.policy-hero h2 { font-size: 22px; font-weight: 700; color: #ffffff; margin: 0 0 8px 0; }
.policy-hero p { font-size: 14px; color: #94a3b8; margin: 0; line-height: 1.6; }

/* Metric row */
.metric-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 20px; }
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
}
.metric-label { font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing:.06em; margin-bottom: 6px; }
.metric-val { font-size: 17px; font-weight: 700; color: #0f172a; }

/* Badges */
.badge { display:inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-high { background:#fee2e2; color:#b91c1c; }
.badge-medium { background:#fef3c7; color:#92400e; }
.badge-low { background:#dcfce7; color:#166534; }
.badge-neutral { background:#e0e7ff; color:#3730a3; }
.badge-blue { background:#dbeafe; color:#1d4ed8; }

/* Key finding */
.finding-row {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    padding: 14px;
    background: #f8fafc;
    border-radius: 10px;
    margin-bottom: 10px;
    border-left: 4px solid #6366f1;
}
.finding-num {
    background: #6366f1;
    color: white;
    font-size: 12px;
    font-weight: 700;
    min-width: 26px;
    height: 26px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.finding-text { font-size: 14px; color: #1e293b; line-height: 1.65; font-weight: 400; }

/* Team impact cards */
.team-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin-bottom: 16px; }
.team-card { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }
.team-card-header { padding: 12px 16px; font-size: 13px; font-weight: 700; color: #fff; }
.team-card-header.benefits { background: #4f46e5; }
.team-card-header.platform { background: #0891b2; }
.team-card-header.marketplace { background: #059669; }
.team-card-header.consumer { background: #d97706; }
.team-card-header.payer { background: #7c3aed; }
.team-card-header.provider { background: #dc2626; }
.team-card-body { padding: 14px 16px; }
.team-bullet { display:flex; gap:10px; margin-bottom:10px; align-items:flex-start; }
.team-dot { width:7px; height:7px; border-radius:50%; background:#6366f1; flex-shrink:0; margin-top:6px; }
.team-text { font-size:13px; color:#334155; line-height:1.55; }

/* Action cards */
.action-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.action-top { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.action-title { font-size:15px; font-weight:600; color:#0f172a; }
.action-owner { font-size:12px; color:#64748b; margin-bottom:8px; }
.action-label { font-size:11px; font-weight:700; color:#6366f1; text-transform:uppercase; letter-spacing:.05em; margin-bottom:6px; }
.action-detail { font-size:13px; color:#475569; line-height:1.6; background:#f8fafc; border-radius:8px; padding:10px 14px; }

/* Risk rows */
.risk-header { display:grid; grid-template-columns:90px 2fr 120px 2fr; gap:12px; padding:6px 14px; }
.risk-row-item { display:grid; grid-template-columns:90px 2fr 120px 2fr; gap:12px; padding:12px 14px; background:#f8fafc; border-radius:8px; margin-bottom:8px; align-items:start; }
.risk-col-lbl { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#94a3b8; }
.risk-cell { font-size:13px; color:#1e293b; line-height:1.5; }
.risk-area-cell { font-size:12px; color:#64748b; font-weight:500; }
.risk-mit-cell { font-size:12px; color:#475569; line-height:1.5; }

/* Timeline */
.tl-row { display:flex; gap:18px; padding:14px 0; border-bottom:1px solid #f1f5f9; align-items:flex-start; }
.tl-row:last-child { border:none; }
.tl-date { background:#0f172a; color:#fff; font-size:11px; font-weight:700; padding:5px 12px; border-radius:6px; white-space:nowrap; flex-shrink:0; }
.tl-info h4 { font-size:14px; font-weight:600; color:#0f172a; margin:0 0 4px 0; }
.tl-info p { font-size:13px; color:#64748b; margin:0; line-height:1.5; }

/* Q&A */
.qa-user { background:#6366f1; color:#fff; padding:12px 16px; border-radius:12px 12px 2px 12px; font-size:13px; margin-bottom:8px; max-width:78%; margin-left:auto; line-height:1.5; }
.qa-ai { background:#f0fdf4; color:#1e293b; border:1px solid #bbf7d0; padding:12px 16px; border-radius:2px 12px 12px 12px; font-size:13px; margin-bottom:8px; line-height:1.6; }

/* Section divider */
.sec-divider { font-size:13px; font-weight:600; color:#6366f1; text-transform:uppercase; letter-spacing:.08em; margin:4px 0 12px 0; padding-bottom:8px; border-bottom:2px solid #e0e7ff; }

/* Download bar */
.dl-bar { background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:14px 20px; display:flex; align-items:center; justify-content:space-between; margin-top:8px; }
.dl-label { font-size:13px; color:#64748b; }
.dl-label strong { color:#0f172a; }
</style>
""", unsafe_allow_html=True)

# ── Presets ───────────────────────────────────────────────────────────────────
PRESETS = {
    "ACA 2026 Payment Notice":     "ACA 2026 Notice of Benefit and Payment Parameters — Marketplace payment notice covering risk adjustment updates, premium rate review, cost sharing limits, plan certification, and enrollee protections.",
    "Essential Health Benefits":   "ACA Essential Health Benefits (EHB) update — benchmark plan selection, state flexibility, habilitative services standards, enforcement for qualified health plans.",
    "Cost Sharing Reductions":     "ACA Cost Sharing Reduction (CSR) reconciliation rules — issuer obligations, silver loading, CMS reimbursement, reconciliation methodology.",
    "Network Adequacy Standards":  "ACA Network Adequacy Standards for QHPs — time/distance, wait times, specialist access, telehealth credit, CMS enforcement.",
    "Preventive Care Mandate":     "ACA Preventive Services Coverage Mandate — Braidwood status, no-cost-sharing for USPSTF A/B services, contraceptive coverage, issuer obligations.",
    "Medicaid FMAP Update":        "Medicaid FMAP update — federal matching rate adjustments, DSH allotments, state plan amendments, managed care rate certification.",
    "Medicare IPPS Rule":          "Medicare IPPS final rule — base rate update, quality programs, coding changes, wage index, hospital cost reporting.",
    "Part D Drug Pricing":         "Medicare Part D drug pricing — negotiated prices, inflation rebates, out-of-pocket cap under Inflation Reduction Act, plan bids.",
}

# ── Extract text ──────────────────────────────────────────────────────────────
def extract_text(f):
    name = f.name.lower()
    raw  = f.read()
    if name.endswith(".pdf"):
        if not PDF_SUPPORT:
            return None, "PyMuPDF not installed."
        doc  = fitz.open(stream=raw, filetype="pdf")
        text = "".join(p.get_text() for p in doc)
        return text[:15000], None
    if name.endswith(".docx"):
        if not DOCX_SUPPORT:
            return None, "python-docx not installed."
        doc  = Document(io.BytesIO(raw))
        text = "\n".join(p.text for p in doc.paragraphs)
        return text[:15000], None
    if name.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore")[:15000], None
    return None, "Unsupported file type."

# ── Groq call ─────────────────────────────────────────────────────────────────
def call_groq(prompt: str, api_key: str) -> str:
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 2500
        },
        timeout=60
    )
    if not res.ok:
        raise Exception(f"Groq error {res.status_code}: {res.text[:200]}")
    return res.json()["choices"][0]["message"]["content"]

# ── Analyze ───────────────────────────────────────────────────────────────────
def analyze_policy(text: str, api_key: str) -> dict:
    prompt = (
        "You are a senior healthcare regulatory analyst. Analyze this policy for a private health insurance marketplace company. "
        "Return ONLY raw JSON — no markdown fences, no preamble, nothing else.\n\n"
        f"Policy text:\n\"\"\"\n{text[:12000]}\n\"\"\"\n\n"
        "Return ONLY this exact JSON:\n"
        "{\n"
        '  "policyName": "short official name",\n'
        '  "intro": "2-sentence plain-language overview any employee can understand",\n'
        '  "effectiveDate": "date or TBD",\n'
        '  "policyType": "ACA|Medicaid|Medicare|Other",\n'
        '  "regulatoryImpact": "High|Medium|Low",\n'
        '  "complianceComplexity": "High|Medium|Low",\n'
        '  "executiveSummary": "3-4 sentences: what changed, why it matters, what the company must do",\n'
        '  "keyFindings": ["finding 1","finding 2","finding 3","finding 4"],\n'
        '  "benefitsPlatformImpact": ["how this changes benefits design or coverage rules on the platform","impact 2","impact 3"],\n'
        '  "marketplaceImpact": ["how this affects the private marketplace product or enrollment","impact 2","impact 3"],\n'
        '  "engineeringImpact": ["system or data change required","change 2","change 3"],\n'
        '  "consumerImpact": ["what changes for end users/employees","impact 2","impact 3"],\n'
        '  "payerImpact": ["what changes for insurance carriers/issuers","impact 2","impact 3"],\n'
        '  "providerImpact": ["what changes for healthcare providers","impact 2","impact 3"],\n'
        '  "actions": [\n'
        '    {"title":"action title","detail":"what to do and how","priority":"High|Medium|Low","owner":"PM|Engineering|Compliance|Benefits|Legal","dueDate":"timeframe"},\n'
        '    {"title":"action title","detail":"what to do and how","priority":"High|Medium|Low","owner":"PM|Engineering|Compliance|Benefits|Legal","dueDate":"timeframe"},\n'
        '    {"title":"action title","detail":"what to do and how","priority":"High|Medium|Low","owner":"PM|Engineering|Compliance|Benefits|Legal","dueDate":"timeframe"},\n'
        '    {"title":"action title","detail":"what to do and how","priority":"High|Medium|Low","owner":"PM|Engineering|Compliance|Benefits|Legal","dueDate":"timeframe"}\n'
        '  ],\n'
        '  "risks": [\n'
        '    {"level":"High|Medium|Low","risk":"risk description","area":"Operational|Legal|Financial|Technical","mitigation":"how to mitigate"},\n'
        '    {"level":"High|Medium|Low","risk":"risk description","area":"Operational|Legal|Financial|Technical","mitigation":"how to mitigate"},\n'
        '    {"level":"High|Medium|Low","risk":"risk description","area":"Operational|Legal|Financial|Technical","mitigation":"how to mitigate"}\n'
        '  ],\n'
        '  "timeline": [\n'
        '    {"date":"Mon YYYY","event":"milestone","detail":"what needs to happen"},\n'
        '    {"date":"Mon YYYY","event":"milestone","detail":"what needs to happen"},\n'
        '    {"date":"Mon YYYY","event":"milestone","detail":"what needs to happen"}\n'
        '  ]\n'
        "}"
    )
    raw   = call_groq(prompt, api_key)
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

def ask_question(q: str, analysis: dict, policy_text: str, api_key: str) -> str:
    return call_groq(
        f"You analyzed this healthcare policy for a private marketplace company: {json.dumps(analysis)}. "
        f"Policy excerpt: \"{policy_text[:2000]}\". "
        f"Answer this question clearly for a product manager or engineer: {q}",
        api_key
    )

def badge(label, level=None):
    cls = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(level or label, "badge-neutral")
    return f'<span class="badge {cls}">{label}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚕ PolicyAI")
    st.markdown("**Private Marketplace Edition**")
    st.markdown("🟢 Free · Groq + Llama 3")
    st.divider()
    st.markdown("**🔑 Free Groq API Key**")
    st.markdown("1. [console.groq.com](https://console.groq.com)\n2. Sign up with Google\n3. API Keys → Create\n4. Paste below")
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    st.divider()
    st.markdown("**⚡ Quick Load Presets**")
    for name in PRESETS:
        if st.button(name, key=f"p_{name}"):
            st.session_state["policy_text"] = PRESETS[name]
            st.session_state["analysis"]    = None
            st.rerun()
    st.divider()
    st.caption("PDF · DOCX · TXT · Any healthcare policy\nFree hosting: Streamlit Cloud")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## ⚕ PolicyAI — Healthcare Policy Analyzer")
st.markdown("**For Product Managers, Engineers & Compliance Teams** — Upload any ACA / CMS / Medicaid document and get a clear, actionable brief broken down by team.")

# ── Input ─────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("📎 Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
if uploaded:
    with st.spinner("Reading document..."):
        extracted, err = extract_text(uploaded)
    if err:
        st.error(err)
    else:
        st.session_state["policy_text"] = extracted
        st.success(f"✅ **{uploaded.name}** — {len(extracted):,} characters extracted")

policy_text = st.text_area(
    "Or paste policy text / type a policy name:",
    value=st.session_state.get("policy_text", ""),
    height=100,
    placeholder="e.g. 'ACA 2026 Notice of Benefit and Payment Parameters' or paste the full rule text…"
)
if policy_text != st.session_state.get("policy_text", ""):
    st.session_state["policy_text"] = policy_text

c1, c2, _ = st.columns([1.2, 1, 5])
with c1:
    go = st.button("⚡ Analyze Policy", type="primary", use_container_width=True)
with c2:
    if st.button("🗑 Clear", use_container_width=True):
        st.session_state["policy_text"] = ""
        st.session_state["analysis"]    = None
        st.rerun()

if go:
    txt = st.session_state.get("policy_text", "").strip()
    if not txt:
        st.error("Please paste policy text, upload a file, or pick a preset from the sidebar.")
    elif not api_key:
        st.error("Add your free Groq API key in the sidebar. Get it at console.groq.com — no credit card.")
    else:
        prog = st.progress(0, text="Starting analysis…")
        try:
            prog.progress(20, text="Parsing regulatory text…")
            result = analyze_policy(txt, api_key)
            prog.progress(80, text="Structuring brief…")
            st.session_state["analysis"]      = result
            st.session_state["analysis_text"] = txt
            prog.progress(100, text="Done!")
            prog.empty()
        except json.JSONDecodeError:
            prog.empty()
            st.error("AI returned unexpected format — please try again.")
        except Exception as e:
            prog.empty()
            st.error(f"Failed: {e}")

# ── Results ───────────────────────────────────────────────────────────────────
D = st.session_state.get("analysis")
if D:
    st.markdown("---")

    # ── Policy hero ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="policy-hero">
        <h2>{D['policyName']}</h2>
        <p>{D['intro']}</p>
    </div>""", unsafe_allow_html=True)

    # ── Metric row ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card"><div class="metric-label">Policy Type</div><div class="metric-val">{badge(D['policyType'])}</div></div>
        <div class="metric-card"><div class="metric-label">Effective Date</div><div class="metric-val" style="font-size:15px">{D['effectiveDate']}</div></div>
        <div class="metric-card"><div class="metric-label">Regulatory Impact</div><div class="metric-val">{badge(D['regulatoryImpact'], D['regulatoryImpact'])}</div></div>
        <div class="metric-card"><div class="metric-label">Compliance Complexity</div><div class="metric-val">{badge(D['complianceComplexity'], D['complianceComplexity'])}</div></div>
    </div>""", unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "📋 Summary", "🏢 Team Impacts", "✅ Action Plan",
        "⚠️ Risk Register", "📅 Timeline", "💬 Q&A", "📤 Export"
    ])

    # ── TAB 1: SUMMARY ───────────────────────────────────────────────────────
    with t1:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="sec-divider">Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:15px;color:#1e293b;line-height:1.75;background:#f8fafc;padding:16px;border-radius:10px;border-left:4px solid #6366f1'>{D['executiveSummary']}</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="sec-divider">Key Findings</div>', unsafe_allow_html=True)
        for i, f in enumerate(D['keyFindings']):
            st.markdown(f'<div class="finding-row"><div class="finding-num">{i+1}</div><div class="finding-text">{f}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 2: TEAM IMPACTS ──────────────────────────────────────────────────
    with t2:
        st.markdown("#### Impact broken down by team — so everyone knows what matters to them")
        st.markdown("<br>", unsafe_allow_html=True)

        # Row 1: Benefits, Marketplace, Engineering
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="team-card"><div class="team-card-header benefits">🎁 Benefits Platform</div><div class="team-card-body">', unsafe_allow_html=True)
            for item in D.get('benefitsPlatformImpact', []):
                st.markdown(f'<div class="team-bullet"><div class="team-dot" style="background:#4f46e5"></div><div class="team-text">{item}</div></div>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="team-card"><div class="team-card-header marketplace">🛒 Marketplace / Enrollment</div><div class="team-card-body">', unsafe_allow_html=True)
            for item in D.get('marketplaceImpact', []):
                st.markdown(f'<div class="team-bullet"><div class="team-dot" style="background:#059669"></div><div class="team-text">{item}</div></div>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="team-card"><div class="team-card-header platform">⚙️ Engineering / Platform</div><div class="team-card-body">', unsafe_allow_html=True)
            for item in D.get('engineeringImpact', []):
                st.markdown(f'<div class="team-bullet"><div class="team-dot" style="background:#0891b2"></div><div class="team-text">{item}</div></div>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 2: Consumer, Payer, Provider
        c4, c5, c6 = st.columns(3)
        with c4:
            st.markdown('<div class="team-card"><div class="team-card-header consumer">👤 Consumers / Employees</div><div class="team-card-body">', unsafe_allow_html=True)
            for item in D.get('consumerImpact', []):
                st.markdown(f'<div class="team-bullet"><div class="team-dot" style="background:#d97706"></div><div class="team-text">{item}</div></div>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        with c5:
            st.markdown('<div class="team-card"><div class="team-card-header payer">🛡 Payers / Carriers</div><div class="team-card-body">', unsafe_allow_html=True)
            for item in D.get('payerImpact', []):
                st.markdown(f'<div class="team-bullet"><div class="team-dot" style="background:#7c3aed"></div><div class="team-text">{item}</div></div>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        with c6:
            st.markdown('<div class="team-card"><div class="team-card-header provider">🏥 Providers</div><div class="team-card-body">', unsafe_allow_html=True)
            for item in D.get('providerImpact', []):
                st.markdown(f'<div class="team-bullet"><div class="team-dot" style="background:#dc2626"></div><div class="team-text">{item}</div></div>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

    # ── TAB 3: ACTION PLAN ───────────────────────────────────────────────────
    with t3:
        st.markdown("#### Prioritized actions — who needs to do what and by when")
        st.markdown("")
        for a in D.get('actions', []):
            lvl = a.get('priority', 'Low')
            owner = a.get('owner', '')
            due   = a.get('dueDate', '')
            st.markdown(f"""
            <div class="action-card">
                <div class="action-top">
                    {badge(lvl, lvl)}
                    <span class="action-title">{a['title']}</span>
                </div>
                <div class="action-owner">
                    👤 <strong>Owner:</strong> {owner} &nbsp;|&nbsp; 📅 <strong>Due:</strong> {due}
                </div>
                <div class="action-detail">{a['detail']}</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 4: RISK REGISTER ─────────────────────────────────────────────────
    with t4:
        st.markdown("#### Compliance risk register — know what could go wrong and how to prevent it")
        st.markdown("")
        st.markdown("""
        <div class="risk-header">
            <span class="risk-col-lbl">Level</span>
            <span class="risk-col-lbl">Risk</span>
            <span class="risk-col-lbl">Area</span>
            <span class="risk-col-lbl">Mitigation</span>
        </div>""", unsafe_allow_html=True)
        for r in D.get('risks', []):
            lvl = r.get('level', 'Low')
            st.markdown(f"""
            <div class="risk-row-item">
                <div>{badge(lvl, lvl)}</div>
                <div class="risk-cell">{r['risk']}</div>
                <div class="risk-area-cell">{r['area']}</div>
                <div class="risk-mit-cell">{r['mitigation']}</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 5: TIMELINE ──────────────────────────────────────────────────────
    with t5:
        st.markdown("#### Key dates — deadlines your team needs to hit")
        st.markdown("")
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        for item in D.get('timeline', []):
            st.markdown(f"""
            <div class="tl-row">
                <div class="tl-date">{item['date']}</div>
                <div class="tl-info">
                    <h4>{item['event']}</h4>
                    <p>{item['detail']}</p>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 6: Q&A ───────────────────────────────────────────────────────────
    with t6:
        st.markdown("#### Ask anything — get answers in plain English")
        st.markdown("Examples: *What does this mean for our enrollment flow?* · *Do we need to update our plan comparison UI?* · *What's the engineering lift?*")
        st.markdown("")
        q = st.text_input("Your question", placeholder="What does this mean for our private marketplace enrollment experience?")
        if st.button("Ask", type="primary") and q:
            if not api_key:
                st.error("Add your Groq key in the sidebar.")
            else:
                with st.spinner("Thinking..."):
                    ans = ask_question(q, D, st.session_state.get("analysis_text", ""), api_key)
                st.markdown(f'<div class="qa-user">{q}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="qa-ai">{ans}</div>', unsafe_allow_html=True)

    # ── TAB 7: EXPORT ────────────────────────────────────────────────────────
    with t7:
        st.markdown("#### Export your analysis")
        st.markdown("")

        nl = "\n"
        findings   = nl.join(f"{i+1}. {f}" for i, f in enumerate(D['keyFindings']))
        benefits_l = nl.join(f"  - {x}" for x in D.get('benefitsPlatformImpact', []))
        market_l   = nl.join(f"  - {x}" for x in D.get('marketplaceImpact', []))
        eng_l      = nl.join(f"  - {x}" for x in D.get('engineeringImpact', []))
        consumer_l = nl.join(f"  - {x}" for x in D.get('consumerImpact', []))
        payer_l    = nl.join(f"  - {x}" for x in D.get('payerImpact', []))
        provider_l = nl.join(f"  - {x}" for x in D.get('providerImpact', []))
        action_l   = nl.join(
            f"{i+1}. [{a['priority']}] {a['title']}\n   Owner: {a['owner']} | Due: {a.get('dueDate','')}\n   {a['detail']}"
            for i, a in enumerate(D.get('actions', []))
        )
        risk_l     = nl.join(
            f"  [{r['level']}] {r['risk']} ({r['area']})\n   Mitigation: {r['mitigation']}"
            for r in D.get('risks', [])
        )
        tl_l       = nl.join(f"  {t['date']}: {t['event']} — {t['detail']}" for t in D.get('timeline', []))

        memo = (
            "=" * 60 + "\n"
            "HEALTHCARE POLICY ANALYSIS BRIEF\n"
            "=" * 60 + "\n\n"
            f"Policy:      {D['policyName']}\n"
            f"Effective:   {D['effectiveDate']}\n"
            f"Type:        {D['policyType']}\n"
            f"Impact:      {D['regulatoryImpact']}\n"
            f"Complexity:  {D['complianceComplexity']}\n\n"
            + "-" * 60 + "\n"
            "EXECUTIVE SUMMARY\n"
            + "-" * 60 + "\n"
            f"{D['executiveSummary']}\n\n"
            + "-" * 60 + "\n"
            "KEY FINDINGS\n"
            + "-" * 60 + "\n"
            f"{findings}\n\n"
            + "-" * 60 + "\n"
            "TEAM IMPACTS\n"
            + "-" * 60 + "\n"
            f"BENEFITS PLATFORM\n{benefits_l}\n\n"
            f"MARKETPLACE / ENROLLMENT\n{market_l}\n\n"
            f"ENGINEERING / PLATFORM\n{eng_l}\n\n"
            f"CONSUMERS / EMPLOYEES\n{consumer_l}\n\n"
            f"PAYERS / CARRIERS\n{payer_l}\n\n"
            f"PROVIDERS\n{provider_l}\n\n"
            + "-" * 60 + "\n"
            "ACTION PLAN\n"
            + "-" * 60 + "\n"
            f"{action_l}\n\n"
            + "-" * 60 + "\n"
            "COMPLIANCE RISK REGISTER\n"
            + "-" * 60 + "\n"
            f"{risk_l}\n\n"
            + "-" * 60 + "\n"
            "KEY DATES & MILESTONES\n"
            + "-" * 60 + "\n"
            f"{tl_l}\n\n"
            + "=" * 60 + "\n"
            "Generated by PolicyAI — Powered by Groq + Llama 3 (Free)\n"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "📄 Download Full Memo (.txt)",
                memo,
                file_name=f"{D['policyName'].replace(' ','-')}-brief.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            st.download_button(
                "{ } Download JSON",
                json.dumps(D, indent=2),
                file_name="policy-analysis.json",
                mime="application/json",
                use_container_width=True
            )
        with col3:
            st.info("💡 **Tip for LinkedIn:** Screenshot the Team Impacts tab and paste in your post with the app link.")

        st.markdown("")
        st.markdown("**What to post on LinkedIn:**")
        st.code(
            f'Just analyzed the "{D["policyName"]}" using PolicyAI — '
            f'an AI tool that reads any healthcare regulation and instantly generates a structured brief '
            f'for PMs, engineers and compliance teams. '
            f'Impact: {D["regulatoryImpact"]} | Complexity: {D["complianceComplexity"]}. '
            f'Try it here: [your-streamlit-url]',
            language=None
        )
