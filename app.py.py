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

# ── Session state init ────────────────────────────────────────────────────────
for k, v in [("policy_text",""),("analysis",None),("analysis_text",""),("uploaded_name","")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif !important;}
.stApp{background:#f0f2f6 !important;}
.main .block-container{background:#f0f2f6 !important;padding:1.5rem 2rem 4rem 2rem !important;max-width:1200px;}
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

.policy-hero{background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);border-radius:14px;padding:24px 28px;margin-bottom:20px;}
.policy-hero h2{font-size:22px;font-weight:700;color:#ffffff !important;margin:0 0 8px 0;}
.policy-hero p{font-size:14px;color:#94a3b8 !important;margin:0;line-height:1.6;}

.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;}
.metric-card{background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;}
.metric-label{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;}
.metric-val{font-size:16px;font-weight:700;color:#0f172a;}

.white-card{background:#ffffff;border-radius:12px;border:1px solid #e2e8f0;padding:20px 24px;margin-bottom:16px;}
.sec-divider{font-size:11px;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #e0e7ff;}

.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}
.badge-high{background:#fee2e2;color:#b91c1c;}
.badge-medium{background:#fef3c7;color:#92400e;}
.badge-low{background:#dcfce7;color:#166534;}
.badge-neutral{background:#e0e7ff;color:#3730a3;}

.exec-summary{font-size:15px;color:#1e293b;line-height:1.75;background:#f8fafc;padding:16px 20px;border-radius:10px;border-left:4px solid #6366f1;margin-bottom:16px;}
.rule-plain{font-size:15px;color:#1e293b;line-height:1.75;background:#eff6ff;padding:16px 20px;border-radius:10px;border-left:4px solid #3b82f6;margin-bottom:16px;}

.finding-row{display:flex;gap:14px;align-items:flex-start;padding:14px;background:#f8fafc;border-radius:10px;margin-bottom:10px;}
.finding-num{background:#6366f1;color:white;font-size:12px;font-weight:700;min-width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.finding-text{font-size:14px;color:#1e293b;line-height:1.65;}

.team-card{background:#fff;border-radius:12px;border:1px solid #e2e8f0;overflow:hidden;margin-bottom:4px;}
.team-card-header{padding:12px 16px;font-size:13px;font-weight:700;color:#fff !important;}
.tc-benefits{background:#4f46e5;}
.tc-marketplace{background:#059669;}
.tc-engineering{background:#0891b2;}
.tc-ecommerce{background:#ea580c;}
.tc-consumer{background:#d97706;}
.tc-payer{background:#7c3aed;}
.tc-provider{background:#dc2626;}
.team-card-body{padding:14px 16px;}
.team-bullet{display:flex;gap:10px;margin-bottom:10px;align-items:flex-start;}
.team-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;margin-top:6px;}
.team-text{font-size:13px;color:#334155;line-height:1.55;}

.rec-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px;}
.rec-card{background:#fff;border-radius:12px;border:1px solid #e2e8f0;overflow:hidden;}
.rec-card-header{padding:14px 18px;font-size:14px;font-weight:700;color:#fff !important;}
.rc-pm{background:#6366f1;}
.rc-eng{background:#0891b2;}
.rc-compliance{background:#059669;}
.rec-card-body{padding:16px 18px;}
.rec-item{display:flex;gap:10px;margin-bottom:12px;align-items:flex-start;padding-bottom:12px;border-bottom:1px solid #f1f5f9;}
.rec-item:last-child{border:none;margin-bottom:0;padding-bottom:0;}
.rec-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:5px;}
.rec-text{font-size:13px;color:#1e293b;line-height:1.55;}
.rec-text strong{color:#0f172a;font-weight:600;display:block;margin-bottom:2px;}

.action-card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px 20px;margin-bottom:12px;}
.action-top{display:flex;align-items:center;gap:10px;margin-bottom:8px;}
.action-title{font-size:15px;font-weight:600;color:#0f172a;}
.action-owner{font-size:12px;color:#64748b;margin-bottom:8px;}
.action-detail{font-size:13px;color:#475569;line-height:1.6;background:#f8fafc;border-radius:8px;padding:10px 14px;}

.risk-header{display:grid;grid-template-columns:90px 2fr 120px 2fr;gap:12px;padding:6px 14px;}
.risk-row-item{display:grid;grid-template-columns:90px 2fr 120px 2fr;gap:12px;padding:12px 14px;background:#f8fafc;border-radius:8px;margin-bottom:8px;align-items:start;}
.risk-col-lbl{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#94a3b8;}
.risk-cell{font-size:13px;color:#1e293b;line-height:1.5;}
.risk-area-cell{font-size:12px;color:#64748b;font-weight:500;}
.risk-mit-cell{font-size:12px;color:#475569;line-height:1.5;}

.tl-row{display:flex;gap:18px;padding:14px 0;border-bottom:1px solid #f1f5f9;align-items:flex-start;}
.tl-row:last-child{border:none;}
.tl-date{background:#0f172a;color:#fff;font-size:11px;font-weight:700;padding:5px 12px;border-radius:6px;white-space:nowrap;flex-shrink:0;}
.tl-info h4{font-size:14px;font-weight:600;color:#0f172a;margin:0 0 4px 0;}
.tl-info p{font-size:13px;color:#64748b;margin:0;line-height:1.5;}

.qa-user{background:#6366f1;color:#fff;padding:12px 16px;border-radius:12px 12px 2px 12px;font-size:13px;margin-bottom:8px;max-width:78%;margin-left:auto;line-height:1.5;}
.qa-ai{background:#f0fdf4;color:#1e293b;border:1px solid #bbf7d0;padding:12px 16px;border-radius:2px 12px 12px 12px;font-size:13px;margin-bottom:8px;line-height:1.6;}
</style>
""", unsafe_allow_html=True)

# ── Presets ───────────────────────────────────────────────────────────────────
PRESETS = {
    "ACA 2026 Payment Notice":    "ACA 2026 Notice of Benefit and Payment Parameters — Marketplace payment notice covering risk adjustment updates, premium rate review, cost sharing limits, plan certification, and enrollee protections for plan year 2026.",
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
            "max_tokens": 3000
        },
        timeout=60
    )
    if not res.ok:
        raise Exception(f"API error {res.status_code}: {res.text[:200]}")
    return res.json()["choices"][0]["message"]["content"]

def analyze_policy(text: str, api_key: str) -> dict:
    prompt = (
        "You are a senior healthcare regulatory analyst for a private health insurance marketplace company like eHealth, Covered California, or HealthSherpa. "
        "Analyze this policy and return ONLY raw JSON — no markdown fences, no preamble, nothing else.\n\n"
        f"Policy:\n\"\"\"\n{text[:12000]}\n\"\"\"\n\n"
        "Return ONLY this exact JSON with no other text:\n"
        "{\n"
        '  "policyName": "short official name",\n'
        '  "effectiveDate": "date or TBD",\n'
        '  "policyType": "ACA|Medicaid|Medicare|Other",\n'
        '  "regulatoryImpact": "High|Medium|Low",\n'
        '  "complianceComplexity": "High|Medium|Low",\n'
        '  "ruleSummary": "What is this rule saying in plain English — 3 sentences max, no legal jargon, anyone can understand it",\n'
        '  "executiveSummary": "What changed, why it matters, what the company must do — 3 sentences for executives",\n'
        '  "keyFindings": ["finding 1","finding 2","finding 3","finding 4"],\n'
        '  "benefitsPlatformImpact": ["specific change to benefits design or coverage rules","impact 2","impact 3"],\n'
        '  "marketplaceImpact": ["specific change to marketplace like eHealth or Covered California enrollment","impact 2","impact 3"],\n'
        '  "ecommerceImpact": ["change to plan shopping, cart, checkout, or pricing display","change 2","change 3"],\n'
        '  "engineeringImpact": ["specific system or data change required","change 2","change 3"],\n'
        '  "consumerImpact": ["what changes for end users or employees","impact 2","impact 3"],\n'
        '  "payerImpact": ["what changes for insurance carriers","impact 2","impact 3"],\n'
        '  "providerImpact": ["what changes for healthcare providers","impact 2","impact 3"],\n'
        '  "pmRecommendations": [\n'
        '    {"action": "what to do", "detail": "plain English explanation of why and how", "priority": "High|Medium|Low", "timeline": "when"},\n'
        '    {"action": "what to do", "detail": "plain English explanation of why and how", "priority": "High|Medium|Low", "timeline": "when"},\n'
        '    {"action": "what to do", "detail": "plain English explanation of why and how", "priority": "High|Medium|Low", "timeline": "when"}\n'
        '  ],\n'
        '  "engineeringRecommendations": [\n'
        '    {"action": "what to build or change", "detail": "technical plain English description", "priority": "High|Medium|Low", "timeline": "when"},\n'
        '    {"action": "what to build or change", "detail": "technical plain English description", "priority": "High|Medium|Low", "timeline": "when"},\n'
        '    {"action": "what to build or change", "detail": "technical plain English description", "priority": "High|Medium|Low", "timeline": "when"}\n'
        '  ],\n'
        '  "complianceRecommendations": [\n'
        '    {"action": "what to file or certify", "detail": "plain English description", "priority": "High|Medium|Low", "timeline": "when"},\n'
        '    {"action": "what to file or certify", "detail": "plain English description", "priority": "High|Medium|Low", "timeline": "when"},\n'
        '    {"action": "what to file or certify", "detail": "plain English description", "priority": "High|Medium|Low", "timeline": "when"}\n'
        '  ],\n'
        '  "risks": [\n'
        '    {"level":"High|Medium|Low","risk":"risk in plain English","area":"Operational|Legal|Financial|Technical","mitigation":"how to fix it"},\n'
        '    {"level":"High|Medium|Low","risk":"risk in plain English","area":"Operational|Legal|Financial|Technical","mitigation":"how to fix it"},\n'
        '    {"level":"High|Medium|Low","risk":"risk in plain English","area":"Operational|Legal|Financial|Technical","mitigation":"how to fix it"}\n'
        '  ],\n'
        '  "timeline": [\n'
        '    {"date":"Mon YYYY","event":"milestone name","detail":"what needs to happen by this date"},\n'
        '    {"date":"Mon YYYY","event":"milestone name","detail":"what needs to happen by this date"},\n'
        '    {"date":"Mon YYYY","event":"milestone name","detail":"what needs to happen by this date"}\n'
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
        f"Answer in plain English for a PM or engineer — no legal jargon: {q}",
        api_key
    )

def badge(label, level=None):
    cls = {"High":"badge-high","Medium":"badge-medium","Low":"badge-low"}.get(level or label,"badge-neutral")
    return f'<span class="badge {cls}">{label}</span>'

def team_bullets(items, dot_color):
    html = ""
    for item in items:
        html += f'<div class="team-bullet"><div class="team-dot" style="background:{dot_color}"></div><div class="team-text">{item}</div></div>'
    return html

def rec_items(items, dot_color):
    html = ""
    for item in items:
        html += (
            f'<div class="rec-item">'
            f'<div class="rec-dot" style="background:{dot_color}"></div>'
            f'<div class="rec-text"><strong>{item["action"]}</strong>{item["detail"]}'
            f' <span style="font-size:11px;background:#f1f5f9;padding:2px 8px;border-radius:10px;color:#64748b;margin-left:6px">{item.get("priority","")} · {item.get("timeline","")}</span>'
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
            st.session_state["policy_text"] = PRESETS[name]
            st.session_state["analysis"]    = None
            st.session_state["analysis_text"] = ""
            st.rerun()
    st.divider()
    st.caption("PDF · DOCX · TXT supported\nStreamlit Cloud · Free hosting")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## ⚕ PolicyAI — Healthcare Policy Analyzer")
st.markdown("For **Product Managers, Engineers & Compliance Teams** — upload any ACA / CMS / Medicaid PDF and get a clear brief broken down by team.")

# ── Input ─────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "📎 Upload PDF, DOCX, or TXT",
    type=["pdf","docx","txt"],
    key="file_uploader"
)

if uploaded and uploaded.name != st.session_state.get("uploaded_name",""):
    with st.spinner("Reading document..."):
        extracted, err = extract_text(uploaded)
    if err:
        st.error(err)
    else:
        st.session_state["policy_text"]  = extracted
        st.session_state["uploaded_name"] = uploaded.name
        st.session_state["analysis"]     = None
        st.success(f"✅ **{uploaded.name}** — {len(extracted):,} characters extracted")

policy_text = st.text_area(
    "Or paste / type policy text:",
    value=st.session_state["policy_text"],
    height=100,
    placeholder="e.g. 'ACA 2026 Notice of Benefit and Payment Parameters' or paste the full rule text…",
    key="text_input"
)
if policy_text != st.session_state["policy_text"]:
    st.session_state["policy_text"] = policy_text

# ── Buttons ───────────────────────────────────────────────────────────────────
c1, c2, _ = st.columns([1.2, 1, 5])
with c1:
    go = st.button("⚡ Analyze Policy", type="primary", use_container_width=True)
with c2:
    clear = st.button("🗑 Clear", use_container_width=True)

# ── CLEAR — wipes everything ──────────────────────────────────────────────────
if clear:
    st.session_state["policy_text"]   = ""
    st.session_state["analysis"]      = None
    st.session_state["analysis_text"] = ""
    st.session_state["uploaded_name"] = ""
    st.rerun()

# ── ANALYZE ───────────────────────────────────────────────────────────────────
if go:
    txt = st.session_state["policy_text"].strip()
    if not txt:
        st.error("Please paste policy text, upload a file, or pick a preset from the sidebar.")
    elif not api_key:
        st.error("Please enter your API key in the sidebar.")
    else:
        prog = st.progress(0, text="Parsing regulatory text…")
        try:
            prog.progress(15, text="Reading policy…")
            result = analyze_policy(txt, api_key)
            prog.progress(85, text="Structuring brief…")
            st.session_state["analysis"]      = result
            st.session_state["analysis_text"] = txt
            prog.progress(100, text="Done!")
            prog.empty()
            st.success("✅ Analysis complete — scroll down to read.")
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

    # Policy hero
    st.markdown(f"""
    <div class="policy-hero">
        <h2>{D.get('policyName','Policy Analysis')}</h2>
        <p>{D.get('ruleSummary','')}</p>
    </div>""", unsafe_allow_html=True)

    # Metric row
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

    # Tabs
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "📋 Summary",
        "🏢 Team Impacts",
        "💡 Recommendations",
        "✅ Action Plan",
        "⚠️ Risks",
        "📅 Timeline",
        "💬 Q&A"
    ])

    # ── TAB 1: SUMMARY ────────────────────────────────────────────────────────
    with t1:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="sec-divider">What is this rule saying — plain English</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rule-plain">{D.get("ruleSummary","")}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="sec-divider">Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="exec-summary">{D.get("executiveSummary","")}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.markdown('<div class="sec-divider">Key Findings</div>', unsafe_allow_html=True)
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
        st.markdown("#### What changes for each team — read your section")
        st.markdown("")

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
        c4, c5, c6 = st.columns(3)
        with c4:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-engineering">⚙️ Engineering / Platform</div>'
                f'<div class="team-card-body">{team_bullets(D.get("engineeringImpact",[]),"#0891b2")}</div></div>',
                unsafe_allow_html=True
            )
        with c5:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-consumer">👤 Consumers / Members</div>'
                f'<div class="team-card-body">{team_bullets(D.get("consumerImpact",[]),"#d97706")}</div></div>',
                unsafe_allow_html=True
            )
        with c6:
            st.markdown(
                f'<div class="team-card"><div class="team-card-header tc-payer">🛡 Payers / Carriers</div>'
                f'<div class="team-card-body">{team_bullets(D.get("payerImpact",[]),"#7c3aed")}</div></div>',
                unsafe_allow_html=True
            )

    # ── TAB 3: RECOMMENDATIONS ────────────────────────────────────────────────
    with t3:
        st.markdown("#### What should your company do — broken down by role")
        st.markdown("Written in plain English. No legal jargon. Each person knows exactly what to do.")
        st.markdown("")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="rec-card"><div class="rec-card-header rc-pm">📌 Product Manager</div>'
                f'<div class="rec-card-body">{rec_items(D.get("pmRecommendations",[]),"#6366f1")}</div></div>',
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f'<div class="rec-card"><div class="rec-card-header rc-eng">⚙️ Engineering</div>'
                f'<div class="rec-card-body">{rec_items(D.get("engineeringRecommendations",[]),"#0891b2")}</div></div>',
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                f'<div class="rec-card"><div class="rec-card-header rc-compliance">📋 Compliance</div>'
                f'<div class="rec-card-body">{rec_items(D.get("complianceRecommendations",[]),"#059669")}</div></div>',
                unsafe_allow_html=True
            )

    # ── TAB 4: ACTION PLAN ────────────────────────────────────────────────────
    with t4:
        st.markdown("#### Prioritized actions — who does what and by when")
        st.markdown("")
        for a in D.get("actions", D.get("pmRecommendations",[])):
            lvl = a.get("priority","Low")
            st.markdown(f"""
            <div class="action-card">
                <div class="action-top">
                    {badge(lvl, lvl)}
                    <span class="action-title">{a.get('title', a.get('action',''))}</span>
                </div>
                <div class="action-owner">👤 <strong>Owner:</strong> {a.get('owner','Team')} &nbsp;|&nbsp; 📅 <strong>Due:</strong> {a.get('dueDate', a.get('timeline',''))}</div>
                <div class="action-detail">{a.get('detail','')}</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 5: RISKS ──────────────────────────────────────────────────────────
    with t5:
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

    # ── TAB 6: TIMELINE ───────────────────────────────────────────────────────
    with t6:
        st.markdown("#### Key dates — deadlines your team needs to hit")
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

    # ── TAB 7: Q&A ────────────────────────────────────────────────────────────
    with t7:
        st.markdown("#### Ask anything — plain English answers")
        st.markdown("*Try: 'What does this mean for our plan shopping page?' or 'What does engineering need to build?'*")
        st.markdown("")
        q = st.text_input("Your question", placeholder="What does this mean for our enrollment flow?")
        if st.button("Ask", type="primary") and q:
            if not api_key:
                st.error("Enter your API key in the sidebar.")
            else:
                with st.spinner("Thinking..."):
                    ans = ask_question(q, D, st.session_state.get("analysis_text",""), api_key)
                st.markdown(f'<div class="qa-user">{q}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="qa-ai">{ans}</div>', unsafe_allow_html=True)

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown("---")
    nl = "\n"

    def fmt_list(items, key=""):
        return nl.join(f"  - {x.get(key,x) if isinstance(x,dict) else x}" for x in items)

    def fmt_recs(items):
        return nl.join(
            f"  {i+1}. [{r.get('priority','')}] {r.get('action','')} ({r.get('timeline','')})\n     {r.get('detail','')}"
            for i,r in enumerate(items)
        )

    memo = (
        "=" * 60 + "\n"
        "HEALTHCARE POLICY ANALYSIS BRIEF\n"
        "=" * 60 + "\n\n"
        f"Policy:     {D.get('policyName','')}\n"
        f"Effective:  {D.get('effectiveDate','')}\n"
        f"Type:       {D.get('policyType','')} | Impact: {D.get('regulatoryImpact','')} | Complexity: {D.get('complianceComplexity','')}\n\n"
        + "-"*60 + "\nWHAT IS THIS RULE (PLAIN ENGLISH)\n" + "-"*60 + "\n"
        + D.get('ruleSummary','') + "\n\n"
        + "-"*60 + "\nEXECUTIVE SUMMARY\n" + "-"*60 + "\n"
        + D.get('executiveSummary','') + "\n\n"
        + "-"*60 + "\nKEY FINDINGS\n" + "-"*60 + "\n"
        + nl.join(f"{i+1}. {f}" for i,f in enumerate(D.get('keyFindings',[]))) + "\n\n"
        + "-"*60 + "\nTEAM IMPACTS\n" + "-"*60 + "\n"
        + "BENEFITS PLATFORM\n" + fmt_list(D.get('benefitsPlatformImpact',[])) + "\n\n"
        + "MARKETPLACE / ENROLLMENT\n" + fmt_list(D.get('marketplaceImpact',[])) + "\n\n"
        + "ECOMMERCE / SHOPPING\n" + fmt_list(D.get('ecommerceImpact',[])) + "\n\n"
        + "ENGINEERING / PLATFORM\n" + fmt_list(D.get('engineeringImpact',[])) + "\n\n"
        + "CONSUMERS / MEMBERS\n" + fmt_list(D.get('consumerImpact',[])) + "\n\n"
        + "PAYERS / CARRIERS\n" + fmt_list(D.get('payerImpact',[])) + "\n\n"
        + "-"*60 + "\nRECOMMENDATIONS\n" + "-"*60 + "\n"
        + "PRODUCT MANAGER\n" + fmt_recs(D.get('pmRecommendations',[])) + "\n\n"
        + "ENGINEERING\n" + fmt_recs(D.get('engineeringRecommendations',[])) + "\n\n"
        + "COMPLIANCE\n" + fmt_recs(D.get('complianceRecommendations',[])) + "\n\n"
        + "-"*60 + "\nRISK REGISTER\n" + "-"*60 + "\n"
        + nl.join(f"  [{r.get('level','')}] {r.get('risk','')} ({r.get('area','')})\n     Fix: {r.get('mitigation','')}" for r in D.get('risks',[])) + "\n\n"
        + "-"*60 + "\nKEY DATES\n" + "-"*60 + "\n"
        + nl.join(f"  {t.get('date','')}: {t.get('event','')} — {t.get('detail','')}" for t in D.get('timeline',[])) + "\n\n"
        + "=" * 60 + "\n"
        "Generated by PolicyAI\n"
    )

    ce1, ce2 = st.columns(2)
    with ce1:
        st.download_button(
            "📄 Download Full Brief (.txt)",
            memo,
            file_name=f"{D.get('policyName','policy').replace(' ','-')}-brief.txt",
            mime="text/plain",
            use_container_width=True
        )
    with ce2:
        st.download_button(
            "{ } Download JSON",
            json.dumps(D, indent=2),
            file_name="policy-analysis.json",
            mime="application/json",
            use_container_width=True
        )
