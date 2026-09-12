import matplotlib.pyplot as plt


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