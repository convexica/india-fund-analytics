import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from components.charts import (
    plot_benchmark_comparison,
    plot_capture_ratios,
    plot_drawdown,
    plot_nav_history,
)
from core.analytics import MFAnalytics
from core.data_fetcher import MFDataFetcher
from core.logger import get_logger, log_event

# Initialize professional logger
logger = get_logger(__name__)

# Page Configuration
st.set_page_config(page_title="India Fund Analytics", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef2f6;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef2f6;
        margin-bottom: 20px;
    }
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    /* Targeted removal of Streamlit's default 6rem sidebar top padding */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding-top: 1.5rem !important;
        gap: 0.8rem;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef2f6;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_tools():
    return MFDataFetcher(), MFAnalytics()


fetcher, analytics = get_tools()

# Sidebar - Search and Selection
with st.sidebar:
    # Custom styled Title to bypass default h1 margins
    st.markdown(
        "<h1 style='margin-top: -2.5rem; font-size: 1.7rem; margin-bottom: 0.2rem;'>📈 Fund Analytics</h1>", 
        unsafe_allow_html=True
    )
    st.caption("Convexica: Mutual Fund Intelligence")

    st.markdown("---")
    st.header("🎯 Selection")
    
    # Fund Discovery
    search_query = st.text_input("Name", placeholder="Search Fund (e.g. HDFC Flexi)", label_visibility="collapsed")
    selected_code = None
    if search_query:
        try:
            search_results = fetcher.search_funds(search_query)
            if search_results:
                schemes = list(search_results.values())
                default_ix = 0
                for i, name in enumerate(schemes):
                    if "Direct" in name and "Growth" in name:
                        default_ix = i
                        break
                selected_name = st.selectbox("Schemes", options=schemes, index=default_ix, label_visibility="collapsed")
                selected_code = [k for k, v in search_results.items() if v == selected_name][0]
            else:
                st.error("Not found.")
        except Exception:
            st.error("Error.")

    # Benchmark Selection (Immediately follows Fund)
    bench_type = st.radio("Benchmark", ["Index", "Fund"], horizontal=True, label_visibility="collapsed")
    benchmark_code = None
    benchmark_name = "Benchmark"
    benchmark_ticker = None
    if bench_type == "Index":
        bench_option = st.selectbox("Index", ["^NSEI (Nifty 50)", "^CRSLDX (Nifty 500)"], index=0, label_visibility="collapsed")
        benchmark_ticker = bench_option.split(" ")[0]
        benchmark_name = bench_option.split("(")[1].replace(")", "")
    else:
        bench_search = st.text_input("Benchmark Search", placeholder="Benchmark Fund", label_visibility="collapsed")
        if bench_search:
            bench_results = fetcher.search_funds(bench_search)
            if bench_results:
                benchmark_name = st.selectbox("Select", options=list(bench_results.values()), label_visibility="collapsed")
                benchmark_code = [k for k, v in bench_results.items() if v == benchmark_name][0]

    st.markdown("---")
    # Analysis Window (When)
    st.header("⏳ Horizon")
    analysis_period = st.radio(
        "Period", 
        ["All Time", "1 Year", "3 Years", "5 Years", "10 Years", "Custom Range"], 
        index=0,
        label_visibility="collapsed"
    )

    if analysis_period == "Custom Range":
        c1, c2 = st.columns(2)
        with c1:
            custom_start_date = st.date_input("Start", value=pd.to_datetime("2020-01-01"))
        with c2:
            custom_end_date = st.date_input("End", value=pd.to_datetime("today"))
    else:
        custom_start_date = None
        custom_end_date = None

    st.markdown("---")
    # Technical Calibration (How)
    st.header("⚙️ Calibration")
    # Fetch real-time rate for initial calibration (fallback to 6.5)
    default_rf = fetcher.get_current_risk_free_rate() * 100
    risk_free_rate = st.slider("Risk-Free Rate (%)", 0.0, 10.0, default_rf, 0.1) / 100
    analytics.rf = risk_free_rate

