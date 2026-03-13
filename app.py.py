import streamlit as st
import anthropic
import json
import io

try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PolicyAI — Healthcare Analyzer",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #f4f6f9; }
[data-testid="stSidebar"] { background-color: #0d1f35; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(0,184,160,0.15) !important;
    border: 1px solid rgba(0,184,160,0.4) !important;
    color: #00b8a0 !important;
    border-radius: 8px !important;
    width: 100%;
    text-align: left;
    font-size: 13px;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(0,184,160,0.3) !important;
}
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    border: 1px solid #e8ecf2;
    margin-bottom: 0.5rem;
}
.metric-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #8898aa; margin-bottom: 4px; }
.metric-value { font-size: 16px; font-weight: 500; color: #0d1f35; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }
.badge-high { background: #fff0f0; color: #e5484d; }
.badge-medium { background: #fff8ec; color: #a36b00; }
.badge-low { background: #edfaf3; color: #166534; }
.badge-type { background: #e8edf4; color: #0d1f35; }
.impact-item {
    padding: 10px 14px;
    background: #f4f6f9;
    border-radius: 8px;
    margin-bottom: 8px;
    font-size: 13px;
    line-height: 1.6;
    border-left: 3px solid #00b8a0;
}
.risk-row {
    display: flex; gap: 12px; align-items: flex-start;
    padding: 10px 0; border-bottom: 1px solid #f4f6f9;
    font-size: 13px;
}
.section-header {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: #8898aa; margin-bottom: 12px; margin-top: 4px;
}
.timeline-item { padding: 12px 0; border-bottom: 1px solid #f4f6f9; }
.timeline-date { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #8898aa; }
.timeline-title { font-size: 14px; font-weight: 500; color: #0d1f35; margin: 3px 0; }
.timeline-desc { font-size: 13px; color: #4a5d70; }
div[data-testid="stExpander"] { background: white; border-radius: 8px; border: 1px solid #e8ecf2; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Presets ───────────────────────────────────────────────────────────────────
PRESETS = {
    "ACA 2026 Payment Notice": "ACA 2026 Notice of Benefit and Payment Parameters — Marketplace payment notice covering risk adjustment methodology updates, premium rate review, cost sharing limits, plan certification changes, and enrollee protections for plan year 2026.",
    "Essential Health Benefits": "ACA Essential Health Benefits (EHB) update — benchmark plan selection methodology, state flexibility in defining EHBs, habilitative services standards, and enforcement for qualified health plans.",
    "Cost Sharing Reductions": "ACA Cost Sharing Reduction (CSR) reconciliation rules — issuer obligations to provide CSRs to eligible enrollees, silver loading implications, CMS federal reimbursement procedures, and reconciliation methodology.",
    "Network Adequacy": "ACA Network Adequacy Standards for Qualified Health Plans — time and distance standards, appointment wait time requirements, specialist access, telehealth network credit, and CMS enforcement mechanisms.",
    "Preventive Care Mandate": "ACA Preventive Services Coverage Mandate — post-Braidwood litigation status, no-cost-sharing requirements for USPSTF A/B rated services, contraceptive coverage, immunizations, and issuer compliance obligations.",
    "Medicaid FMAP Update": "Medicaid Federal Medical Assistance Percentage (FMAP) update — federal matching rate adjustments, DSH allotment changes, state plan amendment requirements, and managed care organization rate certification impacts.",
    "Medicare IPPS Rule": "Medicare IPPS Inpatient Prospective Payment System final rule — base rate update, quality program adjustments, coding changes, hospital wage index impacts, and cost reporting requirements.",
    "Part D Drug Pricing": "Medicare Part D prescription drug pricing policy — negotiated drug prices, inflation rebates, out-of-pocket cap implementation, and plan bid impacts under the Inflation Reduction Act.",
}

# ── Text extraction ───────────────────────────────────────────────────────────
def extract_text(uploaded_file):
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()

    if name.endswith(".pdf"):
        if not PDF_SUPPORT:
            return None, "PyMuPDF not installed. Please install it: pip install pymupdf"
        doc = fitz.open(stream=raw, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text[:15000], None

    elif name.endswith(".docx"):
        if not DOCX_SUPPORT:
            return None, "python-docx not installed."
        doc = Document(io.BytesIO(raw))
        text = "\n".join([p.text for p in doc.paragraphs])
        return text[:15000], None

    elif name.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore")[:15000], None

    else:
        return None, f"Unsupported file type: {uploaded_file.name}"

# ── AI Analysis ───────────────────────────────────────────────────────────────
def analyze_policy(text: str, api_key: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a senior healthcare regulatory analyst. Analyze this policy and return ONLY raw JSON — no markdown, no code fences, no extra text.

Policy text:
\"\"\"
{text[:13000]}
\"\"\"

Return exactly this JSON:
{{
  "policyName": "Official policy name",
  "intro": "2-sentence plain-language overview",
  "effectiveDate": "Effective date or TBD",
  "policyType": "ACA|Medicaid|Medicare|Other",
  "regulatoryImpact": "High|Medium|Low",
  "complianceComplexity": "High|Medium|Low",
  "summary": ["finding 1", "finding 2", "finding 3", "finding 4"],
  "consumerImpact": ["impact 1", "impact 2", "impact 3"],
  "payerImpact": ["impact 1", "impact 2", "impact 3"],
  "providerImpact": ["impact 1", "impact 2", "impact 3"],
  "actions": [
    {{"title": "string", "detail": "string", "priority": "High|Medium|Low", "owner": "string"}},
    {{"title": "string", "detail": "string", "priority": "High|Medium|Low", "owner": "string"}},
    {{"title": "string", "detail": "string", "priority": "High|Medium|Low", "owner": "string"}}
  ],
  "risks": [
    {{"level": "High|Medium|Low", "risk": "string", "area": "Operational|Legal|Financial|Clinical", "mitigation": "string"}},
    {{"level": "High|Medium|Low", "risk": "string", "area": "Operational|Legal|Financial|Clinical", "mitigation": "string"}},
    {{"level": "High|Medium|Low", "risk": "string", "area": "Operational|Legal|Financial|Clinical", "mitigation": "string"}}
  ],
  "timeline": [
    {{"date": "Mon YYYY", "event": "string", "detail": "string"}},
    {{"date": "Mon YYYY", "event": "string", "detail": "string"}},
    {{"date": "Mon YYYY", "event": "string", "detail": "string"}}
  ]
}}"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def ask_question(question: str, analysis: dict, policy_text: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        messages=[{"role": "user", "content": f"You analyzed this healthcare policy: {json.dumps(analysis)}. Source excerpt: \"{policy_text[:2000]}\". Answer concisely: {question}"}]
    )
    return msg.content[0].text

# ── Badge helper ──────────────────────────────────────────────────────────────
def badge(label, cls="type"):
    return f'<span class="badge badge-{cls.lower()}">{label}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚕ PolicyAI")
    st.markdown("**Healthcare Regulation Analyzer**")
    st.markdown("---")

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-api03-...",
        help="Get free credits at console.anthropic.com"
    )

    st.markdown("---")
    st.markdown("**Quick Load — ACA Presets**")
    for name in PRESETS:
        if st.button(name, key=f"preset_{name}"):
            st.session_state["policy_text"] = PRESETS[name]
            st.session_state["analysis"] = None

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px;color:rgba(255,255,255,0.3);line-height:1.7">
    Supports: PDF, DOCX, TXT<br>
    Any CMS / ACA / Medicaid doc<br>
    Free hosting on Streamlit Cloud<br>
    github.com → streamlit.io
    </div>
    """, unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("# PolicyAI — Healthcare Policy Analyzer")
st.markdown("Upload any ACA, CMS, Medicaid, or Medicare document for instant AI-powered analysis.")

# Input area
col1, col2 = st.columns([2, 1])

with col1:
    uploaded = st.file_uploader(
        "Upload document (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        label_visibility="visible"
    )
    if uploaded:
        with st.spinner("Extracting text..."):
            extracted, err = extract_text(uploaded)
        if err:
            st.error(err)
        else:
            st.session_state["policy_text"] = extracted
            st.success(f"Extracted {len(extracted):,} characters from {uploaded.name}")

with col2:
    st.markdown("**Or paste policy text**")

policy_text = st.text_area(
    "Policy text",
    value=st.session_state.get("policy_text", ""),
    height=120,
    placeholder="Paste CMS rule text, regulation excerpt, or select a preset from the sidebar...",
    label_visibility="collapsed"
)

if policy_text:
    st.session_state["policy_text"] = policy_text

# Analyze button
col_btn1, col_btn2, _ = st.columns([1, 1, 3])
with col_btn1:
    analyze_clicked = st.button("⚡ Analyze Policy", type="primary", use_container_width=True)
with col_btn2:
    if st.button("Clear", use_container_width=True):
        st.session_state["policy_text"] = ""
        st.session_state["analysis"] = None
        st.rerun()

# Run analysis
if analyze_clicked:
    txt = st.session_state.get("policy_text", "").strip()
    if not txt:
        st.error("Please enter policy text or upload a document.")
    elif not api_key:
        st.error("Please enter your Anthropic API key in the sidebar.")
    else:
        with st.spinner("Claude is analyzing the policy..."):
            progress = st.progress(0, text="Parsing regulatory text...")
            try:
                progress.progress(25, text="Identifying key provisions...")
                result = analyze_policy(txt, api_key)
                progress.progress(75, text="Building analysis brief...")
                st.session_state["analysis"] = result
                st.session_state["analysis_text"] = txt
                progress.progress(100, text="Done!")
                progress.empty()
            except Exception as e:
                progress.empty()
                st.error(f"Analysis failed: {str(e)}")

# ── Results ───────────────────────────────────────────────────────────────────
analysis = st.session_state.get("analysis")
if analysis:
    st.markdown("---")

    # Header chips
    d = analysis
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Policy type</div><div class="metric-value">{badge(d['policyType'])}</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Effective date</div><div class="metric-value">{d['effectiveDate']}</div></div>""", unsafe_allow_html=True)
    with col3:
        lvl = d['regulatoryImpact'].lower()
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Regulatory impact</div><div class="metric-value">{badge(d['regulatoryImpact'], lvl)}</div></div>""", unsafe_allow_html=True)
    with col4:
        lvl = d['complianceComplexity'].lower()
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Compliance complexity</div><div class="metric-value">{badge(d['complianceComplexity'], lvl)}</div></div>""", unsafe_allow_html=True)

    st.markdown(f"### {d['policyName']}")
    st.markdown(f"*{d['intro']}*")
    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Summary", "Impacts", "Actions", "Compliance", "Timeline", "Q&A"
    ])

    with tab1:
        st.markdown('<div class="section-header">Key findings</div>', unsafe_allow_html=True)
        for item in d["summary"]:
            st.markdown(f'<div class="impact-item">{item}</div>', unsafe_allow_html=True)

    with tab2:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Consumers / Patients**")
            for item in d["consumerImpact"]:
                st.markdown(f'<div class="impact-item">{item}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown("**Payers / Issuers**")
            for item in d["payerImpact"]:
                st.markdown(f'<div class="impact-item">{item}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown("**Providers**")
            for item in d["providerImpact"]:
                st.markdown(f'<div class="impact-item">{item}</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="section-header">Recommended actions</div>', unsafe_allow_html=True)
        for i, action in enumerate(d["actions"]):
            lvl = action['priority'].lower()
            with st.expander(f"{badge(action['priority'], lvl)} &nbsp; {action['title']}", expanded=(i==0)):
                st.markdown(f"**Owner:** {action['owner']}")
                st.markdown(action["detail"])

    with tab4:
        st.markdown('<div class="section-header">Compliance risk register</div>', unsafe_allow_html=True)
        for risk in d["risks"]:
            lvl = risk['level'].lower()
            col_a, col_b, col_c = st.columns([1, 3, 3])
            with col_a:
                st.markdown(f'{badge(risk["level"], lvl)}', unsafe_allow_html=True)
            with col_b:
                st.markdown(f"**{risk['risk']}** _{risk['area']}_")
            with col_c:
                st.markdown(risk["mitigation"])
            st.markdown("---")

    with tab5:
        st.markdown('<div class="section-header">Key dates & milestones</div>', unsafe_allow_html=True)
        for item in d["timeline"]:
            st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-date">{item['date']}</div>
                <div class="timeline-title">{item['event']}</div>
                <div class="timeline-desc">{item['detail']}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab6:
        st.markdown("Ask any follow-up question about this policy.")
        question = st.text_input("Your question", placeholder="e.g. What does this mean for small group employers?")
        if st.button("Ask Claude") and question:
            if not api_key:
                st.error("API key required.")
            else:
                with st.spinner("Thinking..."):
                    answer = ask_question(question, d, st.session_state.get("analysis_text",""), api_key)
                st.markdown(f'<div class="impact-item">{answer}</div>', unsafe_allow_html=True)

    # Export
    st.markdown("---")
    col_e1, col_e2, _ = st.columns([1, 1, 3])
    with col_e1:
        memo = f"""HEALTHCARE POLICY ANALYSIS MEMO
{'='*50}
Policy: {d['policyName']}
Effective: {d['effectiveDate']}
Type: {d['policyType']} | Impact: {d['regulatoryImpact']} | Complexity: {d['complianceComplexity']}

OVERVIEW
{d['intro']}

KEY FINDINGS
{chr(10).join(f"{i+1}. {s}" for i,s in enumerate(d['summary']))}

CONSUMER IMPACT
{chr(10).join(f"• {s}" for s in d['consumerImpact'])}

PAYER IMPACT
{chr(10).join(f"• {s}" for s in d['payerImpact'])}

PROVIDER IMPACT
{chr(10).join(f"• {s}" for s in d['providerImpact'])}

RECOMMENDED ACTIONS
{chr(10).join(f"{i+1}. [{a['priority']}] {a['title']}{chr(10)}   Owner: {a['owner']}{chr(10)}   {a['detail']}" for i,a in enumerate(d['actions']))}

COMPLIANCE RISKS
{chr(10).join(f"[{r['level']}] {r['risk']} ({r['area']}){chr(10)}   Mitigation: {r['mitigation']}" for r in d['risks'])}

KEY DATES
{chr(10).join(f"{t['date']}: {t['event']} — {t['detail']}" for t in d['timeline'])}

Generated by PolicyAI — Powered by Claude (Anthropic)
"""
        st.download_button("Download Memo", memo, file_name="policy-analysis.txt", mime="text/plain")
    with col_e2:
        st.download_button("Download JSON", json.dumps(d, indent=2), file_name="policy-analysis.json", mime="application/json")
