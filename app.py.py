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

st.set_page_config(page_title="PolicyAI — Healthcare Analyzer", page_icon="⚕", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #f4f6f9; }
[data-testid="stSidebar"] { background-color: #0d1f35; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] .stButton button { background: rgba(0,184,160,0.15) !important; border: 1px solid rgba(0,184,160,0.4) !important; color: #00b8a0 !important; border-radius: 8px !important; width: 100%; text-align: left; font-size: 13px; }
[data-testid="stSidebar"] .stButton button:hover { background: rgba(0,184,160,0.3) !important; }
.metric-card { background: white; border-radius: 12px; padding: 1rem 1.25rem; border: 1px solid #e8ecf2; margin-bottom: 0.5rem; }
.metric-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #8898aa; margin-bottom: 4px; }
.metric-value { font-size: 15px; font-weight: 500; color: #0d1f35; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }
.badge-high { background: #fff0f0; color: #e5484d; }
.badge-medium { background: #fff8ec; color: #a36b00; }
.badge-low { background: #edfaf3; color: #166534; }
.badge-type { background: #e8edf4; color: #0d1f35; }
.impact-item { padding: 10px 14px; background: #f4f6f9; border-radius: 8px; margin-bottom: 8px; font-size: 13px; line-height: 1.6; border-left: 3px solid #00b8a0; }
.timeline-item { padding: 12px 0; border-bottom: 1px solid #f4f6f9; }
.timeline-date { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #8898aa; }
.timeline-title { font-size: 14px; font-weight: 500; color: #0d1f35; margin: 3px 0; }
.timeline-desc { font-size: 13px; color: #4a5d70; }
</style>
""", unsafe_allow_html=True)

PRESETS = {
    "ACA 2026 Payment Notice": "ACA 2026 Notice of Benefit and Payment Parameters — Marketplace payment notice covering risk adjustment methodology updates, premium rate review, cost sharing limits, plan certification changes, and enrollee protections for plan year 2026.",
    "Essential Health Benefits": "ACA Essential Health Benefits (EHB) update — benchmark plan selection methodology, state flexibility in defining EHBs, habilitative services standards, and enforcement for qualified health plans.",
    "Cost Sharing Reductions": "ACA Cost Sharing Reduction (CSR) reconciliation rules — issuer obligations to provide CSRs, silver loading implications, CMS reimbursement procedures.",
    "Network Adequacy": "ACA Network Adequacy Standards for Qualified Health Plans — time/distance standards, appointment wait times, specialist access, telehealth credit, and CMS enforcement.",
    "Preventive Care Mandate": "ACA Preventive Services Coverage Mandate — post-Braidwood status, no-cost-sharing for USPSTF A/B services, contraceptive coverage, and issuer obligations.",
    "Medicaid FMAP Update": "Medicaid FMAP update — federal matching rate adjustments, DSH allotment changes, state plan amendments, and managed care rate certification impacts.",
    "Medicare IPPS Rule": "Medicare IPPS final rule — base rate update, quality program changes, coding adjustments, wage index, and hospital cost reporting.",
    "Part D Drug Pricing": "Medicare Part D drug pricing — negotiated prices, inflation rebates, out-of-pocket cap under Inflation Reduction Act, and plan bid impacts.",
}

def extract_text(uploaded_file):
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    if name.endswith(".pdf"):
        if not PDF_SUPPORT:
            return None, "PyMuPDF not installed."
        doc = fitz.open(stream=raw, filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        return text[:15000], None
    elif name.endswith(".docx"):
        if not DOCX_SUPPORT:
            return None, "python-docx not installed."
        doc = Document(io.BytesIO(raw))
        text = "\n".join(p.text for p in doc.paragraphs)
        return text[:15000], None
    elif name.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore")[:15000], None
    return None, "Unsupported file type."

def call_gemini(prompt: str, api_key: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}}
    res = requests.post(url, json=payload, timeout=60)
    if not res.ok:
        raise Exception(f"Gemini API error {res.status_code}: {res.text[:300]}")
    return res.json()["candidates"][0]["content"]["parts"][0]["text"]

def analyze_policy(text: str, api_key: str) -> dict:
    prompt = f"""You are a senior healthcare regulatory analyst. Analyze this policy and return ONLY raw JSON — no markdown, no code fences, nothing else.

Policy:
\"\"\"{text[:12000]}\"\"\"

Return ONLY this exact JSON:
{{"policyName":"string","intro":"2-sentence plain-language overview","effectiveDate":"string","policyType":"ACA|Medicaid|Medicare|Other","regulatoryImpact":"High|Medium|Low","complianceComplexity":"High|Medium|Low","summary":["finding 1","finding 2","finding 3","finding 4"],"consumerImpact":["item1","item2","item3"],"payerImpact":["item1","item2","item3"],"providerImpact":["item1","item2","item3"],"actions":[{{"title":"string","detail":"string","priority":"High|Medium|Low","owner":"string"}},{{"title":"string","detail":"string","priority":"High|Medium|Low","owner":"string"}},{{"title":"string","detail":"string","priority":"High|Medium|Low","owner":"string"}}],"risks":[{{"level":"High|Medium|Low","risk":"string","area":"Operational|Legal|Financial|Clinical","mitigation":"string"}},{{"level":"High|Medium|Low","risk":"string","area":"Operational|Legal|Financial|Clinical","mitigation":"string"}},{{"level":"High|Medium|Low","risk":"string","area":"Operational|Legal|Financial|Clinical","mitigation":"string"}}],"timeline":[{{"date":"Mon YYYY","event":"string","detail":"string"}},{{"date":"Mon YYYY","event":"string","detail":"string"}},{{"date":"Mon YYYY","event":"string","detail":"string"}}]}}"""
    raw = call_gemini(prompt, api_key)
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

def ask_question(question: str, analysis: dict, policy_text: str, api_key: str) -> str:
    prompt = f"You analyzed this healthcare policy: {json.dumps(analysis)}. Source: \"{policy_text[:2000]}\". Answer concisely: {question}"
    return call_gemini(prompt, api_key)

def badge(label, cls="type"):
    return f'<span class="badge badge-{cls.lower()}">{label}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚕ PolicyAI")
    st.markdown("**Healthcare Regulation Analyzer**")
    st.markdown("🟢 **100% Free — Google Gemini**")
    st.markdown("---")
    st.markdown("**Get your FREE API key:**")
    st.markdown("1. Go to [aistudio.google.com](https://aistudio.google.com)\n2. Sign in with Google\n3. Click **Get API Key**\n4. Copy and paste below")
    api_key = st.text_input("Gemini API Key (free)", type="password", placeholder="AIza...", help="Free at aistudio.google.com — no credit card")
    st.markdown("---")
    st.markdown("**ACA Quick Load**")
    for name in PRESETS:
        if st.button(name, key=f"p_{name}"):
            st.session_state["policy_text"] = PRESETS[name]
            st.session_state["analysis"] = None
            st.rerun()
    st.markdown("---")
    st.markdown('<div style="font-size:11px;color:rgba(255,255,255,0.3);line-height:1.8">PDF · DOCX · TXT supported<br>Free: Gemini 1.5 Flash<br>Hosted free: Streamlit Cloud</div>', unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("# ⚕ PolicyAI — Healthcare Policy Analyzer")
st.markdown("Upload **any** healthcare policy document (PDF, DOCX, TXT) for instant AI analysis. **Completely free.**")

uploaded = st.file_uploader("Upload document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
if uploaded:
    with st.spinner("Extracting text..."):
        extracted, err = extract_text(uploaded)
    if err:
        st.error(err)
    else:
        st.session_state["policy_text"] = extracted
        st.success(f"Extracted {len(extracted):,} characters from **{uploaded.name}**")

policy_text = st.text_area(
    "Or paste policy text / select a preset from the sidebar",
    value=st.session_state.get("policy_text", ""),
    height=100,
    placeholder="Paste any CMS rule, ACA regulation, policy description..."
)
if policy_text != st.session_state.get("policy_text", ""):
    st.session_state["policy_text"] = policy_text

cb1, cb2, _ = st.columns([1, 1, 5])
with cb1:
    analyze_clicked = st.button("⚡ Analyze", type="primary", use_container_width=True)
with cb2:
    if st.button("Clear", use_container_width=True):
        st.session_state["policy_text"] = ""
        st.session_state["analysis"] = None
        st.rerun()

if analyze_clicked:
    txt = st.session_state.get("policy_text", "").strip()
    if not txt:
        st.error("Please enter policy text, upload a document, or select a preset from the sidebar.")
    elif not api_key:
        st.error("Please enter your free Gemini API key in the sidebar. Get it free at aistudio.google.com — no credit card needed.")
    else:
        prog = st.progress(0, text="Parsing regulatory text...")
        try:
            prog.progress(30, text="Identifying key provisions...")
            result = analyze_policy(txt, api_key)
            prog.progress(80, text="Building analysis brief...")
            st.session_state["analysis"] = result
            st.session_state["analysis_text"] = txt
            prog.progress(100, text="Complete!")
            prog.empty()
        except json.JSONDecodeError:
            prog.empty()
            st.error("AI returned invalid format. Please try again.")
        except Exception as e:
            prog.empty()
            st.error(f"Analysis failed: {str(e)}")

# ── Results ───────────────────────────────────────────────────────────────────
analysis = st.session_state.get("analysis")
if analysis:
    d = analysis
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Policy type</div><div class="metric-value">{badge(d["policyType"])}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Effective date</div><div class="metric-value">{d["effectiveDate"]}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Regulatory impact</div><div class="metric-value">{badge(d["regulatoryImpact"], d["regulatoryImpact"].lower())}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Compliance complexity</div><div class="metric-value">{badge(d["complianceComplexity"], d["complianceComplexity"].lower())}</div></div>', unsafe_allow_html=True)

    st.markdown(f"### {d['policyName']}")
    st.markdown(f"*{d['intro']}*")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Summary", "Impacts", "Actions", "Compliance", "Timeline", "Q&A"])

    with tab1:
        st.markdown("**Key findings**")
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
        for i, a in enumerate(d["actions"]):
            with st.expander(f"[{a['priority']}]  {a['title']}", expanded=(i == 0)):
                st.markdown(f"**Owner:** {a['owner']}")
                st.markdown(a["detail"])

    with tab4:
        for risk in d["risks"]:
            ca, cb, cc = st.columns([1, 3, 3])
            with ca:
                st.markdown(f'{badge(risk["level"], risk["level"].lower())}', unsafe_allow_html=True)
            with cb:
                st.markdown(f"**{risk['risk']}** — _{risk['area']}_")
            with cc:
                st.markdown(risk["mitigation"])
            st.divider()

    with tab5:
        for item in d["timeline"]:
            st.markdown(f'<div class="timeline-item"><div class="timeline-date">{item["date"]}</div><div class="timeline-title">{item["event"]}</div><div class="timeline-desc">{item["detail"]}</div></div>', unsafe_allow_html=True)

    with tab6:
        st.markdown("Ask any follow-up question about this policy.")
        q = st.text_input("Your question", placeholder="e.g. What does this mean for small group employers?")
        if st.button("Ask") and q:
            if not api_key:
                st.error("Enter API key in sidebar.")
            else:
                with st.spinner("Thinking..."):
                    ans = ask_question(q, d, st.session_state.get("analysis_text", ""), api_key)
                st.markdown(f'<div class="impact-item">{ans}</div>', unsafe_allow_html=True)

    st.markdown("---")
    memo = f"HEALTHCARE POLICY ANALYSIS\n{'='*50}\nPolicy: {d['policyName']}\nEffective: {d['effectiveDate']}\nType: {d['policyType']} | Impact: {d['regulatoryImpact']} | Complexity: {d['complianceComplexity']}\n\nOVERVIEW\n{d['intro']}\n\nKEY FINDINGS\n{chr(10).join(f'{i+1}. {s}' for i,s in enumerate(d['summary']))}\n\nCONSUMER IMPACT\n{chr(10).join(f'• {s}' for s in d['consumerImpact'])}\n\nPAYER IMPACT\n{chr(10).join(f'• {s}' for s in d['payerImpact'])}\n\nPROVIDER IMPACT\n{chr(10).join(f'• {s}' for s in d['providerImpact'])}\n\nRECOMMENDED ACTIONS\n{chr(10).join(f'{i+1}. [{a[\"priority\"]}] {a[\"title\"]}{chr(10)}   Owner: {a[\"owner\"]}{chr(10)}   {a[\"detail\"]}' for i,a in enumerate(d['actions']))}\n\nCOMPLIANCE RISKS\n{chr(10).join(f'[{r[\"level\"]}] {r[\"risk\"]} ({r[\"area\"]}){chr(10)}   Mitigation: {r[\"mitigation\"]}' for r in d['risks'])}\n\nKEY DATES\n{chr(10).join(f'{t[\"date\"]}: {t[\"event\"]} - {t[\"detail\"]}' for t in d['timeline'])}\n\nGenerated by PolicyAI - Powered by Google Gemini (Free)"
    ce1, ce2, _ = st.columns([1, 1, 4])
    with ce1:
        st.download_button("Download Memo", memo, file_name="policy-analysis.txt", mime="text/plain")
    with ce2:
        st.download_button("Download JSON", json.dumps(d, indent=2), file_name="policy-analysis.json", mime="application/json")