# Main Content
if selected_code:
    with st.spinner(f"Analyzing {selected_name}..."):
        try:
            raw_nav_data = fetcher.get_nav_history(selected_code)
            fund_info = fetcher.get_fund_info(selected_code)
        except Exception as e:
            logger.error(f"AMFI API failure: {e}")
            st.error("⚠️ **API Gateway Error (AMFI)**")
            st.warning(f"{e}")
            st.info("The external AMFI server is currently unresponsive. Please wait 5-10 minutes and try again.")
            st.stop()

        if not raw_nav_data.empty:
            # Determine start date for benchmark based on available fund history
            raw_start_date = raw_nav_data.index[0]

            if bench_type == "Index":
                raw_bench_data = fetcher.get_benchmark_history(benchmark_ticker, start_date=raw_start_date)
            else:
                if benchmark_code:
                    if benchmark_code == selected_code:
                        st.warning("Comparing a fund against itself. Benchmark data will be identical.")
                    try:
                        raw_bench_data_df = fetcher.get_nav_history(benchmark_code)
                        raw_bench_data = raw_bench_data_df["nav"] if not raw_bench_data_df.empty else pd.Series()
                    except Exception as e:
                        st.error(f"Could not load benchmark fund: {e}")
                        raw_bench_data = pd.Series()
                else:
                    raw_bench_data = pd.Series()

            if bench_type == "Index" and raw_bench_data.empty:
                st.warning(f"⚠️ **Benchmark Connection Timeout**: Could not retrieve {benchmark_name} history. Only fund performance will be displayed.")
            elif not raw_bench_data.empty:
                log_event(logger, "BENCHMARK_LOADED", ticker=benchmark_name, status="SUCCESS")

            # 0. Initial App State
            if "app_init" not in st.session_state:
                log_event(logger, "APP_LAUNCH", status="SUCCESS")
                st.session_state.app_init = True
            # Apply Time Period Filtering
            nav_data = raw_nav_data.copy()
            bench_data = raw_bench_data.copy() if not raw_bench_data.empty else pd.Series()

            if analysis_period == "Custom Range":
                if custom_start_date and custom_end_date:
                    start_ts = pd.Timestamp(custom_start_date)
                    end_ts = pd.Timestamp(custom_end_date)
                    nav_data = nav_data[(nav_data.index >= start_ts) & (nav_data.index <= end_ts)]
                    if not bench_data.empty:
                        bench_data = bench_data[(bench_data.index >= start_ts) & (bench_data.index <= end_ts)]
            elif analysis_period != "All Time":
                years = int(analysis_period.split(" ")[0])
                cutoff_date = nav_data.index[-1] - pd.DateOffset(years=years)
                nav_data = nav_data[nav_data.index >= cutoff_date]
                if not bench_data.empty:
                    bench_data = bench_data[bench_data.index >= cutoff_date]

            if nav_data.empty:
                st.error("No data available for the selected range. Please adjust your dates or time horizon.")
                st.stop()

    if not raw_nav_data.empty:
        # Fund Title & Stats Summary
        st.markdown(f"### {selected_name}")
        st.caption(f"**{fund_info.get('scheme_type', 'N/A')}** | {fund_info.get('scheme_category', 'N/A')} | {fund_info.get('fund_house', 'N/A')}")
        st.markdown("---")

        # Top Level Metrics - Single Row
        metrics = analytics.calculate_risk_metrics(nav_data["nav"])
        _, max_dd = analytics.calculate_drawdowns(nav_data["nav"])
        multiplier = analytics.calculate_fund_multiplier(nav_data["nav"])

        # Clarify Period Label if actual history is shorter than selection
        actual_days = (nav_data.index[-1] - nav_data.index[0]).days
        actual_yrs = actual_days / 365.25

        # Determine if we should show 'Since Inception' or the selected period
        is_si = False
        if analysis_period == "Custom Range":
            display_label = f"Custom (~{actual_yrs:.1f}Y)"
        elif analysis_period != "All Time":
            try:
                req_yrs = int(analysis_period.split(" ")[0])
                if actual_yrs < (req_yrs - 0.1):  # If significantly shorter than requested
                    is_si = True
            except Exception:
                pass

        if analysis_period != "Custom Range":
            display_label = f"S.I. (~{actual_yrs:.1f}Y)" if (is_si or analysis_period == "All Time") else analysis_period

        m_col0, m_col1, m_col2, m_col3, m_col4 = st.columns(5)
        m_col0.metric(f"Growth ({display_label})", f"{multiplier:.2f}x", help="Investment multiple. e.g., 2.0x means your money doubled.")
        m_col1.metric(f"CAGR ({display_label})", f"{metrics.get('cagr', 0):.1%}", help="The effective annual growth rate of your investment, assuming returns are compounded yearly.")
        m_col2.metric("Volatility", f"{metrics.get('volatility', 0):.1%}", help="Annualized Standard Deviation of returns. Measures the 'bounciness' or risk of the fund.")
        m_col3.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}", help="Excess return per unit of risk. Higher is better. Uses the provided Risk-Free Rate.")
        m_col4.metric("Max Drawdown", f"{max_dd:.1%}", help="Largest peak-to-trough decline. Measures the worst-case loss scenario.")

        # 1. Performance History (Rebased to 100)
        st.markdown("### 📈 Performance & Drawdown")
        if not bench_data.empty:
            st.plotly_chart(plot_benchmark_comparison(nav_data["nav"], bench_data, selected_name, benchmark_name), width="stretch", key="main_perf_comparison")
        else:
            st.plotly_chart(plot_nav_history(nav_data, selected_name), width="stretch", key="main_nav_history")

        # 2. Drawdown History
        drawdown_fund, _ = analytics.calculate_drawdowns(nav_data["nav"])
        drawdown_bench = None
        if not bench_data.empty:
            drawdown_bench, _ = analytics.calculate_drawdowns(bench_data)
        st.plotly_chart(plot_drawdown(drawdown_fund, drawdown_bench, selected_name, benchmark_name), width="stretch", key="main_drawdown_history")

        # 3. Calendar Year Returns
        st.markdown("### 📅 Calendar Year Performance")
        f_cal = analytics.calculate_calendar_returns(raw_nav_data["nav"])
        if not raw_bench_data.empty:
            b_cal = analytics.calculate_calendar_returns(raw_bench_data)
            cal_df = pd.DataFrame({"Fund": f_cal, benchmark_name: b_cal})
        else:
            cal_df = pd.DataFrame({"Fund": f_cal})

        # Sort and limit to last 10 entries
        cal_df = cal_df.sort_index(ascending=False).head(11)  # To show roughly 10 years + current YTD

        cal_c1, cal_c2 = st.columns([1, 1.8])
        with cal_c1:
            # Display table with formatting
            disp_cal = cal_df.copy()
            for col in disp_cal.columns:
                disp_cal[col] = disp_cal[col].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "-")
            st.dataframe(disp_cal, width="stretch", height=420)

        with cal_c2:
            # Display comparative bar chart
            cal_df_plot = cal_df.copy()
            cal_df_plot.index.name = "Year"
            plot_cal_df = cal_df_plot.reset_index().melt(id_vars="Year", var_name="Type", value_name="Return")
            fig_cal = px.bar(
                plot_cal_df, x="Year", y="Return", color="Type", barmode="group", color_discrete_sequence=["#1f77b4", "#ff7f0e"], labels={"Return": "Annual Return", "Year": ""}, height=350
            )
            fig_cal.update_layout(margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig_cal.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_cal, width="stretch", key="calendar_year_chart")

        # Performance Analysis Data Prep
        periods = {"1 Year": 1, "3 Years": 3, "5 Years": 5, "10 Years": 10}
        ret_data, vol_data, ratio_data, deep_metrics = [], [], [], []

        for label, yrs in periods.items():
            f_ret, f_vol, f_stats = analytics.get_periodic_metrics(raw_nav_data["nav"], yrs, raw_bench_data)

            # Benchmark standalone metrics for the same window
            b_ret, b_vol = None, None
            if not raw_bench_data.empty:
                b_ret, b_vol, _ = analytics.get_periodic_metrics(raw_bench_data, yrs)

            # Data for compact sections
            ret_data.append({"Period": label, "Fund": f_ret, f"{benchmark_name}": b_ret})
            vol_data.append({"Period": label, "Fund": f_vol, f"{benchmark_name}": b_vol})

            f_rat = (f_ret / f_vol) if f_ret and f_vol else None
            b_rat = (b_ret / b_vol) if b_ret and b_vol else None
            ratio_data.append({"Period": label, "Fund": f_rat, f"{benchmark_name}": b_rat})

            if f_stats:
                deep_metrics.append(
                    {
                        "Period": label,
                        "Jensen Alpha": f"{f_stats['Alpha']:.1%}",
                        "Beta": f"{f_stats['Beta']:.2f}",
                        "Sharpe": f"{f_stats['Sharpe']:.2f}",
                        "Sortino": f"{f_stats['Sortino']:.2f}",
                        "Calmar": f"{f_stats['Calmar']:.2f}",
                        "Info Ratio": f"{f_stats['InfoRatio']:.2f}",
                        "Batting Avg": f"{f_stats['BattingAvg']:.1%}",
                        "Omega": f"{f_stats['Omega']:.2f}",
                        "Hurst (H)": f"{f_stats['Hurst']:.2f}",
                        "Upside Capture": f"{f_stats['Upside']:.1f}%",
                        "Downside Capture": f"{f_stats['Downside']:.1f}%",
                    }
                )

        def display_metric_section(title, data_list, is_pct=True):
            st.markdown(f"#### {title}")
            df = pd.DataFrame(data_list)
            col_tbl, col_cht = st.columns([1, 1.5])
            with col_tbl:
                display_df = df.copy()
                for col in ["Fund", benchmark_name]:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.1%}" if is_pct and pd.notnull(x) else (f"{x:.2f}" if pd.notnull(x) else "-"))

                # Professional Column Config for Periodic blocks
                config = {"Period": st.column_config.TextColumn(width="small")}
                if title == "Periodic Returns":
                    help_text = "Annualized performance over the specific window."
                elif title == "Periodic Volatility":
                    help_text = "Annualized risk (Standard Deviation). Lower is preferred for conservative investors."
                else:
                    help_text = "Risk-Adjusted Return (Return / Volatility). Measures return per 1% risk."

                config["Fund"] = st.column_config.TextColumn(help=help_text)
                st.dataframe(display_df, hide_index=True, width="stretch", column_config=config)
            with col_cht:
                plot_df = df.melt(id_vars="Period", var_name="Type", value_name="Value")
                fig = px.bar(plot_df, x="Period", y="Value", color="Type", barmode="group", color_discrete_sequence=["#1f77b4", "#ff7f0e"], height=180)
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=True, xaxis_title=None, yaxis_title=None)
                if is_pct:
                    fig.update_yaxes(tickformat=".0%")
                st.plotly_chart(fig, width="stretch", key=f"bar_{title.lower().replace(' ', '_')}")

        display_metric_section("Periodic Returns", ret_data)
        display_metric_section("Periodic Volatility", vol_data)
        display_metric_section("Return / Risk Ratio", ratio_data, is_pct=False)

        # 3. Market Participation Insight
        st.markdown("### 🎯 Market Participation & Efficiency")
        if not bench_data.empty and len(bench_data) > 20:
            c1, c2 = st.columns([1.2, 1])
            with c1:
                # Scatter Plot for Insight: Fund Monthly vs Benchmark Monthly
                df_monthly = analytics.get_monthly_returns(nav_data["nav"], bench_data)
                fig_scatter = px.scatter(df_monthly, x="Bench", y="Fund", trendline="ols", title="Monthly Performance Sensitivity", labels={"Bench": f"{benchmark_name} Return", "Fund": "Fund Return"})
                # Add diagonal y=x line
                lims = [min(df_monthly.min()), max(df_monthly.max())]
                fig_scatter.add_shape(type="line", x0=lims[0], y0=lims[0], x1=lims[1], y1=lims[1], line=dict(color="gray", dash="dash"))
                fig_scatter.update_layout(height=400, template="plotly_white")
                fig_scatter.update_xaxes(tickformat=".0%")
                fig_scatter.update_yaxes(tickformat=".0%")
                st.plotly_chart(fig_scatter, width="stretch", key="market_sensitivity_scatter")
                st.info(f"**Interpretation:** Points above the line beat {benchmark_name}. A steeper trendline suggests a high-beta fund.")

            with c2:
                cap_metrics = analytics.calculate_capture_ratios(nav_data["nav"], bench_data)
                st.plotly_chart(plot_capture_ratios(cap_metrics), width="stretch", key="capture_ratios_summary")

        if deep_metrics:
            st.markdown("#### 📜 Detailed Analysis Reports")
            df_full = pd.DataFrame(deep_metrics)

            t1, t2 = st.tabs(["📊 Risk Efficiency", "🧬 Style & Consistency"])

            with t1:
                # Group 1: Risk-Adjusted Efficiency
                efficiency_cols = ["Period", "Sharpe", "Sortino", "Calmar", "Info Ratio", "Omega"]
                st.dataframe(
                    df_full[efficiency_cols],
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Sharpe": st.column_config.TextColumn(help="Excess return per unit of total risk. Higher is better."),
                        "Sortino": st.column_config.TextColumn(help="Penalizes downside volatility. Ideal for skewed return profiles."),
                        "Calmar": st.column_config.TextColumn(help="CAGR / Max Drawdown. Measures return vs 'crash' risk. Higher is better."),
                        "Info Ratio": st.column_config.TextColumn(help="Active return vs benchmark per tracking error. Measures manager skills."),
                        "Omega": st.column_config.TextColumn(help="Weighted gains vs losses. Considers full distribution shape."),
                    },
                )
                st.caption("Insights into how efficiently the fund generates returns for every unit of risk taken.")

            with t2:
                # Group 2: Behavioral & Market Character
                behavior_cols = ["Period", "Beta", "Jensen Alpha", "Batting Avg", "Hurst (H)", "Upside Capture", "Downside Capture"]
                st.dataframe(
                    df_full[behavior_cols],
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Beta": st.column_config.TextColumn(help="Market Sensitivity. 1.0 = moves with index. >1.0 Aggressive, <1.0 Defensive."),
                        "Jensen Alpha": st.column_config.TextColumn(help="Annualized excess return above market risk expectation. High Alpha = Skill."),
                        "Batting Avg": st.column_config.TextColumn(help="Frequency the fund beat the benchmark. Measures consistency."),
                        "Hurst (H)": st.column_config.TextColumn(help="Trend intensity. >0.5 Persistent (Trending), <0.5 Mean-reverting."),
                        "Upside Capture": st.column_config.TextColumn(help="Gain capture during positive months. Higher is better."),
                        "Downside Capture": st.column_config.TextColumn(help="Loss capture during negative months. Lower is better."),
                    },
                )
                st.caption("Analysis of the fund's behavioral style, consistency, and active management character.")

        # 4. Rolling Returns Profile
        st.markdown("---")
        st.markdown("### 📊 Rolling Returns Performance")
        rolling_profile = analytics.calculate_rolling_return_profile(raw_nav_data["nav"])

        if rolling_profile:
            profile_df = pd.DataFrame(rolling_profile)
            row_order = [
                "Minimum",
                "Median",
                "Maximum",
                "% times -ve returns",
                "% times returns 0 - 5%",
                "% times returns 5 - 10%",
                "% times returns 10 - 15%",
                "% times returns 15 - 20%",
                "% times returns > 20%",
            ]
            profile_df = profile_df.reindex(row_order)

            # Professionally highlight insufficient history
            def format_rolling(val):
                if pd.isna(val) or val is None:
                    return "Short Hist."
                return f"{val:.1%}"

            st.dataframe(
                profile_df.map(format_rolling),
                width="stretch",
                column_config={
                    "index": st.column_config.TextColumn("Returns Statistic", width="medium"),
                    "1 Year": st.column_config.TextColumn(help="Rolling 1-Year annualized returns.", width="small"),
                    "3 Years": st.column_config.TextColumn(help="Rolling 3-Year annualized returns.", width="small"),
                    "5 Years": st.column_config.TextColumn(help="Rolling 5-Year annualized returns.", width="small"),
                },
            )
        else:
            st.info("Insufficient history for rolling return profile (requires at least 1 year of data).")

        if not deep_metrics and not bench_data.empty:
            st.warning("Insufficient history for detailed periodic metrics.")

    else:
        st.error("Historical NAV data unavailable.")

else:
    st.info("👈 Enter a fund name (e.g., 'HDFC Flexi' or 'SBI Bluechip') to begin deep analysis.")
