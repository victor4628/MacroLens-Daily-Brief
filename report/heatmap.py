import base64
from io import BytesIO


def generate_sector_heatmap(sector_performance: list[dict]) -> str:
    """
    Generate a sector performance heatmap (1D / 5D / 1M).
    Returns a base64-encoded PNG data URI for embedding in HTML.
    Returns empty string if matplotlib is unavailable or data is missing.
    """
    if not sector_performance:
        return ""

    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        import numpy as np
    except ImportError:
        return ""

    # Sort by 1M return descending (already sorted by fetcher, but be safe)
    data = sorted(sector_performance, key=lambda x: x["return_1m"], reverse=True)

    sectors  = [s["sector"] for s in data]
    returns  = {
        "1D":  [s["return_1d"] for s in data],
        "5D":  [s["return_5d"] for s in data],
        "1M":  [s["return_1m"] for s in data],
    }

    matrix = np.array([returns["1D"], returns["5D"], returns["1M"]]).T  # (n_sectors, 3)

    fig, ax = plt.subplots(figsize=(7, len(sectors) * 0.55 + 1.2))
    fig.patch.set_facecolor("#ffffff")

    # Red → white → green colormap
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "rg", ["#c0392b", "#f5f5f5", "#27ae60"]
    )

    # Symmetric normalization centred on 0
    max_abs = max(abs(matrix).max(), 2.0)
    norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0, vmax=max_abs)

    ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")

    # Axis labels
    ax.set_xticks(range(3))
    ax.set_xticklabels(["1D", "5D", "1M"], fontsize=11, fontweight="bold", color="#1a1a2e")
    ax.set_yticks(range(len(sectors)))
    ax.set_yticklabels(sectors, fontsize=10, color="#1a1a2e")
    ax.xaxis.tick_top()
    ax.tick_params(length=0)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Cell values
    for i in range(len(sectors)):
        for j, col in enumerate(["1D", "5D", "1M"]):
            val = matrix[i][j]
            # use white text on dark cells, dark text on light cells
            text_color = "white" if abs(val) > max_abs * 0.55 else "#1a1a2e"
            ax.text(
                j, i, f"{val:+.1f}%",
                ha="center", va="center",
                fontsize=9, fontweight="bold", color=text_color,
            )

    ax.set_title("Sector Performance Heatmap", fontsize=12,
                 fontweight="bold", color="#0f3460", pad=14)

    plt.tight_layout(pad=0.5)

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)

    b64 = base64.b64encode(buf.read()).decode()
    return f"data:image/png;base64,{b64}"
