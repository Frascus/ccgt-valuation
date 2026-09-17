import matplotlib.pyplot as plt
import numpy as np


def plot_series_vs_threshold(x, y, threshold=0, title="", ylabel="",
                             figsize=(14, 4)):
    """
    Plot a time series, highlighting where it lies above/below a
    threshold (green above, red below) with a reference line.
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
    Waterfall showing the difference between the ideal strategy and the 
    optimal one with constrains. Breaking down the different causes of the
    difference.
    The three different source of loss due to the constraints are:
    * turbine off when would be profitable
    * run at loss when unprofitable
    * start up costs.
    Parameters
    ----------
    spark_spread : array-like, hourly spark spread (EUR/MWh).
    is_on : array-like di bool, optimal dispatch.
    capacity : float, turbine power (MW).
    n_startups : int, number of start ups with the optimal dispatch.
    switch_on_cost : float, cost associated to each startup (EUR).
    value_optimal_dp : float, optional. the total optimal yearly profits:
        if present, the function checks that the total is reconstructed.
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
            f"scomposizione {value_optimal:,.0f} != DP {value_optimal_dp:,.0f}"
        )

    labels = ["Ideal profits\n(unconstrained)", "Profit \nforegone", "Run \nat loss",
              "Start up\ncosts", "Optimal profits\n (constrained)", "profits if\n always ON"]
    heights = [value_ideal, profit_foregone, loss_running, startup_total,
               value_optimal, value_naive]
    colors = ["steelblue", "indianred", "indianred", "indianred", "seagreen", "slategray"]

    # livelli portati da un gradino al successivo (top di ciascuna barra "delta")
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

    # connettori tratteggiati tra barre consecutive
    for k in range(4):
        ax.plot([x[k] + 0.3, x[k + 1] - 0.3], [levels[k], levels[k]],
                color="grey", linewidth=0.8, linestyle="--")

    # etichette con il valore di ciascuna barra (delta col segno, totali senza)
    signed = [value_ideal, -profit_foregone, -loss_running, -startup_total,
              value_optimal, value_naive]
    tops = [value_ideal, levels[0], levels[1], levels[2], value_optimal, value_naive]
    for xi, s, top in zip(x, signed, tops):
        ax.text(xi, top + value_ideal * 0.012, f"{s / 1e6:.2f}M",
                ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("value (€)")
    ax.set_title("From unconstrained profits to optimal constraint profits")
    ax.set_ylim(0, value_ideal * 1.10)
    return fig, ax
