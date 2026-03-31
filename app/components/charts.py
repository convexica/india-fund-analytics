import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_nav_history(nav_df, scheme_name):
    """Plot NAV history over time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=nav_df.index, y=nav_df["nav"], mode="lines", name="NAV", line=dict(color="#1f77b4", width=2)))

    fig.update_layout(
        title=dict(text=f"NAV History: {scheme_name}", font=dict(size=18)),
        xaxis_title="Date",
        yaxis_title="NAV",
        template="plotly_white",
        hovermode="x unified",
        height=430,
        margin=dict(l=20, r=20, t=60, b=100),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        font=dict(family="Inter, sans-serif", size=13),
    )
    return fig


def plot_rolling_returns(rolling_df, window_years):
    """Plot rolling returns heatmap or line chart."""
    fig = px.line(rolling_df, x=rolling_df.index, y=rolling_df.values, title=f"{window_years}Y Rolling Returns", labels={"y": "Annualized Return", "index": "Date"})

    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.update_layout(title=dict(text=f"{window_years}Y Rolling Returns", font=dict(size=18)), template="plotly_white", height=400, font=dict(family="Inter, sans-serif", size=13))
    # Format yaxis as percentage
    fig.update_yaxes(tickformat=".1%")
    return fig


def plot_drawdown(fund_drawdown, bench_drawdown=None, fund_name="Fund", bench_name="Benchmark"):
    """Plot comparative drawdown chart."""
    fig = go.Figure()
    # Fund Trace - Professional bold red with subtle fill
    fig.add_trace(go.Scatter(x=fund_drawdown.index, y=fund_drawdown, fill="tozeroy", name=fund_name, line=dict(color="#1f77b4", width=2)))
    # Benchmark Trace - Match performance chart (dashed line)
    if bench_drawdown is not None:
        # Align index before plotting to ensure clean overlay
        bench_aligned = bench_drawdown.reindex(fund_drawdown.index).ffill()
        fig.add_trace(go.Scatter(x=bench_aligned.index, y=bench_aligned, name=bench_name, line=dict(color="#ff7f0e", width=2, dash="dash")))

    fig.update_layout(
        title=dict(text="Peak-to-Trough Drawdown Analysis", font=dict(size=18)),
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        template="plotly_white",
        hovermode="x unified",
        height=430,
        margin=dict(l=20, r=20, t=60, b=100),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        font=dict(family="Inter, sans-serif", size=13),
    )
    fig.update_yaxes(tickformat=".1%")
    return fig


def plot_returns_distribution(nav_df):
    """Plot distribution of daily returns."""
    returns = nav_df["nav"].pct_change(fill_method=None).dropna()
    fig = px.histogram(returns, nbins=50, title="Daily Returns Distribution", labels={"value": "Daily Return"}, color_discrete_sequence=["#2ca02c"])
    fig.update_layout(title=dict(font=dict(size=18)), template="plotly_white", showlegend=False, height=400, font=dict(family="Inter, sans-serif", size=13))
    fig.update_xaxes(tickformat=".1%")
    return fig


def plot_benchmark_comparison(fund_nav, bench_nav, fund_name, bench_name):
    """Plot rebased comparison of fund vs benchmark."""
    # Ensure benchmark_nav is a 1D Series
    if hasattr(bench_nav, "squeeze"):
        bench_nav = bench_nav.squeeze()

    # Align and rebase to 100
    df = pd.DataFrame({"fund": fund_nav, "bench": bench_nav}).dropna()
    if df.empty:
        return go.Figure()

    df = (df / df.iloc[0]) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["fund"], name=fund_name, line=dict(color="#1f77b4", width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df["bench"], name=bench_name, line=dict(color="#ff7f0e", width=2, dash="dash")))

    fig.update_layout(
        title=dict(text="Fund vs Benchmark Performance (Rebased to 100)", font=dict(size=18)),
        xaxis_title="Date",
        yaxis_title="Normalized Value",
        template="plotly_white",
        height=450,
        margin=dict(l=20, r=20, t=60, b=100),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        font=dict(family="Inter, sans-serif", size=13),
    )
    return fig


def plot_capture_ratios(capture_dict):
    """Plot bar chart for upside/downside capture."""
    categories = ["Upside Capture", "Downside Capture"]
    values = [capture_dict["upside"], capture_dict["downside"]]

    fig = go.Figure(data=[go.Bar(x=categories, y=values, marker_color=["#2ca02c", "#d62728"])])

    fig.add_hline(y=100, line_dash="dash", line_color="black")

    fig.update_layout(
        title=dict(text="Market Capture Ratios (%)", font=dict(size=18)),
        yaxis_title="Ratio (%)",
        template="plotly_white",
        height=400,
        yaxis=dict(ticksuffix="%"),
        font=dict(family="Inter, sans-serif", size=13),
    )
    return fig


def plot_stress_scenarios(stress_df: pd.DataFrame) -> go.Figure:
    """Plot grouped bar chart for historical stress events."""
    if stress_df.empty:
        return go.Figure()

    plot_df = stress_df.copy()
    # Institutional Labels: Fund and Benchmark
    plot_df = plot_df.rename(columns={"Fund Drop": "Fund", "Benchmark Drop": "Benchmark"})
    plot_df = plot_df.melt(id_vars=["Crisis", "Period"], value_vars=["Fund", "Benchmark"], var_name="Type", value_name="Drop")

    fig = px.bar(
        plot_df,
        x="Crisis",
        y="Drop",
        color="Type",
        barmode="group",
        color_discrete_map={"Fund": "#1f77b4", "Benchmark": "#ff7f0e"},
        text_auto=".1%",
        labels={"Type": ""},
        hover_data={"Period": True},
    )
    fig.update_layout(
        title=dict(text="Historical Stress Scenarios", font=dict(size=18)),
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=100),
        yaxis_title="Peak-to-Trough Decline",
        xaxis_title=None,
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        font=dict(family="Inter, sans-serif", size=13),
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def plot_calendar_returns(cal_df: pd.DataFrame) -> go.Figure:
    """Plot comparative annual returns."""
    if cal_df.empty:
        return go.Figure()

    df_plot = cal_df.copy()
    df_plot.index.name = "Year"
    plot_df = df_plot.reset_index().melt(id_vars="Year", var_name="Type", value_name="Return")

    fig = px.bar(plot_df, x="Year", y="Return", color="Type", barmode="group", color_discrete_sequence=["#1f77b4", "#ff7f0e"], labels={"Return": "Annual Return", "Year": "", "Type": ""}, height=350)
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5), yaxis_title="Annual Return", font=dict(family="Inter, sans-serif", size=13)
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def plot_periodic_metrics(df: pd.DataFrame, is_pct: bool = True, y_label: str = "Metric") -> go.Figure:
    """Plot comparative periodic performance metrics."""
    if df.empty:
        return go.Figure()

    plot_df = df.melt(id_vars="Period", var_name="Type", value_name="Value")
    fig = px.bar(plot_df, x="Period", y="Value", color="Type", barmode="group", color_discrete_sequence=["#1f77b4", "#ff7f0e"], labels={"Type": ""}, height=280)
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        showlegend=True,
        xaxis_title=None,
        yaxis_title=y_label,
        legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5),
        font=dict(family="Inter, sans-serif", size=11),
    )
    if is_pct:
        fig.update_yaxes(tickformat=".0%")
    return fig


def plot_market_sensitivity(df_monthly: pd.DataFrame, benchmark_name: str) -> go.Figure:
    """Plot scatter chart for sensitivity analysis."""
    if df_monthly.empty:
        return go.Figure()

    fig = px.scatter(df_monthly, x="Bench", y="Fund", trendline="ols", title="Monthly Performance Sensitivity", labels={"Bench": f"{benchmark_name} Return", "Fund": "Fund Return"})

    # Add diagonal y=x line
    lims = [min(df_monthly.min()), max(df_monthly.max())]
    fig.add_shape(type="line", x0=lims[0], y0=lims[0], x1=lims[1], y1=lims[1], line=dict(color="gray", dash="dash"))

    fig.update_layout(title=dict(text="Monthly Performance Sensitivity", font=dict(size=18)), height=400, template="plotly_white", font=dict(family="Inter, sans-serif", size=13))
    fig.update_xaxes(tickformat=".0%")
    fig.update_yaxes(tickformat=".0%")
    return fig
