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

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("policy_text",""),("analysis",None),("analysis_text",""),("uploaded_name","")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif !important;}
.stApp{background:#f0f2f6 !important;}
.main .block-container{background:#f0f2f6 !important;padding:1.5rem 2rem 4rem 2rem !important;max-width:1280px;}

[data-testid="stSidebar"]{background:#0f172a !important;}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div{color:#cbd5e1 !important;}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3{color:#f1f5f9 !important;}
[data-testid="stSidebar"] .stButton>button{
    background:rgba(99,102,241,0.15) !important;
    border:1px solid rgba(99,102,241,0.4) !important;
    color:#a5b4fc !important;
    border-radius:8px !important;
    width:100% !important;
    font-size:12px !important;
    text-align:left !important;
    padding:8px 12px !important;
    margin-bottom:3px !important;
}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(99,102,241,0.3) !important;}
.stTabs [data-baseweb="tab"]{font-size:14px !important;font-weight:500 !important;color:#64748b !important;}
.stTabs [aria-selected="true"]{color:#0f172a !important;font-weight:600 !important;}

/* Hero */
.policy-hero{background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);border-radius:14px;padding:24px 28px;margin-bottom:20px;}
.policy-hero h2{font-size:22px;font-weight:700;color:#ffffff !important;margin:0 0 8px 0;}
.policy-hero p{font-size:14px;color:#94a3b8 !important;margin:0;line-height:1.7;}

/* Metrics */
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;}
.metric-card{background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;}
.metric-label{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;}
.metric-val{font-size:16px;font-weight:700;color:#0f172a;}

/* Cards */
.white-card{background:#ffffff;border-radius:12px;border:1px solid #e2e8f0;padding:20px 24px;margin-bottom:16px;}
.sec-divider{font-size:11px;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid #e0e7ff;}

/* Badges */
.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}
.badge-high{background:#fee2e2;color:#b91c1c;}
.badge-medium{background:#fef3c7;color:#92400e;}
.badge-low{background:#dcfce7;color:#166534;}
.badge-neutral{background:#e0e7ff;color:#3730a3;}
.badge-blue{background:#dbeafe;color:#1d4ed8;}
.badge-orange{background:#ffedd5;color:#9a3412;}

/* Rule plain */
.rule-plain{font-size:15px;color:#1e293b;line-height:1.8;background:#eff6ff;padding:18px 22px;border-radius:10px;border-left:5px solid #3b82f6;margin-bottom:16px;}
.exec-summary{font-size:15px;color:#1e293b;line-height:1.8;background:#f8fafc;padding:18px 22px;border-radius:10px;border-left:5px solid #6366f1;margin-bottom:16px;}

/* Section blocks in summary */
.policy-section{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px 20px;margin-bottom:12px;}
.policy-section-title{font-size:13px;font-weight:700;color:#0f172a;margin-bottom:10px;display:flex;align-items:center;gap:8px;}
.policy-section-rule{font-size:12px;font-weight:600;color:#6366f1;background:#e0e7ff;padding:2px 8px;border-radius:4px;margin-bottom:10px;display:inline-block;}
.policy-change{display:flex;gap:10px;margin-bottom:8px;align-items:flex-start;}
.policy-change-dot{width:6px;height:6px;border-radius:50%;background:#6366f1;flex-shrink:0;margin-top:7px;}
.policy-change-text{font-size:13px;color:#334155;line-height:1.6;}

/* Key findings */
.finding-row{display:flex;gap:14px;align-items:flex-start;padding:13px 16px;background:#f8fafc;border-radius:10px;margin-bottom:8px;border-left:3px solid #6366f1;}
.finding-num{background:#6366f1;color:white;font-size:11px;font-weight:700;min-width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.finding-text{font-size:13px;color:#1e293b;line-height:1.65;}

/* Team cards */
.team-card{background:#fff;border-radius:12px;border:1px solid #e2e8f0;overflow:hidden;height:100%;}
.team-card-header{padding:13px 16px;font-size:13px;font-weight:700;color:#fff !important;}
.tc-benefits{background:#4f46e5;}
.tc-marketplace{background:#059669;}
.tc-ecommerce{background:#ea580c;}
.tc-engineering{background:#0891b2;}
.tc-platform{background:#7c3aed;}
.tc-consumer{background:#d97706;}
.tc-payer{background:#0f766e;}
.tc-provider{background:#dc2626;}
.team-card-body{padding:14px 16px;}
.team-bullet{display:flex;gap:9px;margin-bottom:9px;align-items:flex-start;}
.team-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;margin-top:7px;}
.team-text{font-size:13px;color:#334155;line-height:1.55;}

/* Recommendation cards */
.rec-card{background:#fff;border-radius:12px;border:1px solid #e2e8f0;overflow:hidden;margin-bottom:16px;}
.rec-card-header{padding:14px 20px;font-size:14px;font-weight:700;color:#fff !important;display:flex;align-items:center;gap:10px;}
.rc-pm{background:#6366f1;}
.rc-eng{background:#0891b2;}
.rc-compliance{background:#059669;}
.rc-platform{background:#7c3aed;}
.rec-card-body{padding:0;}
.rec-item{padding:14px 20px;border-bottom:1px solid #f1f5f9;display:flex;gap:14px;align-items:flex-start;}
.rec-item:last-child{border-bottom:none;}
.rec-left{flex-shrink:0;width:56px;text-align:center;}
.rec-right{}
.rec-action{font-size:14px;font-weight:600;color:#0f172a;margin-bottom:4px;}
.rec-detail{font-size:13px;color:#475569;line-height:1.6;}
.rec-meta{font-size:11px;color:#94a3b8;margin-top:5px;}

/* Risk */
.risk-header{display:grid;grid-template-columns:90px 2fr 120px 2fr;gap:12px;padding:6px 16px;margin-bottom:4px;}
.risk-row-item{display:grid;grid-template-columns:90px 2fr 120px 2fr;gap:12px;padding:13px 16px;background:#f8fafc;border-radius:8px;margin-bottom:8px;align-items:start;}
.risk-col-lbl{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#94a3b8;}
.risk-cell{font-size:13px;color:#1e293b;line-height:1.5;}
.risk-area-cell{font-size:12px;color:#64748b;font-weight:500;}
.risk-mit-cell{font-size:12px;color:#475569;line-height:1.5;}

/* Timeline */
.tl-row{display:flex;gap:18px;padding:14px 0;border-bottom:1px solid #f1f5f9;align-items:flex-start;}
.tl-row:last-child{border:none;}
.tl-date{background:#0f172a;color:#fff;font-size:11px;font-weight:700;padding:5px 12px;border-radius:6px;white-space:nowrap;flex-shrink:0;margin-top:2px;}
.tl-info h4{font-size:14px;font-weight:600;color:#0f172a;margin:0 0 4px 0;}
.tl-info p{font-size:13px;color:#64748b;margin:0;line-height:1.5;}

/* Q&A */
.qa-user{background:#6366f1;color:#fff;padding:12px 16px;border-radius:12px 12px 2px 12px;font-size:13px;margin-bottom:8px;max-width:78%;margin-left:auto;line-height:1.5;}
.qa-ai{background:#f0fdf4;color:#1e293b;border:1px solid #bbf7d0;padding:14px 18px;border-radius:2px 12px 12px 12px;font-size:13px;line-height:1.7;}
</style>
""", unsafe_allow_html=True)

# ── Presets ───────────────────────────────────────────────────────────────────
PRESETS = {
    "ACA 2027 Payment Notice":    "ACA 2027 Notice of Benefit and Payment Parameters — proposed rule covering risk adjustment, user fees, marketing rules, standardized plan elimination, non-network QHP certification, ECP threshold reduction, APTC eligibility changes, WFTC legislation alignment, State EDE model, multi-year catastrophic plans, and SEP verification for plan year 2027.",
    "ACA 2026 Payment Notice":    "ACA 2026 Notice of Benefit and Payment Parameters — Marketplace payment notice covering risk adjustment updates, premium rate review, cost sharing limits, plan certification, and enrollee protections.",
    "Essential Health Benefits":  "ACA Essential Health Benefits (EHB) update — benchmark plan selection, state flexibility, habilitative services, enforcement for qualified health plans.",
    "Cost Sharing Reductions":    "ACA Cost Sharing Reduction (CSR) reconciliation — issuer obligations, silver loading, CMS reimbursement, reconciliation methodology.",
    "Network Adequacy":           "ACA Network Adequacy Standards for QHPs — time/distance, appointment wait times, specialist access, telehealth credit, CMS enforcement.",
    "Preventive Care Mandate":    "ACA Preventive Services Mandate — Braidwood status, no-cost-sharing for USPSTF A/B services, contraceptive coverage, issuer obligations.",
    "Medicaid FMAP Update":       "Medicaid FMAP — federal matching rate adjustments, DSH allotments, state plan amendments, managed care rate certification.",
    "Medicare IPPS Rule":         "Medicare IPPS final rule — base rate update, quality programs, coding changes, wage index, hospital cost reporting.",
    "Part D Drug Pricing":        "Medicare Part D — negotiated drug prices, inflation rebates, out-of-pocket cap under Inflation Reduction Act, plan bid impacts.",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
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

def call_groq(prompt: str, api_key: str) -> str:
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 4000
        },
        timeout=90
    )
    if not res.ok:
        raise Exception(f"API error {res.status_code}: {res.text[:200]}")
    return res.json()["choices"][0]["message"]["content"]

def analyze_policy(text: str, api_key: str) -> dict:
    prompt = (
        "You are a senior healthcare regulatory analyst for a private health insurance marketplace company like eHealth, Covered California, or HealthSherpa. "
        "Analyze this policy document thoroughly. Return ONLY raw JSON — no markdown fences, no preamble, no extra text whatsoever.\n\n"
        f"Policy document:\n\"\"\"\n{text[:13000]}\n\"\"\"\n\n"
        "Return ONLY this exact JSON structure. Be thorough — provide 6-8 bullets per impact section, 6-8 recommendations per role:\n"
        "{\n"
        '  "policyName": "full official name of the rule",\n'
        '  "effectiveDate": "plan year or date",\n'
        '  "policyType": "ACA|Medicaid|Medicare|Other",\n'
        '  "regulatoryImpact": "High|Medium|Low",\n'
        '  "complianceComplexity": "High|Medium|Low",\n'
        '  "ruleSummary": "3-4 sentences in plain English — what is this rule, who does it affect, what is the main goal. No legal jargon.",\n'
        '  "executiveSummary": "3-4 sentences — what changed, why it matters for a private marketplace company, what leadership needs to know and decide",\n'
        '  "keyFindings": [\n'
        '    "Plain English finding 1 — specific change and its impact",\n'
        '    "Plain English finding 2",\n'
        '    "Plain English finding 3",\n'
        '    "Plain English finding 4",\n'
        '    "Plain English finding 5",\n'
        '    "Plain English finding 6",\n'
        '    "Plain English finding 7",\n'
        '    "Plain English finding 8",\n'
        '    "Plain English finding 9",\n'
        '    "Plain English finding 10"\n'
        '  ],\n'
        '  "policySections": [\n'
        '    {\n'
        '      "sectionName": "Section name e.g. Program Integrity",\n'
        '      "ruleReference": "Rule or section number if available",\n'
        '      "changes": ["Plain English change 1","Plain English change 2","Plain English change 3"]\n'
        '    }\n'
        '  ],\n'
        '  "benefitsPlatformImpact": [\n'
        '    "Specific impact on benefits design or coverage rules — 6 to 8 items",\n'
        '    "impact 2","impact 3","impact 4","impact 5","impact 6","impact 7","impact 8"\n'
        '  ],\n'
        '  "marketplaceImpact": [\n'
        '    "Specific impact on enrollment, plan shopping, eligibility for marketplace like eHealth or Covered California — 6 to 8 items",\n'
        '    "impact 2","impact 3","impact 4","impact 5","impact 6","impact 7","impact 8"\n'
        '  ],\n'
        '  "ecommerceImpact": [\n'
        '    "Specific impact on plan shopping UI, cart, checkout, pricing display, plan comparison, SEO — 6 to 8 items",\n'
        '    "impact 2","impact 3","impact 4","impact 5","impact 6","impact 7","impact 8"\n'
        '  ],\n'
        '  "engineeringImpact": [\n'
        '    "Specific system, API, data, or logic change required — 6 to 8 items",\n'
        '    "impact 2","impact 3","impact 4","impact 5","impact 6","impact 7","impact 8"\n'
        '  ],\n'
        '  "platformTeamImpact": [\n'
        '    "Specific infrastructure, API gateway, data pipeline, shared services, or DevOps change — 6 to 8 items",\n'
        '    "impact 2","impact 3","impact 4","impact 5","impact 6","impact 7","impact 8"\n'
        '  ],\n'
        '  "consumerImpact": [\n'
        '    "What changes for end users — 5 to 6 items",\n'
        '    "impact 2","impact 3","impact 4","impact 5","impact 6"\n'
        '  ],\n'
        '  "payerImpact": [\n'
        '    "What changes for insurance carriers — 5 to 6 items",\n'
        '    "impact 2","impact 3","impact 4","impact 5","impact 6"\n'
        '  ],\n'
        '  "providerImpact": [\n'
        '    "What changes for healthcare providers — 4 to 5 items",\n'
        '    "impact 2","impact 3","impact 4","impact 5"\n'
        '  ],\n'
        '  "pmRecommendations": [\n'
        '    {"action":"specific roadmap action","detail":"plain English — what to do, why, referencing the actual rule provision","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 2","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 3","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 4","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 5","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 6","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 7","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"}\n'
        '  ],\n'
        '  "engineeringRecommendations": [\n'
        '    {"action":"specific thing to build or change","detail":"technical plain English — what system, what change, what rule requires it","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 2","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 3","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 4","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 5","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 6","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 7","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"}\n'
        '  ],\n'
        '  "platformRecommendations": [\n'
        '    {"action":"specific infra or platform change","detail":"what to build, scale, or configure and why","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 2","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 3","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 4","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 5","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 6","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"}\n'
        '  ],\n'
        '  "complianceRecommendations": [\n'
        '    {"action":"specific filing or compliance action","detail":"what to file, certify, update, or document and deadline","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 2","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 3","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 4","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 5","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"},\n'
        '    {"action":"action 6","detail":"detail","priority":"High|Medium|Low","timeline":"timeframe"}\n'
        '  ],\n'
        '  "risks": [\n'
        '    {"level":"High|Medium|Low","risk":"risk in plain English","area":"Operational|Legal|Financial|Technical","mitigation":"specific mitigation action"},\n'
        '    {"level":"High|Medium|Low","risk":"risk 2","area":"area","mitigation":"mitigation"},\n'
        '    {"level":"High|Medium|Low","risk":"risk 3","area":"area","mitigation":"mitigation"},\n'
        '    {"level":"High|Medium|Low","risk":"risk 4","area":"area","mitigation":"mitigation"},\n'
        '    {"level":"High|Medium|Low","risk":"risk 5","area":"area","mitigation":"mitigation"}\n'
        '  ],\n'
        '  "timeline": [\n'
        '    {"date":"Mon YYYY","event":"milestone","detail":"what must be done by this date"},\n'
        '    {"date":"Mon YYYY","event":"milestone","detail":"detail"},\n'
        '    {"date":"Mon YYYY","event":"milestone","detail":"detail"},\n'
        '    {"date":"Mon YYYY","event":"milestone","detail":"detail"},\n'
        '    {"date":"Mon YYYY","event":"milestone","detail":"detail"}\n'
        '  ]\n'
        "}"
    )
    raw   = call_groq(prompt, api_key)
    clean = raw.replace("```json","").replace("```","").strip()
    return json.loads(clean)

def ask_question(q: str, analysis: dict, policy_text: str, api_key: str) -> str:
    return call_groq(
        f"You analyzed this healthcare policy for a private marketplace like eHealth: {json.dumps(analysis)}. "
        f"Policy excerpt: \"{policy_text[:2000]}\". "
        f"Answer in plain English — no jargon — for a PM, engineer, or compliance person: {q}",
        api_key
    )

def badge(label, level=None):
    cls = {"High":"badge-high","Medium":"badge-medium","Low":"badge-low"}.get(level or label,"badge-neutral")
    return f'<span class="badge {cls}">{label}</span>'

def team_bullets(items, dot_color):
    if not items:
        return '<div class="team-text" style="color:#94a3b8;font-size:12px">No items</div>'
    return "".join(
        f'<div class="team-bullet"><div class="team-dot" style="background:{dot_color}"></div>'
        f'<div class="team-text">{item}</div></div>'
        for item in items
    )

def rec_block(items, dot_color):
    if not items:
        return ""
    html = ""
    for r in items:
        lvl = r.get("priority","Low")
        badge_cls = {"High":"badge-high","Medium":"badge-medium","Low":"badge-low"}.get(lvl,"badge-neutral")
        html += (
            f'<div class="rec-item">'
            f'<div class="rec-left"><span class="badge {badge_cls}" style="font-size:11px">{lvl}</span></div>'
            f'<div class="rec-right">'
            f'<div class="rec-action">{r.get("action","")}</div>'
            f'<div class="rec-detail">{r.get("detail","")}</div>'
            f'<div class="rec-meta">⏱ {r.get("timeline","")}</div>'
            f'</div></div>'
        )
    return html

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚕ PolicyAI")
    st.markdown("**Private Marketplace Edition**")
    st.divider()
    api_key = st.text_input("API Key", type="password", placeholder="gsk_...")
    st.divider()
    st.markdown("**⚡ Quick Load**")
    for name in PRESETS:
        if st.button(name, key=f"p_{name}"):
            st.session_state["policy_text"]   = PRESETS[name]
            st.session_state["analysis"]      = None
            st.session_state["analysis_text"] = ""
            st.session_state["uploaded_name"] = ""
            st.rerun()
    st.divider()
    st.caption("PDF · DOCX · TXT supported")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## ⚕ PolicyAI — Healthcare Policy Analyzer")
st.markdown("For **Product Managers, Engineers, Platform & Compliance Teams** — upload any ACA / CMS document and get a full structured brief by team.")

# ── Input ─────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("📎 Upload PDF, DOCX, or TXT", type=["pdf","docx","txt"])
if uploaded and uploaded.name != st.session_state.get("uploaded_name",""):
    with st.spinner("Reading document..."):
        extracted, err = extract_text(uploaded)
    if err:
        st.error(err)
    else:
        st.session_state["policy_text"]   = extracted
        st.session_state["uploaded_name"] = uploaded.name
        st.session_state["analysis"]      = None
        st.success(f"✅ **{uploaded.name}** — {len(extracted):,} characters extracted")

policy_text = st.text_area(
    "Or paste / type policy text:",
    value=st.session_state["policy_text"],
    height=100,
    placeholder="Paste any ACA, CMS, Medicaid rule text — or pick a preset from the sidebar…"
)
if policy_text != st.session_state["policy_text"]:
    st.session_state["policy_text"] = policy_text

c1, c2, _ = st.columns([1.2, 1, 5])
with c1:
    go = st.button("⚡ Analyze Policy", type="primary", use_container_width=True)
with c2:
    clear = st.button("🗑 Clear", use_container_width=True)

if clear:
    st.session_state["policy_text"]   = ""
    st.session_state["analysis"]      = None
    st.session_state["analysis_text"] = ""
    st.session_state["uploaded_name"] = ""
    st.rerun()

if go:
    txt = st.session_state["policy_text"].strip()
    if not txt:
        st.error("Paste policy text, upload a file, or pick a preset from the sidebar.")
    elif not api_key:
        st.error("Enter your API key in the sidebar.")
    else:
        prog = st.progress(0, text="Reading policy…")
        try:
            prog.progress(10, text="Parsing regulatory sections…")
            result = analyze_policy(txt, api_key)
            prog.progress(85, text="Building brief…")
            st.session_state["analysis"]      = result
            st.session_state["analysis_text"] = txt
            prog.progress(100, text="Done!")
            prog.empty()
            st.success("✅ Analysis complete — see results below.")
        except json.JSONDecodeError:
            prog.empty()
            st.error("AI returned unexpected format — please try again.")
        except Exception as e:
            prog.empty()
            st.error(f"Failed: {e}")

# ── RESULTS ───────────────────────────────────────────────────────────────────
D = st.session_state.get("analysis")
if D:
    st.markdown("---")

    # Hero
    st.markdown(f"""
    <div class="policy-hero">
        <h2>{D.get('policyName','Policy Analysis')}</h2>
        <p>{D.get('ruleSummary','')}</p>
    </div>""", unsafe_allow_html=True)

    # Metrics
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Policy Type</div>
            <div class="metric-val">{badge(D.get('policyType','—'))}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Effective Date</div>
            <div class="metric-val" style="font-size:14px">{D.get('effectiveDate','—')}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Regulatory Impact</div>
            <div class="metric-val">{badge(D.get('regulatoryImpact','—'), D.get('regulatoryImpact'))}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Compliance Complexity</div>
            <div class="metric-val">{badge(D.get('complianceComplexity','—'), D.get('complianceComplexity'))}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "📋 Summary & All Sections",
        "🏢 Team Impacts",
        "💡 Recommendations",
        "⚠️ Risks",
        "📅 Timeline",
        "💬 Q&A",
        "📤 Export"
    ])

    # ── TAB 1: SUMMARY ────────────────────────────────────────────────────────
    with t1:
        # Executive summary
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="sec-divider">What is this rule — plain English</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rule-plain">{D.get("ruleSummary","")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-divider" style="margin-top:16px">Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="exec-summary">{D.get("executiveSummary","")}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # All policy sections
        sections = D.get("policySections", [])
        if sections:
            st.markdown('<div class="white-card">', unsafe_allow_html=True)
            st.markdown('<div class="sec-divider">All Rule Sections & Changes</div>', unsafe_allow_html=True)
            for sec in sections:
                changes_html = "".join(
                    f'<div class="policy-change">'
                    f'<div class="policy-change-dot"></div>'
                    f'<div class="policy-change-text">{c}</div>'
                    f'</div>'
                    for c in sec.get("changes", [])
                )
                ref = sec.get("ruleReference","")
                ref_html = f'<span class="policy-section-rule">{ref}</span>' if ref else ""
                st.markdown(
                    f'<div class="policy-section">'
                    f'<div class="policy-section-title">📌 {sec.get("sectionName","")}</div>'
                    f'{ref_html}'
                    f'{changes_html}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # Key findings
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="sec-divider">Key Findings — Overall Changes at a Glance</div>', unsafe_allow_html=True)
        for i, f in enumerate(D.get("keyFindings",[])):
            st.markdown(
                f'<div class="finding-row">'
                f'<div class="finding-num">{i+1}</div>'
                f'<div class="finding-text">{f}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 2: TEAM IMPACTS ───────────────────────────────────────────────────
    with t2:
        st.markdown("#### What changes for each team — find your team and read your section")
        st.markdown("")

        # Row 1
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-benefits">🎁 Benefits Platform</div>'
                f'<div class="team-card-body">{team_bullets(D.get("benefitsPlatformImpact",[]),"#4f46e5")}</div></div>',
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-marketplace">🛒 Marketplace / Enrollment</div>'
                f'<div class="team-card-body">{team_bullets(D.get("marketplaceImpact",[]),"#059669")}</div></div>',
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-ecommerce">🛍 eCommerce / Shopping</div>'
                f'<div class="team-card-body">{team_bullets(D.get("ecommerceImpact",[]),"#ea580c")}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("")

        # Row 2
        c4, c5, c6 = st.columns(3)
        with c4:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-engineering">⚙️ Engineering</div>'
                f'<div class="team-card-body">{team_bullets(D.get("engineeringImpact",[]),"#0891b2")}</div></div>',
                unsafe_allow_html=True
            )
        with c5:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-platform">🖥 Platform Team</div>'
                f'<div class="team-card-body">{team_bullets(D.get("platformTeamImpact",[]),"#7c3aed")}</div></div>',
                unsafe_allow_html=True
            )
        with c6:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-consumer">👤 Consumers / Members</div>'
                f'<div class="team-card-body">{team_bullets(D.get("consumerImpact",[]),"#d97706")}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("")

        # Row 3
        c7, c8, _ = st.columns(3)
        with c7:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-payer">🛡 Payers / Carriers</div>'
                f'<div class="team-card-body">{team_bullets(D.get("payerImpact",[]),"#0f766e")}</div></div>',
                unsafe_allow_html=True
            )
        with c8:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-provider">🏥 Providers</div>'
                f'<div class="team-card-body">{team_bullets(D.get("providerImpact",[]),"#dc2626")}</div></div>',
                unsafe_allow_html=True
            )

    # ── TAB 3: RECOMMENDATIONS ────────────────────────────────────────────────
    with t3:
        st.markdown("#### What your company should do — specific actions per role, plain English")
        st.markdown("Each item references the actual rule provision. Priority and timeline included.")
        st.markdown("")

        # PM
        st.markdown(
            f'<div class="rec-card"><div class="rec-card-header rc-pm">📌 Product Manager Recommendations</div>'
            f'<div class="rec-card-body">{rec_block(D.get("pmRecommendations",[]),"#6366f1")}</div></div>',
            unsafe_allow_html=True
        )

        # Engineering
        st.markdown(
            f'<div class="rec-card"><div class="rec-card-header rc-eng">⚙️ Engineering Recommendations</div>'
            f'<div class="rec-card-body">{rec_block(D.get("engineeringRecommendations",[]),"#0891b2")}</div></div>',
            unsafe_allow_html=True
        )

        # Platform
        st.markdown(
            f'<div class="rec-card"><div class="rec-card-header rc-platform">🖥 Platform Team Recommendations</div>'
            f'<div class="rec-card-body">{rec_block(D.get("platformRecommendations",[]),"#7c3aed")}</div></div>',
            unsafe_allow_html=True
        )

        # Compliance
        st.markdown(
            f'<div class="rec-card"><div class="rec-card-header rc-compliance">📋 Compliance Recommendations</div>'
            f'<div class="rec-card-body">{rec_block(D.get("complianceRecommendations",[]),"#059669")}</div></div>',
            unsafe_allow_html=True
        )

    # ── TAB 4: RISKS ──────────────────────────────────────────────────────────
    with t4:
        st.markdown("#### Compliance risk register — what could go wrong and how to prevent it")
        st.markdown("")
        st.markdown("""
        <div class="risk-header">
            <span class="risk-col-lbl">Level</span>
            <span class="risk-col-lbl">Risk</span>
            <span class="risk-col-lbl">Area</span>
            <span class="risk-col-lbl">How to fix it</span>
        </div>""", unsafe_allow_html=True)
        for r in D.get("risks",[]):
            st.markdown(f"""
            <div class="risk-row-item">
                <div>{badge(r.get('level','Low'), r.get('level'))}</div>
                <div class="risk-cell">{r.get('risk','')}</div>
                <div class="risk-area-cell">{r.get('area','')}</div>
                <div class="risk-mit-cell">{r.get('mitigation','')}</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 5: TIMELINE ───────────────────────────────────────────────────────
    with t5:
        st.markdown("#### Key dates — deadlines your team must hit")
        st.markdown("")
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        for item in D.get("timeline",[]):
            st.markdown(f"""
            <div class="tl-row">
                <div class="tl-date">{item.get('date','')}</div>
                <div class="tl-info">
                    <h4>{item.get('event','')}</h4>
                    <p>{item.get('detail','')}</p>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 6: Q&A ────────────────────────────────────────────────────────────
    with t6:
        st.markdown("#### Ask anything about this policy — plain English answers")
        st.markdown("*Try: 'What does this mean for our plan shopping page?' · 'What does engineering need to build?' · 'What is the State EDE model?'*")
        st.markdown("")
        q = st.text_input("Your question", placeholder="e.g. What does the State EDE provision mean for our marketplace?")
        if st.button("Ask", type="primary") and q:
            if not api_key:
                st.error("Enter API key in sidebar.")
            else:
                with st.spinner("Thinking..."):
                    ans = ask_question(q, D, st.session_state.get("analysis_text",""), api_key)
                st.markdown(f'<div class="qa-user">{q}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="qa-ai">{ans}</div>', unsafe_allow_html=True)

    # ── TAB 7: EXPORT ─────────────────────────────────────────────────────────
    with t7:
        st.markdown("#### Download your analysis")
        st.markdown("")

        nl = "\n"

        def fmt_list(items):
            return nl.join(f"  • {x}" for x in items) if items else "  None"

        def fmt_recs(items):
            return nl.join(
                f"  {i+1}. [{r.get('priority','')}] {r.get('action','')} ({r.get('timeline','')})\n     {r.get('detail','')}"
                for i,r in enumerate(items)
            ) if items else "  None"

        def fmt_sections(sections):
            out = ""
            for s in sections:
                out += f"\n  {s.get('sectionName','')}"
                if s.get('ruleReference'):
                    out += f" [{s['ruleReference']}]"
                out += "\n"
                for c in s.get("changes",[]):
                    out += f"    - {c}\n"
            return out

        memo = (
            "=" * 65 + "\n"
            "HEALTHCARE POLICY ANALYSIS BRIEF\n"
            "=" * 65 + "\n\n"
            f"Policy:     {D.get('policyName','')}\n"
            f"Effective:  {D.get('effectiveDate','')}\n"
            f"Type:       {D.get('policyType','')} | Impact: {D.get('regulatoryImpact','')} | Complexity: {D.get('complianceComplexity','')}\n\n"
            + "-"*65 + "\nWHAT IS THIS RULE (PLAIN ENGLISH)\n" + "-"*65 + "\n"
            + D.get('ruleSummary','') + "\n\n"
            + "-"*65 + "\nEXECUTIVE SUMMARY\n" + "-"*65 + "\n"
            + D.get('executiveSummary','') + "\n\n"
            + "-"*65 + "\nALL RULE SECTIONS\n" + "-"*65
            + fmt_sections(D.get('policySections',[])) + "\n"
            + "-"*65 + "\nKEY FINDINGS\n" + "-"*65 + "\n"
            + nl.join(f"{i+1}. {f}" for i,f in enumerate(D.get('keyFindings',[]))) + "\n\n"
            + "-"*65 + "\nTEAM IMPACTS\n" + "-"*65 + "\n"
            + "BENEFITS PLATFORM\n" + fmt_list(D.get('benefitsPlatformImpact',[])) + "\n\n"
            + "MARKETPLACE / ENROLLMENT\n" + fmt_list(D.get('marketplaceImpact',[])) + "\n\n"
            + "ECOMMERCE / SHOPPING\n" + fmt_list(D.get('ecommerceImpact',[])) + "\n\n"
            + "ENGINEERING\n" + fmt_list(D.get('engineeringImpact',[])) + "\n\n"
            + "PLATFORM TEAM\n" + fmt_list(D.get('platformTeamImpact',[])) + "\n\n"
            + "CONSUMERS / MEMBERS\n" + fmt_list(D.get('consumerImpact',[])) + "\n\n"
            + "PAYERS / CARRIERS\n" + fmt_list(D.get('payerImpact',[])) + "\n\n"
            + "PROVIDERS\n" + fmt_list(D.get('providerImpact',[])) + "\n\n"
            + "-"*65 + "\nRECOMMENDATIONS\n" + "-"*65 + "\n"
            + "PRODUCT MANAGER\n" + fmt_recs(D.get('pmRecommendations',[])) + "\n\n"
            + "ENGINEERING\n" + fmt_recs(D.get('engineeringRecommendations',[])) + "\n\n"
            + "PLATFORM TEAM\n" + fmt_recs(D.get('platformRecommendations',[])) + "\n\n"
            + "COMPLIANCE\n" + fmt_recs(D.get('complianceRecommendations',[])) + "\n\n"
            + "-"*65 + "\nRISK REGISTER\n" + "-"*65 + "\n"
            + nl.join(f"  [{r.get('level','')}] {r.get('risk','')} ({r.get('area','')})\n     Fix: {r.get('mitigation','')}" for r in D.get('risks',[])) + "\n\n"
            + "-"*65 + "\nKEY DATES\n" + "-"*65 + "\n"
            + nl.join(f"  {t.get('date','')}: {t.get('event','')} — {t.get('detail','')}" for t in D.get('timeline',[])) + "\n\n"
            + "=" * 65 + "\n"
            "Generated by PolicyAI\n"
        )

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📄 Download Full Brief (.txt)",
                memo,
                file_name=f"{D.get('policyName','policy').replace(' ','-')[:40]}-brief.txt",
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
