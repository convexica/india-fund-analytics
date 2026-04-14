# 🔬 ConvexLab | Quantitative Portfolio Intelligence (v1.4.0)

A high-performance, institutional-grade quantitative analysis workstation for Indian Mutual Funds. Evaluate performance, risk, and consistency using advanced financial forensics and **High-Conviction AI Synthesis**.

> **Live Demo**: [convexlab.streamlit.app](https://convexlab.streamlit.app/)

---

## 🛡️ v1.4.0: Stability & Security Hardening (Current)

This update focuses on institutional-grade security and dependency governance.

*   **Security Audit**: Mitigated CVE-2025-27499 (Pillow GZIP Decompression Bomb) by upgrading to `pillow>=12.2.0`.
*   **Code Quality**: Full linting pass with **Ruff** for optimized import ordering and deterministic code style.
*   **Dependency Governance**: Optimized `uv.lock` for faster, cross-platform deterministic builds.

---

## 🚀 v1.3.0: Proprietary High-Conviction Metrics

ConvexLab now features a suite of four proprietary forensic scores designed to separate manager skill from circumstantial market luck.

*   ⚓ **Convexity Score (Inclusive Model)**: Measures a fund’s **Structural Asymmetry** using a multi-horizon (1Y/3Y/5Y) blend of capture efficiency. Target: >1.2.
*   💎 **Alpha Quality (40/40/20 Model)**: A composite score (0—10) measuring **Tracking-Error Efficiency**, Outperformance Frequency, and Alpha Persistence. Target: >7.
*   ⚖️ **Drawdown Efficiency (DER)**: A horizon-synchronized metric measuring **Return per unit of Crash Risk** (CAGR / Max Drawdown). Target: >0.5x.
*   🫧 **Consistency Index**: Measures **Return Repeatability** by blending benchmark outperformance frequency (40%) with an intensive rolling variance penalty (60%). Target: >75%.

---

## 🦾 v1.2.0 Branch: The AI Insight Agent

ConvexLab features a state-of-the-art **AI Synthesis Engine** designed to transform complex multi-dimensional data into institutional investment memos.

*   🧠 **High-Conviction Synthesis**: Moves beyond generic summaries to provide definitive verdicts on alpha validity and downside behavior.
*   ✨ **"Quiet Luxury" UI Rendering**: Custom-engineered **Deterministic CSS Container** with institutional typography and zero AI formatting artifacts.
*   📊 **Analyst Briefing Mode**: Generates a dense, quantitative markdown briefing for export into external AI models (Claude/GPT-4o) for private forensics.

---

## 🛠️ Core Quantitative Capabilities

*   **Inclusive Performance Analysis**: Calculate CAGR, Absolute Growth, and Multipliers across 1Y, 3Y, 5Y, and Max horizons.
*   **Risk & Efficiency**: Compute advanced risk-adjusted metrics like **Sharpe Ratio**, **Sortino Ratio**, **Information Ratio**, and **Omega Ratio**.
*   🛡️ **Advanced Historical Stress-Testing**: Evaluate fund resilience during the **2024-25 (Market Correction)**, COVID-19 Crash, 2018 NBFC Crisis, and the 2008 Financial Crisis.
*   **Regime Dynamics**: Identify fund style using **Beta** and **Jensen's Alpha** across distinct market regimes (Bull/Bear/Sideways).
*   **Rolling Returns**: Generate detailed rolling return profiles (1Y, 3Y, 5Y) illustrating the probability of beating bank FDs and the frequency of negative outcome scenarios.

---

## 🛠️ Architecture & Technology

The application follows a modular, professional Python architecture designed for speed, observability, and reliability:

```mermaid
graph TD
    User([User In Dashboard]) --> UI[Streamlit Frontend]
    UI --> Fetcher[Data Fetcher Module]
    Fetcher --> Cache[(Local CSV Cache)]
    Fetcher --> AMFI_API{AMFI API}

    UI --> AI[AI Insight Agent]
    AI --> Groq[Groq Llama-3.3]
    AI --> Gemini[Google Gemini]

    Fetcher --> Analytics[Analytics Engine]
    Analytics --> Math[Quantitative Math: Alpha/Beta/Sharpe]
    Math --> UI
    Math --> AI
```

### Technical Stack
*   **Intelligence Layer**: [Groq SDK](https://github.com/groq/groq-python) and [Google Generative AI](https://github.com/google-gemini/generative-ai-python).
*   **Frontend**: [Streamlit](https://streamlit.io/) with custom **CSS Injection** for premium branding.
*   **Visualization**: [Plotly](https://plotly.com/python/) for interactive, publication-quality financial charts.
*   **Analytics Engine**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), and [SciPy](https://scipy.org/) for vectorized financial computations.
*   **Data Layer**: Custom robust integration with **AMFI API** (`mfapi.in`) and **yfinance** for index benchmarks.
*   **Dependency Governance**: Uses **`uv`** for deterministic builds, ensuring version-locked reproducibility.

---

## 📦 Installation & Setup

### 1. Clone & Initialize
```bash
git clone https://github.com/convexica/convexlab.git
cd convexlab
python -m venv venv
# Activate venv: source venv/bin/activate (Mac/Linux) or .\venv\Scripts\activate (Windows)
```

### 2. Install Dependencies
```bash
# Recommended (Fast & Deterministic)
uv sync

# Standard
pip install -r requirements.txt
```

### 3. Configure AI Secrets
Create a `.streamlit/secrets.toml` file in the root directory:
```toml
GROQ_API_KEY = "your_groq_key_here"
GEMINI_API_KEY = "your_gemini_key_here"
```

### 4. Run the Dashboard
```bash
streamlit run app/main.py
```

---

## 📁 Project Structure

```text
├── .github/workflows/       # CI/CD Guardian (Linting, Testing, Keep-Alive)
├── app/
│   ├── main.py              # UI Orchestration & Deterministic AI Renderer
│   ├── core/
│   │   ├── analytics.py     # Financial Engine & AI Prompt Framework
│   │   └── data_fetcher.py  # API Management & Cache Logic
│   └── components/
│       └── charts.py        # Reusable Plotly Financial Visuals
├── tests/                   # Automated Financial Validation
├── internal_docs/           # Architectural Guidelines & KI Records
├── pyproject.toml           # Modern Project Config (PEP 621)
└── LICENSE                  # MIT License
```

---

## ⚙️ Quality Assurance
*   **Linter**: Fast style checking with **Ruff**.
*   **Type Guard**: Strict static analysis with **Mypy**.
*   **Unit Tests**: Automated financial validation with **Pytest**.
*   **Maintenance**: Managed by **Dependabot** for zero-effort security updates.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

**Refining Alpha through Forensics 📈 [Convexica](https://convexica.com)**
ro-effort maintenance.


---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

**Developed with 📈 by [Convexica](https://convexica.com)**
