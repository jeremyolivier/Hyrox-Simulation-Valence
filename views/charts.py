import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde

from views.data import CATEGORY_COLORS, CATEGORY_LABELS, hex_to_rgba

CHART_CONFIG = {"displayModeBar": False, "scrollZoom": False}


def _hms(total) -> str:
    hours, remainder = divmod(int(total), 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def kde_by_category(
        values_by_category: dict,
        highlight: tuple[str, int] | None = None,
        x_title: str = "Temps",
) -> go.Figure:
    """KDE des temps par catégorie (M/F/Mx), rug et moyennes verticales.

    Courbe, rug et moyenne d'une catégorie partagent un ``legendgroup`` : un
    clic sur la légende les masque/affiche ensemble.
    """
    codes = [
        code for code in CATEGORY_LABELS
        if len(values_by_category.get(code, []))
    ]

    all_values = (
        np.concatenate([np.asarray(values_by_category[code]) for code in codes])
        if codes
        else np.array([0.0])
    )

    x_grid = np.linspace(all_values.min(), all_values.max(), 200)
    x_labels = [_hms(value) for value in x_grid]

    plottable = []
    for code in codes:
        data = np.asarray(values_by_category[code])

        if len(data) >= 2 and np.unique(data).size > 1:
            density = gaussian_kde(data)(x_grid)
            plottable.append((code, data, density, float(np.mean(data))))

    max_density = max((density.max() for _, _, density, _ in plottable), default=1.0)
    rug_step = max_density * 0.06

    fig = go.Figure()

    for code, _data, density, mean in plottable:
        label = CATEGORY_LABELS[code]
        color = CATEGORY_COLORS[code]

        fig.add_scatter(
            x=x_grid,
            y=density,
            name=label,
            legendgroup=code,
            mode="lines",
            line={"color": color, "width": 2},
            fill="tozeroy",
            fillcolor=hex_to_rgba(color, 0.18),
            customdata=x_labels,
            hovertemplate=f"<b>{label}</b><br>%{{customdata}}<extra></extra>",
        )

        fig.add_scatter(
            x=[mean, mean],
            y=[0, max_density * 1.05],
            legendgroup=code,
            showlegend=False,
            mode="lines+text",
            line={"color": color, "width": 1.5, "dash": "dash"},
            text=["", f"Moyenne {_hms(mean)}"],
            textposition="top center",
            textfont={"color": color, "size": 10},
            hovertemplate=f"Moyenne {label}<br>{_hms(mean)}<extra></extra>",
        )

    for index, (code, data, _density, _mean) in enumerate(plottable):
        fig.add_scatter(
            x=data,
            y=np.full(len(data), -rug_step * (index + 1)),
            legendgroup=code,
            showlegend=False,
            mode="markers",
            marker={
                "symbol": "line-ns-open",
                "color": CATEGORY_COLORS[code],
                "size": 8,
            },
            hoverinfo="skip",
        )

    if highlight is not None:
        label, seconds = highlight
        fig.add_vline(
            x=seconds,
            line_color="#7C3AED",
            line_width=2.5,
            annotation_text=f"{label} · {_hms(seconds)}",
            annotation_position="top left",
            annotation_font={"color": "#7C3AED", "size": 12},
        )

    ticks = np.linspace(all_values.min(), all_values.max(), num=8)

    fig.update_xaxes(
        tickmode="array",
        tickvals=ticks,
        ticktext=[_hms(value) for value in ticks],
        showgrid=False,
        ticks="outside",
        tickcolor="rgba(0, 0, 0, 0.15)",
    )

    fig.update_yaxes(
        showticklabels=False,
        showgrid=False,
        zeroline=True,
        zerolinecolor="rgba(0, 0, 0, 0.15)",
        range=[-rug_step * (len(plottable) + 1), max_density * 1.28],
    )

    fig.update_layout(
        uirevision="categories",
        xaxis_title=x_title,
        yaxis_title="Densité d'équipes",
        height=480,
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        font={
            "family": "system-ui, -apple-system, sans-serif",
            "color": "#1F2937",
        },
        hoverlabel={
            "bgcolor": "white",
            "bordercolor": "rgba(0, 0, 0, 0.1)",
            "font_size": 13,
        },
        legend={
            "title": "Catégorie",
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "groupclick": "togglegroup",
        },
    )

    return fig
