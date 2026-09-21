"""
Plotting helpers: spark spread against a threshold, the ideal->optimal
value waterfall, and Monte Carlo distributions.
"""

import matplotlib.pyplot as plt
import numpy as np


def plot_series_vs_threshold(x, y, threshold=0, title="", ylabel="",
                             figsize=(14, 4)):
    """
    Plot a time series, shading where it lies above/below a threshold
    (green above, red below) with a reference line.
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(x, y, linewidth=0.5, color="steelblue")
    ax.axhline(threshold, color="black", linewidth=0.8)
    ax.fill_between(x, y, threshold, where=(y < threshold),
                    color="red", alpha=0.3, interpolate=True)
    ax.fill_between(x, y, threshold, where=(y >= threshold),
                    color="green", alpha=0.3, interpolate=True)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    return fig, ax



def plot_value_waterfall(*, spark_spread, is_on, capacity,
                         n_startups, switch_on_cost,
                         value_optimal_dp=None, figsize=(10, 6)):
    """
    Waterfall from the ideal (unconstrained) margin to the constrained
    optimum, breaking down the gap into its three sources:
      * profit foregone -- profitable hours the plant is kept off;
      * run at loss     -- unprofitable hours the plant is forced to run;
      * start-up costs.
    The always-on margin is shown alongside for reference.

    Parameters
    ----------
    spark_spread : array-like, hourly spark spread (EUR/MWh).
    is_on : array-like of bool, the optimal dispatch profile.
    capacity : float, plant capacity (MW).
    n_startups : int, number of start-ups in the optimal dispatch.
    switch_on_cost : float, cost per start-up (EUR).
    value_optimal_dp : float, optional. If given, the reconstructed
        optimum is checked against it (the DP value).
    """
    spark = np.asarray(spark_spread, dtype=float)
    is_on = np.asarray(is_on, dtype=bool)


    value_ideal     = (spark[spark > 0] * capacity).sum()
    profit_foregone = (spark[(spark > 0) & ~is_on] * capacity).sum()
    loss_running    = -(spark[(spark <= 0) & is_on] * capacity).sum()   # >= 0
    startup_total   = n_startups * switch_on_cost
    value_optimal   = value_ideal - profit_foregone - loss_running - startup_total
    value_naive     = (spark * capacity).sum()   # always ON: every hour, losses included


    if value_optimal_dp is not None:
        assert abs(value_optimal - value_optimal_dp) < 1.0, (
            f"decomposition {value_optimal:,.0f} != DP {value_optimal_dp:,.0f}"
        )

    labels = ["Ideal\n(unconstrained)", "Profit\nforegone", "Run\nat loss",
              "Start-up\ncosts", "Optimal\n(constrained)", "Always on"]
    heights = [value_ideal, profit_foregone, loss_running, startup_total,
               value_optimal, value_naive]
    colors = ["steelblue", "indianred", "indianred", "indianred", "seagreen", "slategray"]

    # running level carried from one step to the next (top of each delta bar)
    levels = [
        value_ideal,
        value_ideal - profit_foregone,
        value_ideal - profit_foregone - loss_running,
        value_optimal
    ]
    bottoms = [0, levels[1], levels[2], levels[3], 0, 0]

    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(len(labels))
    ax.bar(x, heights, bottom=bottoms, color=colors, width=0.6)

    # dashed connectors between consecutive bars
    for k in range(4):
        ax.plot([x[k] + 0.3, x[k + 1] - 0.3], [levels[k], levels[k]],
                color="grey", linewidth=0.8, linestyle="--")

    # per-bar value labels (deltas signed, totals unsigned)
    signed = [value_ideal, -profit_foregone, -loss_running, -startup_total,
              value_optimal, value_naive]
    tops = [value_ideal, levels[0], levels[1], levels[2], value_optimal, value_naive]
    for xi, s, top in zip(x, signed, tops):
        ax.text(xi, top + value_ideal * 0.012, f"{s / 1e6:.2f}M",
                ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Gross margin (€)")
    ax.set_title("Gross margin: ideal → constrained optimum")
    ax.set_ylim(0, value_ideal * 1.10)
    return fig, ax


def plot_distribution(values, *, title="", xlabel="", bins=40):
    """
    Histogram of simulated values, with the mean and the 5th/95th
    percentiles marked.
    """
    values = np.asarray(values)
    mean = values.mean()
    p5, p95 = np.percentile(values, [5, 95])

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(values, bins=bins, color="steelblue", edgecolor="white")
    ax.axvline(mean, color="black", linestyle="--", linewidth=1, label=f"mean {mean:,.0f}")
    ax.axvline(p5, color="red", linestyle=":", linewidth=1, label="5th pct")
    ax.axvline(p95, color="red", linestyle=":", linewidth=1, label="95th pct")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequency")
    ax.legend()
    return fig, ax
