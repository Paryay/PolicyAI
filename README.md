# PolicyAI — Healthcare Policy Analyzer

AI-powered analysis of any ACA, CMS, Medicaid, Medicare document.  
Upload PDF, DOCX, or TXT → get instant structured analysis.

**100% free hosting on Streamlit Community Cloud.**

---

## Deploy in 5 minutes (all free)

### Step 1 — Get Anthropic API key
1. Go to https://console.anthropic.com
2. Sign up → click API Keys → Create Key
3. Copy it (starts with `sk-ant-...`)
4. New accounts get free credits

### Step 2 — Put on GitHub
1. Go to https://github.com → sign up free
2. Click **New repository** → name it `policyai` → Create
3. Click **Add file → Upload files**
4. Upload these 3 files: `app.py`, `requirements.txt`, `README.md`
5. Click **Commit changes**

### Step 3 — Deploy on Streamlit Cloud (free)
1. Go to https://share.streamlit.io → sign in with GitHub
2. Click **New app**
3. Select your `policyai` repo
4. Main file path: `app.py`
5. Click **Advanced settings → Secrets** and add:
   ```
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
   *(Optional — users can also enter their own key in the app)*
6. Click **Deploy** → wait 2 minutes
7. You get a free URL: `https://yourname-policyai.streamlit.app`

### Step 4 — Share on LinkedIn
Post your live link — anyone can upload a healthcare PDF and analyze it instantly.

---

## What it analyzes
- ACA Marketplace rules & payment notices
- CMS final rules (IPPS, OPPS, Part D)
- Medicaid/CHIP policy updates  
- Medicare Advantage plan documents
- State insurance bulletins
- Any PDF, DOCX, or TXT policy document

## Output tabs
- **Summary** — key findings in plain language
- **Impacts** — consumers, payers, providers
- **Actions** — prioritized recommended actions
- **Compliance** — risk register with mitigations
- **Timeline** — key dates and deadlines
- **Q&A** — ask follow-up questions

---

Built with Streamlit + Claude (Anthropic)
