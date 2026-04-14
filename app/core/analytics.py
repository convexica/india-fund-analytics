from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import streamlit as st

from .logger import get_logger

# Initialize professional logger
logger = get_logger(__name__)


class MFAnalytics:
    """
    A comprehensive financial analytics engine for Mutual Fund performance analysis.

    Provides vectorized calculations for risk-adjusted returns, benchmark comparisons,
    and rolling return distributions.
    """

    def __init__(self, risk_free_rate: float = 0.053):
        """
        Initialize the analytics engine.

        Args:
            risk_free_rate (float): The annual risk-free rate (e.g., 0.053 for 5.3%).
        """
        self.rf = risk_free_rate

    @st.cache_data(show_spinner=False)
    def calculate_cagr(_self, nav_series: pd.Series) -> float:
        """
        Calculate the Compound Annual Growth Rate (CAGR).

        Args:
            nav_series (pd.Series): Time series of Net Asset Values.

        Returns:
            float: The annualized CAGR. Returns 0.0 if data is insufficient.
        """
        if nav_series.empty or len(nav_series) < 2:
            return 0.0

        start_val = nav_series.iloc[0]
        end_val = nav_series.iloc[-1]

        years = (nav_series.index[-1] - nav_series.index[0]).days / 365.25
        if years <= 0:
            return 0.0

        return (end_val / start_val) ** (1 / years) - 1

    @st.cache_data(show_spinner=False)
    def calculate_rolling_returns(_self, nav_series: pd.Series, window_years: int = 1) -> pd.Series:
        """
        Calculate rolling returns for a given time window.

        Args:
            nav_series (pd.Series): Time-series of NAV values.
            window_years (int): The rolling window length in years.

        Returns:
            pd.Series: A series of rolling annualized returns.
        """
        if nav_series.empty:
            return pd.Series(dtype=float)

        # Approx 252 trading days in a year
        window = int(window_years * 252)
        if len(nav_series) < window:
            return pd.Series(dtype=float)

        return (nav_series / nav_series.shift(window)) ** (1 / window_years) - 1

    def calculate_downside_deviation(self, nav_series: pd.Series) -> float:
        """
        Calculate the Annualized Downside Deviation (Semi-variance).

        Measures the volatility of negative returns only, providing a more
        accurate risk metric for asymmetric return distributions.

        Args:
            nav_series (pd.Series): Time-series of NAV values.

        Returns:
            float: Annualized downside deviation.
        """
        if nav_series.empty or len(nav_series) < 2:
            return 0.0

        returns = nav_series.pct_change(fill_method=None).dropna()
        if returns.empty:
            return 0.0

        # Filter only negative returns
        negative_returns = returns[returns < 0]
        sum_sq_negative = (negative_returns**2).sum()

        # Daily downside risk
        downside_risk_daily = np.sqrt(sum_sq_negative / len(returns))
        return downside_risk_daily * np.sqrt(252)

    @st.cache_data(show_spinner=False)
    def calculate_risk_metrics(_self, nav_series: pd.Series, rf_rate: Optional[float] = None) -> Dict[str, float]:
        """
        Compute a comprehensive set of risk-adjusted return metrics.

        Includes Volatility, Sharpe Ratio, Sortino Ratio, Calmar Ratio,
        Omega Ratio, Hurst Exponent, and CAGR.

        Args:
            nav_series (pd.Series): Time-series of NAV values.
            rf_rate (float, optional): Custom risk-free rate. Defaults to instance rf.

        Returns:
            Dict[str, float]: A dictionary containing calculated metrics.
        """
        rf = rf_rate if rf_rate is not None else _self.rf

        if nav_series.empty or len(nav_series) < 2:
            return {}

        returns = nav_series.pct_change(fill_method=None).dropna()
        if returns.empty:
            return {}

        # Basic statistics
        volatility = returns.std() * np.sqrt(252)
        mean_annual_return = returns.mean() * 252
        cagr = _self.calculate_cagr(nav_series)

        # Sharpe Ratio
        excess_return = mean_annual_return - rf
        sharpe = excess_return / volatility if volatility != 0 else 0

        # Sortino Ratio
        downside_dev = _self.calculate_downside_deviation(nav_series)
        sortino = excess_return / downside_dev if downside_dev != 0 else 0

        # Calmar Ratio
        _, max_dd = _self.calculate_drawdowns(nav_series)
        calmar = (cagr / abs(max_dd)) if max_dd != 0 else 0

        # Omega Ratio (Threshold set at rf/252)
        threshold = rf / 252
        gains = returns[returns > threshold].sum()
        losses = abs(returns[returns <= threshold].sum())
        omega = gains / losses if losses != 0 else 0

        # Behavioral Metrics
        hurst = _self.calculate_hurst(nav_series)

        return {
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "downside_deviation": downside_dev,
            "calmar_ratio": calmar,
            "omega_ratio": omega,
            "hurst_exponent": hurst,
            "cagr": cagr,
            "max_drawdown": max_dd,
        }

    def calculate_hurst(self, nav_series: pd.Series) -> float:
        """
        Calculate the Hurst Exponent (H) using Rescaled Range (R/S) methodology.

        Interpretation:
            H = 0.5: Random Walk (Brownian Motion).
            H < 0.5: Mean-Reverting (Anti-persistent).
            H > 0.5: Trending (Persistent).

        Args:
            nav_series (pd.Series): Time-series of NAV values.

        Returns:
            float: The Hurst Exponent. Defaults to 0.5 if data < 100 points.
        """
        if nav_series.empty or len(nav_series) < 100:
            return 0.5

        lags = range(2, 20)
        vals = nav_series.to_numpy()

        # Variance of differences across different lags
        tau = [np.sqrt(np.std(vals[lag:] - vals[:-lag])) for lag in lags]

        # Slope of the log plot log(lags) vs log(tau)
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0] * 2.0

    @st.cache_data(show_spinner=False)
    def calculate_drawdowns(_self, nav_series: pd.Series) -> Tuple[pd.Series, float]:
        """
        Generate the drawdown series and calculate Maximum Drawdown.

        Args:
            nav_series (pd.Series): Time-series of NAV values.

        Returns:
            Tuple[pd.Series, float]: (Drawdown series, Max Drawdown).
        """
        if nav_series.empty:
            return pd.Series(dtype=float), 0.0

        rolling_max = nav_series.cummax()
        drawdown = (nav_series - rolling_max) / rolling_max
        return drawdown, float(drawdown.min())

    @st.cache_data(show_spinner=False)
    def calculate_capture_ratios(_self, fund_nav: pd.Series, benchmark_nav: Union[pd.Series, pd.DataFrame]) -> Dict[str, float]:
        """
        Calculate Upside and Downside Capture Ratios relative to a benchmark.

        Args:
            fund_nav (pd.Series): Time-series of Fund NAV.
            benchmark_nav (pd.Series|pd.DataFrame): Time-series of Benchmark values.

        Returns:
            Dict[str, float]: {'upside': percentage, 'downside': percentage}.
        """
        # Ensure 1D series
        bench_series: pd.Series
        if isinstance(benchmark_nav, pd.DataFrame):
            bench_series = benchmark_nav.iloc[:, 0]
        else:
            bench_series = benchmark_nav

        df = pd.DataFrame({"fund": fund_nav, "bench": bench_series}).dropna()
        if df.empty:
            return {"upside": 0.0, "downside": 0.0}

        # Monthly resampled returns
        monthly_df = df.resample("ME").last().pct_change(fill_method=None).dropna()

        upside_bench = monthly_df[monthly_df["bench"] > 0]
        downside_bench = monthly_df[monthly_df["bench"] <= 0]

        upside_ratio = (upside_bench["fund"].mean() / upside_bench["bench"].mean()) if not upside_bench.empty else 0
        downside_ratio = (downside_bench["fund"].mean() / downside_bench["bench"].mean()) if not downside_bench.empty else 0

        return {"upside": upside_ratio * 100, "downside": downside_ratio * 100}

    @st.cache_data(show_spinner=False)
    def calculate_stress_performance(_self, fund_nav: pd.Series, bench_nav: pd.Series) -> pd.DataFrame:
        """
        Calculate and return peak-to-trough performance during historical market stress events.
        Dynamically handles funds that might not have existed during older crises (like 2008).
        """
        scenarios = [
            {"Name": "2024-25 Market Correction", "Start": "2024-09-27", "End": "2025-04-01"},
            {"Name": "2022 Global Tightening", "Start": "2021-10-18", "End": "2022-06-17"},
            {"Name": "COVID-19 Crash", "Start": "2020-02-19", "End": "2020-03-23"},
            {"Name": "2018 Broad Market Correction", "Start": "2018-01-15", "End": "2018-10-26"},
            {"Name": "2008 Financial Crisis", "Start": "2008-01-08", "End": "2009-03-09"},
        ]

        df = pd.DataFrame({"Fund": fund_nav, "Benchmark": bench_nav}).dropna()
        if df.empty:
            return pd.DataFrame()

        results = []
        for cr in scenarios:
            s_dt = pd.to_datetime(cr["Start"])
            e_dt = pd.to_datetime(cr["End"])

            # Data Validation: Only run if fund and bench have history before crisis starts
            # Adding a tiny buffer (30 days) to prevent edge cases for newly launched funds
            if df.index[0] > (s_dt - pd.Timedelta(days=30)):
                continue

            try:
                # Find accurate trading days closest to the target bounds
                start_mask = df.index >= s_dt
                if not start_mask.any():
                    continue
                start_real = df.index[start_mask][0]

                end_mask = df.index <= e_dt
                if not end_mask.any():
                    continue
                end_real = df.index[end_mask][-1]

                if start_real >= end_real:
                    continue

                f_start, f_end = df.loc[start_real, "Fund"], df.loc[end_real, "Fund"]
                b_start, b_end = df.loc[start_real, "Benchmark"], df.loc[end_real, "Benchmark"]

                f_ret = (f_end / f_start) - 1
                b_ret = (b_end / b_start) - 1

                # Calculate Downside Capture. If benchmark positive (rare in crisis), report N/A
                capture = (f_ret / b_ret) if b_ret < 0 else None

                results.append(
                    {"Crisis": cr["Name"], "Period": f"{start_real.strftime('%b %Y')} - {end_real.strftime('%b %Y')}", "Fund Drop": f_ret, "Benchmark Drop": b_ret, "Capture Ratio": capture}
                )
            except Exception as e:
                logger.warning(f"Error calculating stress scenario for {cr['Name']}: {e}")
                continue

        # Sort by most recent crisis first
        return pd.DataFrame(results)

    @st.cache_data(show_spinner=False)
    def calculate_alpha_beta(_self, fund_nav: pd.Series, benchmark_nav: Union[pd.Series, pd.DataFrame], rf_rate: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate Alpha and Beta using Linear Regression on daily excess returns.

        Formula: Fund_Excess = Alpha + Beta * Bench_Excess

        Args:
            fund_nav (pd.Series): Fund NAV series.
            benchmark_nav (pd.Series|pd.DataFrame): Benchmark price series.
            rf_rate (float, optional): Risk-free rate. Defaults to instance rf.

        Returns:
            Dict[str, float]: Regression outputs (Alpha, Beta, R-Squared, etc.).
        """
        rf = rf_rate if rf_rate is not None else _self.rf
        bench_series: pd.Series
        if isinstance(benchmark_nav, pd.DataFrame):
            bench_series = benchmark_nav.iloc[:, 0]
        else:
            bench_series = benchmark_nav

        df = pd.DataFrame({"fund": fund_nav, "bench": bench_series}).dropna()
        if len(df) < 20:
            return {"alpha": 0.0, "beta": 0.0, "r_squared": 0.0}

        f_ret = df["fund"].pct_change(fill_method=None).dropna()
        b_ret = df["bench"].pct_change(fill_method=None).dropna()

        daily_rf = rf / 252
        f_excess = f_ret - daily_rf
        b_excess = b_ret - daily_rf

        # CAPM Regression
        beta, alpha_daily = np.polyfit(b_excess, f_excess, 1)
        alpha_annual = alpha_daily * 252

        # Stats
        correlation = np.corrcoef(b_excess, f_excess)[0, 1]
        r_squared = correlation**2

        # Information Ratio (Institutional Daily-Annualized)
        active_returns = f_ret - b_ret
        tracking_error = active_returns.std() * np.sqrt(252)
        info_ratio = (active_returns.mean() * 252) / tracking_error if tracking_error != 0 else 0

        # Batting Average (Institutional Monthly Consistency)
        monthly_df = df.resample("ME").last().pct_change(fill_method=None).dropna()
        if not monthly_df.empty:
            batting_avg = (monthly_df["fund"] > monthly_df["bench"]).mean() * 100
        else:
            batting_avg = 0.0

        return {"alpha": alpha_annual, "beta": beta, "r_squared": r_squared, "info_ratio": info_ratio, "batting_average": batting_avg}

    def calculate_fund_multiplier(self, nav_series: pd.Series) -> float:
        """Calculate asset growth multiplier (e.g., 2.5x)."""
        if nav_series.empty:
            return 1.0
        return float(nav_series.iloc[-1] / nav_series.iloc[0])

    def calculate_calendar_returns(self, nav_series: pd.Series) -> pd.Series:
        """Calculate annual returns for each calendar year."""
        if nav_series.empty:
            return pd.Series(dtype=float)

        yearly_nav = nav_series.resample("YE").last()
        returns = yearly_nav.pct_change(fill_method=None)

        # Handle first year (possibly partial)
        if not yearly_nav.empty:
            returns.iloc[0] = (yearly_nav.iloc[0] / nav_series.iloc[0]) - 1

        dt_index = pd.DatetimeIndex(returns.index)
        returns.index = pd.Index(dt_index.year)
        return returns

    @st.cache_data(show_spinner=False)
    def calculate_rolling_return_profile(_self, nav_series: pd.Series, bench_nav_series: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Generate statistical profiles for standard rolling horizons including Outperformance.
        Updated: 2026-04-01 (v2.3.0 Signature Sync)
        """
        profile: Dict[str, Any] = {}
        horizons = {1: "1 Year", 3: "3 Years", 5: "5 Years", 7: "7 Years", 10: "10 Years"}

        for yrs, label in horizons.items():
            rolling = _self.calculate_rolling_returns(nav_series, window_years=yrs).dropna()
            if rolling.empty:
                profile[label] = None
                continue

            # Calculate Outperformance frequency if benchmark is provided
            outperf_pct = 0.0
            if bench_nav_series is not None:
                bench_rolling = _self.calculate_rolling_returns(bench_nav_series, window_years=yrs).dropna()
                # Align both series to find common periods
                common_ix = rolling.index.intersection(bench_rolling.index)
                if not common_ix.empty:
                    outperf_pct = (rolling[common_ix] > bench_rolling[common_ix]).mean()

            profile[label] = {
                "Minimum Return": rolling.min(),
                "Median Return": rolling.median(),
                "Maximum Return": rolling.max(),
                "Outperformance": outperf_pct,
                "% times returns   < -20%": (rolling < -0.20).mean(),
                "% times returns   -20% to -10%": ((rolling >= -0.20) & (rolling < -0.10)).mean(),
                "% times returns   -10% to 0%": ((rolling >= -0.10) & (rolling < 0.00)).mean(),
                "% times returns    0% to 5%": ((rolling >= 0.00) & (rolling < 0.05)).mean(),
                "% times returns    5% to 10%": ((rolling >= 0.05) & (rolling < 0.10)).mean(),
                "% times returns   10% to 15%": ((rolling >= 0.10) & (rolling < 0.15)).mean(),
                "% times returns   15% to 20%": ((rolling >= 0.15) & (rolling < 0.20)).mean(),
                "% times returns   > 20%": (rolling >= 0.20).mean(),
            }
        return profile

    def get_periodic_metrics(self, series: pd.Series, years: int, bench_series: Optional[pd.Series] = None) -> Tuple[Optional[float], Optional[float], Optional[Dict[str, float]]]:
        """
        Calculates performance and risk metrics for a specific multi-year window.
        Moved from UI layer to Engine for SOLID architectural compliance.
        """
        if series.empty:
            return None, None, None
        try:
            target_date = series.index[-1] - pd.DateOffset(years=years)
            subset = series.loc[series.index >= target_date]
            if len(subset) < 20:
                return None, None, None

            start_val = subset.iloc[0]
            end_val = series.iloc[-1]
            ann_ret = (end_val / start_val) ** (1 / years) - 1

            # Annualized Volatility
            daily_rets = subset.pct_change(fill_method=None).dropna()
            ann_vol = daily_rets.std() * np.sqrt(252)

            ratios = {}
            if bench_series is not None and not bench_series.empty:
                b_subset = bench_series.loc[bench_series.index >= target_date]
                if len(b_subset) >= 20:
                    ab = self.calculate_alpha_beta(subset, b_subset)
                    rm = self.calculate_risk_metrics(subset)
                    cap = self.calculate_capture_ratios(subset, b_subset)
                    _, mdd = self.calculate_drawdowns(subset)

                    ratios = {
                        "Alpha": ab["alpha"],
                        "Beta": ab["beta"],
                        "R-Squared": ab["r_squared"],
                        "InfoRatio": ab.get("info_ratio", 0),
                        "BattingAvg": ab.get("batting_average", 0),
                        "Sharpe": rm.get("sharpe_ratio", 0),
                        "Sortino": rm.get("sortino_ratio", 0),
                        "Volatility": ann_vol,
                        "MaxDrawdown": mdd,
                        "Calmar": rm.get("calmar_ratio", 0),
                        "Omega": rm.get("omega_ratio", 0),
                        "Hurst": rm.get("hurst_exponent", 0.5),
                        "Upside": cap["upside"],
                        "Downside": cap["downside"],
                        "CaptureRatio": (cap["upside"] / cap["downside"]) if cap.get("downside", 0) != 0 else 0,
                    }

            return ann_ret, ann_vol, ratios
        except Exception:
            return None, None, None

    def get_monthly_returns(self, fund_nav: pd.Series, bench_nav: pd.Series) -> pd.DataFrame:
        """Alignment and resampling logic for monthly comparative returns."""
        df = pd.DataFrame({"Fund": fund_nav, "Bench": bench_nav}).dropna()
        if df.empty:
            return pd.DataFrame()
        result = df.resample("ME").last().pct_change(fill_method=None).dropna()
        return result if isinstance(result, pd.DataFrame) else pd.DataFrame(result)

    # ═══════════════════════════════════════════════════════════════════
    # PROPRIETARY METRICS ENGINE (v1.2.0)
    # ═══════════════════════════════════════════════════════════════════

    def calculate_convexity_score(self, capture_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convexity Score (Inclusive Multi-Horizon Model):
        Blends capture efficiency across all available forensic windows (1Y, 3Y, 5Y).
        Weighted 50% (3Y), 25% (1Y), 25% (5Y). Rewards structural persistence.
        Target: >1.2 for Highly Convex Asymmetry.
        """
        if not capture_metrics:
            return {"score": 0.0, "ratio": 0.0, "label": "Insufficient History"}

        # Anchor horizons: 1Y, 3Y, 5Y (Fuzzy Matching for robustness)
        weights = {"1": 0.25, "3": 0.50, "5": 0.25}
        composite_ratio = 0.0
        total_weight = 0.0
        persistence_count = 0
        avail_horizons = 0

        for m in capture_metrics:
            p_label = str(m.get("Period", ""))
            upside = m.get("Upside Capture", 0) / 100
            downside = m.get("Downside Capture", 100) / 100
            if downside == 0:
                downside = 0.01  # Floor
            ratio = upside / downside

            # Fuzzy match for '1', '3', or '5' in labels like '1 Yr', '3 Year', etc.
            match_w = 0.0
            if "1" in p_label:
                match_w = weights["1"]
            elif "3" in p_label:
                match_w = weights["3"]
            elif "5" in p_label:
                match_w = weights["5"]

            if match_w > 0:
                composite_ratio += ratio * match_w
                total_weight += match_w
                avail_horizons += 1
                if ratio > 1.0:
                    persistence_count += 1

        # Normalize across available weights
        if total_weight > 0:
            composite_ratio = composite_ratio / total_weight
        else:
            # Absolute fallback: average of every period provided
            ratios = [(m.get("Upside Capture", 0) / (m.get("Downside Capture", 100) or 1)) for m in capture_metrics]
            composite_ratio = sum(ratios) / len(ratios) if ratios else 0.0

        # --- Convexity Persistence Bonus ---
        # Reward structural consistency: If the fund is convex in ALL available horizons,
        # it demonstrates regime-resilience.
        persistence_bonus = 0.0
        if avail_horizons > 1 and persistence_count == avail_horizons:
            persistence_bonus = 0.1  # Reward for structural consistency

        score = round(composite_ratio + persistence_bonus, 2)

        if score > 1.2:
            label = "Structural Asymmetry"
        elif score >= 0.95:
            label = "Persistent Convexity" if persistence_count >= 2 else "Moderate Asymmetry"
        else:
            label = "Linear / Episodic Profile"

        return {"score": score, "ratio": round(composite_ratio, 2), "label": label}

    def calculate_alpha_quality_score(
        self,
        info_ratio: float,
        outperformance_pct: float,
        rolling_alphas: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Composite Alpha Quality Score (0–10):
        - Information Ratio     40%
        - Outperformance Freq   40%
        - Rolling Alpha Persist 20%
        High ≥ 7, Medium 4–7, Low < 4.
        """
        # Normalise IR to 0–10 (cap at IR=2 → 10)
        ir_norm = min(max(info_ratio, 0) / 2.0, 1.0) * 10
        # Outperformance frequency is already 0–1 → scale to 0–10
        op_norm = min(max(outperformance_pct, 0), 1.0) * 10
        # Rolling alpha persistence: consistency of positive alpha
        if rolling_alphas and len(rolling_alphas) >= 3:
            persist = sum(1 for a in rolling_alphas if a > 0) / len(rolling_alphas)
        else:
            persist = 0.5  # neutral if insufficient data
        persist_norm = persist * 10

        score = round(0.40 * ir_norm + 0.40 * op_norm + 0.20 * persist_norm, 1)

        if score >= 7.0:
            label = "High Alpha Quality"
        elif score >= 4.0:
            label = "Medium Alpha Quality"
        else:
            label = "Low Alpha Quality"

        return {"score": score, "label": label}

    def calculate_drawdown_efficiency_ratio(self, cagr: float, max_drawdown: float) -> Dict[str, Any]:
        """
        DER = CAGR / |Max Drawdown|
        Higher = more efficient capital deployment relative to drawdown risk.
        """
        mdd_abs = abs(max_drawdown) if max_drawdown != 0 else 1e-6
        der = round(cagr / mdd_abs, 2)

        if der >= 0.8:
            label = "Efficient Capital Usage"
        elif der >= 0.4:
            label = "Moderate Efficiency"
        else:
            label = "Drawdown-Heavy Strategy"

        return {"score": der, "label": label}

    def calculate_consistency_index(
        self,
        outperformance_pct: float,
        rolling_returns: pd.Series,
    ) -> Dict[str, Any]:
        """
        Consistency Index (0–100):
        Blend of outperformance frequency, rolling return variance, and dispersion.
        Higher score = more repeatable, less episodic return pattern.
        """
        op_score = min(max(outperformance_pct, 0), 1.0) * 40  # max 40 pts
        variance = float(rolling_returns.var()) if not rolling_returns.empty else 1.0
        var_score = max(0, 40 - (variance * 200))  # penalise high variance, max 40 pts
        dispersion = float(rolling_returns.std()) if not rolling_returns.empty else 1.0
        disp_score = max(0, 20 - (dispersion * 100))  # max 20 pts

        score = round(min(op_score + var_score + disp_score, 100), 1)

        if score >= 70:
            label = "Highly Consistent"
        elif score >= 45:
            label = "Above Average"
        elif score >= 25:
            label = "Moderate Consistency"
        else:
            label = "Episodic / Regime-Dependent"

        return {"score": score, "label": label}

    # ═══════════════════════════════════════════════════════════════════
    # MARKET REGIME CLASSIFICATION ENGINE (v1.2.0)
    # Uses Nifty 500 (^CRSLDX) as the sole market proxy — not fund benchmarks.
    # ═══════════════════════════════════════════════════════════════════

    def classify_market_regimes(
        self,
        market_nav: pd.Series,
        fund_nav: pd.Series,
        bench_nav: pd.Series,
    ) -> Dict[str, Any]:
        """
        Classifies market regimes using rolling windows applied to the Nifty 500 index.
        Performance within each regime is then evaluated using Fund vs Benchmark (not market).

        Regime Definitions:
          Bull    : Rolling return > 12% AND max drawdown > -10% AND vol_pct < 70th pct
          Bear    : Peak-to-trough drawdown < -15% AND rolling return < 0%
          Sideways: Everything else (return -5% to +10%, elevated volatility)
        """
        results: Dict[str, Any] = {"horizons": {}, "dominant": "Insufficient Data", "fund_vs_bench": []}

        if market_nav.empty or len(market_nav) < 90:
            return results

        mkt_rets = market_nav.pct_change(fill_method=None).dropna()
        if mkt_rets.empty:
            return results

        # Historical volatility series for percentile computation
        hist_vol = mkt_rets.rolling(63).std() * np.sqrt(252)  # 3M rolling vol
        full_vol_series = hist_vol.dropna()

        horizons = {"3M": 63, "6M": 126, "12M": 252, "36M": 756}
        horizon_results = {}

        for label, window in horizons.items():
            if len(market_nav) < window:
                continue

            mkt_window = market_nav.iloc[-window:]
            fund_window = fund_nav.reindex(mkt_window.index, method="nearest").dropna()
            bench_window = bench_nav.reindex(mkt_window.index, method="nearest").dropna()

            if len(mkt_window) < 20:
                continue

            # --- Market Signals (Nifty 500 only) ---
            mkt_return = float((mkt_window.iloc[-1] / mkt_window.iloc[0]) ** (252 / len(mkt_window)) - 1)
            rolling_max_mkt = mkt_window.cummax()
            mkt_drawdown = float(((mkt_window - rolling_max_mkt) / rolling_max_mkt).min())

            # Realised vol of this window
            win_vol = float(mkt_rets.reindex(mkt_window.index).std() * np.sqrt(252))
            vol_pct = float((full_vol_series <= win_vol).mean() * 100) if not full_vol_series.empty else 50.0

            # --- Regime Classification ---
            if mkt_drawdown <= -0.15 and mkt_return < 0:
                regime = "Bear"
            elif mkt_return >= 0.12 and mkt_drawdown > -0.10 and vol_pct < 70:
                regime = "Bull"
            else:
                regime = "Sideways"

            # --- Confidence Score (3-signal voting) ---
            votes = 0
            if regime == "Bull":
                if mkt_return >= 0.12:
                    votes += 1
                if mkt_drawdown > -0.10:
                    votes += 1
                if vol_pct < 70:
                    votes += 1
            elif regime == "Bear":
                if mkt_drawdown <= -0.15:
                    votes += 1
                if mkt_return < 0:
                    votes += 1
                votes += 1  # Bear always at least 2/3 by definition
            else:
                votes = 2  # Sideways = moderate confidence by default

            confidence_map = {3: "High", 2: "Medium", 1: "Low"}
            confidence = confidence_map.get(votes, "Low")

            # --- Fund Performance in this regime ---
            fund_ret: Optional[float] = None
            bench_ret: Optional[float] = None
            excess: Optional[float] = None
            behavior = "Insufficient Data"

            if len(fund_window) >= 20 and len(bench_window) >= 20:
                fund_ret = float((fund_window.iloc[-1] / fund_window.iloc[0]) ** (252 / len(fund_window)) - 1)
                bench_ret = float((bench_window.iloc[-1] / bench_window.iloc[0]) ** (252 / len(bench_window)) - 1)
                excess = round(fund_ret - bench_ret, 4)

                if excess > 0.03:
                    behavior = "Alpha-generative" if regime != "Bear" else "Defensive"
                elif excess > 0:
                    behavior = "Outperforming"
                elif excess > -0.03:
                    behavior = "Lagging"
                else:
                    behavior = "Significantly Lagging"

            horizon_results[label] = {
                "regime": regime,
                "confidence": confidence,
                "mkt_return": round(mkt_return, 4),
                "mkt_drawdown": round(mkt_drawdown, 4),
                "vol_percentile": round(vol_pct, 1),
                "fund_return": round(fund_ret, 4) if fund_ret is not None else None,
                "bench_return": round(bench_ret, 4) if bench_ret is not None else None,
                "excess_return": excess,
                "behavior": behavior,
            }

        results["horizons"] = horizon_results

        # Dominant regime = 12M if available, else latest horizon
        if "12M" in horizon_results:
            results["dominant"] = horizon_results["12M"]["regime"]
            results["dominant_confidence"] = horizon_results["12M"]["confidence"]
        elif horizon_results:
            last_key = list(horizon_results.keys())[-1]
            results["dominant"] = horizon_results[last_key]["regime"]
            results["dominant_confidence"] = horizon_results[last_key]["confidence"]

        return results

    def generate_ai_report_markdown(
        self,
        fund_name: str,
        benchmark_name: str,
        deep_metrics: List[dict],
        rolling_profiles: dict,
        stress_df: Optional[pd.DataFrame] = None,
        proprietary_metrics: Optional[Dict[str, Any]] = None,
        regime_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        AI SYNTHESIS ENGINE (v1.2.0 — CIO-Grade Investment Memo)
        ----------------------------------------------------------
        Upgraded to a 7-section institutional memo framework:
          [INVESTMENT_VIEW] [DIAGNOSTICS] [PROPRIETARY_METRICS]
          [REGIME_ANALYSIS] [PORTFOLIO_ROLE] [ALLOCATION_GUIDANCE]
          [RISK_CONSIDERATIONS]

        Key v1.2.0 improvements:
        - Pre-computed proprietary metrics injected as hard numbers (AI interprets, not calculates)
        - Market Regime data from Nifty 500 included for regime-aware synthesis
        - Strict language governance: banned retail keywords, mandated institutional vocabulary
        - CIO hedge-fund-memo persona with 7-section deterministic output format
        """
        if stress_df is None:
            stress_df = pd.DataFrame()
        if proprietary_metrics is None:
            proprietary_metrics = {}
        if regime_data is None:
            regime_data = {}

        report = [
            "# ROLE",
            "You are a CIO-level investment analyst generating a hedge-fund-style fund evaluation. "
            "You write like a senior portfolio manager presenting to an investment committee. "
            "Every statement must be defensible by the provided quantitative data.",
            "\n# LANGUAGE GOVERNANCE — MANDATORY",
            "BANNED WORDS (never use): strong, good, effective, great, excellent, impressive, robust, SIP, " "stop-loss, buy, sell, invest",
            "PREFERRED VOCABULARY: structural, persistent, asymmetric, repeatable, drawdown-sensitive, " "regime-dependent, alpha-generating, defensive, episodic, conviction",
            "\n# OBJECTIVE",
            f"Generate a structured investment memo for **{fund_name}** " f"benchmarked against **{benchmark_name}**.",
            "\n# INPUT DATA",
            "## Performance Grid (1Y, 3Y, 5Y Horizons)",
            "| Period | Sharpe | Sortino | Info Ratio | Alpha | Beta | Batting Avg | Upside | Downside |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for m in deep_metrics:
            report.append(
                f"| {m.get('Period', 'N/A')} | {m.get('Sharpe', 0):.2f} | "
                f"{m.get('Sortino', 0):.2f} | {m.get('Info Ratio', 0):.2f} | "
                f"{m.get('Jensen Alpha', 0):.1%} | {m.get('Beta', 0):.2f} | "
                f"{m.get('Batting Avg', 0):.0%} | "
                f"{m.get('Upside Capture', 0):.0%} | {m.get('Downside Capture', 0):.0%} |"
            )

        report.extend(
            [
                "\n## Rolling Return Profiles",
                "| Window | Median | Max | Min | Outperformance % |",
                "| :--- | :--- | :--- | :--- | :--- |",
            ]
        )
        for label, stats in rolling_profiles.items():
            if isinstance(stats, dict):
                report.append(
                    f"| {label} | {stats.get('Median Return', 0):.1%} | "
                    f"{stats.get('Maximum Return', 0):.1%} | "
                    f"{stats.get('Minimum Return', 0):.1%} | "
                    f"{stats.get('Outperformance', 0):.0%} |"
                )

        report.extend(
            [
                "\n## Historical Stress Scenarios",
                "| Crisis | Fund | Benchmark | Capture |",
                "| :--- | :--- | :--- | :--- |",
            ]
        )
        if not stress_df.empty:
            for _, row in stress_df.iterrows():
                cap_val = row.get("Capture Ratio", "-")
                cap_str = f"{cap_val:.0%}" if isinstance(cap_val, (int, float)) else "-"
                report.append(f"| {row['Crisis']} | {row['Fund Drop']:.1%} | " f"{row['Benchmark Drop']:.1%} | {cap_str} |")
        else:
            report.append("| No crisis history available | - | - | - |")

        # Proprietary Metrics Block (pre-computed — AI interprets, not calculates)
        if proprietary_metrics:
            cs = proprietary_metrics.get("convexity_score", {})
            aq = proprietary_metrics.get("alpha_quality", {})
            dr = proprietary_metrics.get("der", {})
            ci = proprietary_metrics.get("consistency_index", {})
            report.extend(
                [
                    "\n## Proprietary Metrics (Pre-Computed — Do NOT Recalculate)",
                    f"- Convexity Score: {cs.get('ratio', 'N/A')} ({cs.get('label', 'N/A')})",
                    f"- Alpha Quality Score: {aq.get('score', 'N/A')}/10 ({aq.get('label', 'N/A')})",
                    f"- Drawdown Efficiency Ratio (DER): {dr.get('score', 'N/A')} " f"({dr.get('label', 'N/A')})",
                    f"- Consistency Index: {ci.get('score', 'N/A')}/100 ({ci.get('label', 'N/A')})",
                ]
            )

        # Regime Block
        if regime_data and regime_data.get("horizons"):
            dom = regime_data.get("dominant", "N/A")
            dom_conf = regime_data.get("dominant_confidence", "N/A")
            report.extend(
                [
                    f"\n## Market Regime Data (Nifty 500 — Dominant 12M Regime: {dom} [{dom_conf} Confidence])",
                    "| Horizon | Regime | Confidence | Fund Return | Benchmark | Excess | Behavior |",
                    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
                ]
            )
            for hz, hd in regime_data["horizons"].items():
                fr = f"{hd['fund_return']:.1%}" if hd.get("fund_return") is not None else "N/A"
                br = f"{hd['bench_return']:.1%}" if hd.get("bench_return") is not None else "N/A"
                ex = f"{hd['excess_return']:.1%}" if hd.get("excess_return") is not None else "N/A"
                report.append(f"| {hz} | {hd['regime']} | {hd['confidence']} | {fr} | {br} | {ex} | " f"{hd['behavior']} |")

        report.extend(
            [
                "\n# OUTPUT FORMAT — MANDATORY",
                "Return the analysis ONLY using the 7 TAGS below in this exact order.",
                "Do NOT use markdown headers (#, ##). Do NOT use the banned words listed above.",
                "The app renders each tag as a separate UI section.",
                "\n[INVESTMENT_VIEW]",
                "2–3 sentences. State: (1) what the fund is structurally, " "(2) its primary role in a portfolio, (3) its structural edge or deficit.",
                "\n[DIAGNOSTICS]",
                "4 sub-sections. Each bullet starts with **Bold Sub-Header:**",
                "Sub-sections: **Downside Participation & Asymmetry:** | " "**Return Consistency:** | **Risk-Adjusted Efficiency:** | **Alpha Quality:**",
                "\n[PROPRIETARY_METRICS]",
                "One interpretation sentence per metric. Reference the pre-computed values above. " "Do NOT recalculate. Format: **Metric Name (Value):** interpretation.",
                "\n[REGIME_ANALYSIS]",
                "Describe fund behaviour across regime windows from the data above. " "Identify where the fund outperforms or underperforms structurally.",
                "\n[PORTFOLIO_ROLE]",
                "State Core / Satellite / Hedge and explain fit. " "What does it complement? What does it not replace?",
                "\n[ALLOCATION_GUIDANCE]",
                "Qualitative portfolio weight context only. No specific percentages. " "Reference portfolio construction principles (diversification, risk budget, regime fit).",
                "\n[RISK_CONSIDERATIONS]",
                "3 bullets minimum. Cover: (1) when the strategy structurally fails, " "(2) style/factor biases, (3) regime or concentration risk.",
                "\n---",
                "Write with precision. Every claim must reference a metric from the data above.",
            ]
        )

        return "\n".join(report)

    def generate_live_report(self, markdown_brief: str) -> str:
        """
        Attempts to generate a live analytical report by calling Groq or Gemini API directly.
        Uses st.secrets for secure key management and prioritizes Groq for speed/privacy.
        """
        import streamlit as st

        # 1. Groq Implementation: Priority for speed and Llama-3 accuracy
        if "GROQ_API_KEY" in st.secrets:
            try:
                from groq import Groq

                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                logger.info("Executing Groq request (llama-3.3-70b-versatile)...")
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional investment analyst. Use the provided quantitative data to generate a multi-section markdown report.",
                        },
                        {"role": "user", "content": markdown_brief},
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.4,
                )
                return str(chat_completion.choices[0].message.content)
            except Exception as e:
                logger.warning(f"Groq generation failed, falling back to Gemini: {e}")

        # 2. Gemini Implementation: Generous free tier
        if "GEMINI_API_KEY" in st.secrets:
            try:
                import google.generativeai as genai

                logger.info("Executing Gemini request (gemini-2.0-flash)...")
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(markdown_brief)
                return response.text
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}")
                return f"⚠️ **AI Execution Error:** {e}\n\nFalling back to the briefing below for manual analysis."

        # 3. Fallback: Return a helpful message if no keys are configured
        return (
            "⚠️ **Live Agent Offline:** No API keys (GROQ_API_KEY or GEMINI_API_KEY) found in Streamlit Secrets.\n\n"
            "### Instructions for Activation:\n"
            "1. Open your Streamlit Dashboard Settings.\n2. Go to **Secrets**.\n"
            '3. Add your key: `GROQ_API_KEY = "your_key"`.\n\n'
            "**Analyst Briefing:** (Copy the code block below to your preferred assistant)"
        )

    def generate_chat_response(self, messages: List[Dict[str, str]], context_brief: Optional[str] = None) -> str:
        """
        Conversational engine for ConvexAI.
        Processes chat history and optional quant context to provide senior-analyst level responses.
        """
        import streamlit as st

        # 🛸 SYSTEM PROMPT — The Soul of ConvexAI
        system_prompt = (
            "# ROLE\n"
            "You are **ConvexAI**, a state-of-the-art investment strategist and quantitative analyst at Convexica. "
            "You deliver institutional-grade analysis of Indian mutual funds for sophisticated investors and fiduciaries.\n\n"
            "# OBJECTIVE\n"
            "Provide high-conviction, data-driven insights that help users evaluate mutual funds through:\n"
            "- Risk-adjusted performance\n"
            "- Downside behavior\n"
            "- Structural consistency\n"
            "- Portfolio role suitability\n\n"
            "# DOMAIN EXPERTISE (ASSUMED)\n"
            "- SEBI mutual fund classifications\n"
            "- Indian taxation (LTCG, STCG, indexation where applicable)\n"
            "- Advanced risk metrics: Sharpe, Sortino, Calmar, Alpha, Beta, Capture Ratios\n"
            "- Market regime analysis (inflation, liquidity, rate cycles)\n\n"
            "# CORE OPERATING RULES\n\n"
            "## 1. Professional Persona\n"
            "- Tone: precise, analytical, and authoritative\n"
            "- Audience: HNIs, wealth managers, portfolio managers\n"
            "- Avoid retail language (“safe”, “great fund”)\n"
            "- Prefer: “drawdown-sensitive”, “alpha persistence”, “risk asymmetry”\n\n"
            "## 2. No Direct Investment Advice\n"
            "- Never issue “buy/sell/recommend” statements\n"
            "- If prompted, respond with:\n"
            "  > “My role is to provide quantitative forensics to support your decision-making process.”\n"
            "- Reframe advice requests into strategic evaluation\n\n"
            "## 3. Data-Driven Reasoning\n"
            "- Anchor every conclusion to explicit data\n"
            "- If **context_brief** is provided:\n"
            "  - Treat it as the primary dataset\n"
            "  - Explain *why* the fund behaves as observed (not just what)\n"
            "- If data is missing or insufficient:\n"
            "  - Explicitly state the limitation\n"
            "  - Do not infer or hallucinate\n\n"
            "## 4. Analytical Priorities\n"
            "Always bias analysis toward:\n"
            "- Downside protection over raw returns\n"
            "- Consistency over point performance\n"
            "- Risk-adjusted alpha over absolute returns\n"
            "- Regime behavior over static averages\n\n"
            "## 5. Concept Explanation Mode\n"
            "If asked about a concept:\n"
            "- Define it quantitatively and concisely\n"
            "- Include interpretation (what is “good” vs “poor”)\n"
            "- Example:\n"
            "  “Sharpe Ratio = excess return per unit of volatility; higher indicates more efficient risk-taking.”\n\n"
            "# RESPONSE STRUCTURE (DEFAULT)\n\n"
            "## When analyzing a fund:\n"
            "1. **Summary Insight (2–3 lines)**\n"
            "   Clear, high-level judgment of the fund’s character\n\n"
            "2. **Quantitative Interpretation**\n"
            "   - Risk & drawdown profile\n"
            "   - Return consistency\n"
            "   - Risk-adjusted metrics\n\n"
            "3. **Behavioral Diagnosis**\n"
            "   - When the fund outperforms/underperforms\n"
            "   - Regime sensitivity\n\n"
            "4. **Strategic Role**\n"
            "   - Where it fits in a portfolio (e.g., core, satellite, defensive diversifier)\n\n"
            "## When answering general queries:\n"
            "- Provide structured, insight-dense responses\n"
            "- Use frameworks instead of opinions\n\n"
            "# STYLE & FORMAT\n"
            "- Use Markdown (headers, bullet points, tables when useful)\n"
            "- Be concise but information-dense\n"
            "- No fluff, no repetition\n\n"
            "# OUTPUT STANDARD\n"
            "Every response must:\n"
            "- Contain at least one non-obvious insight\n"
            "- Be defensible with data or financial logic\n"
            "- Reflect institutional-quality thinking"
        )

        if context_brief:
            system_prompt += f"\n\n### CONTEXT FOR CURRENT FUND BEING VIEWED:\n{context_brief}"

        # Insert system prompt at the beginning of the message history
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        # 1. Groq Implementation
        if "GROQ_API_KEY" in st.secrets:
            try:
                from groq import Groq

                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                logger.info("Executing ConvexAI chat request (Groq)...")
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=full_messages,  # type: ignore
                    temperature=0.4,
                    max_tokens=2048,
                )
                return str(completion.choices[0].message.content)
            except Exception as e:
                logger.warning(f"ConvexAI Groq fallthrough: {e}")

        # 2. Gemini Implementation
        if "GEMINI_API_KEY" in st.secrets:
            try:
                import google.generativeai as genai

                logger.info("Executing ConvexAI chat request (Gemini)...")
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("gemini-2.0-flash")

                # Convert message format for Gemini
                gemini_history = []
                for m in messages[:-1]:  # All but the last as history
                    role = "user" if m["role"] == "user" else "model"
                    gemini_history.append({"role": role, "parts": [{"text": m["content"]}]})

                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(messages[-1]["content"])
                return response.text
            except Exception as e:
                logger.error(f"ConvexAI Gemini failure: {e}")
                return "I am currently experiencing a localized core synchronization failure. Please retrieve the analyst briefing for manual forensics."

        return "🔒 **ConvexAI Core Offline:** Please configure GROQ_API_KEY or GEMINI_API_KEY in the dashboard secrets to activate the strategist."
