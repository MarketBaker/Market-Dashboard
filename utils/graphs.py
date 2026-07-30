import plotly.express as px
import plotly.graph_objects as go


def compute_graph(pivot, colors, title, xaxis, yaxis, vertical_line=None):
    fig = go.Figure()
    fallback_colors = px.colors.qualitative.Dark24

    for i, col in enumerate(pivot.columns):
        if col in colors:
            color = colors[col]
        else:
            color = fallback_colors[i % len(fallback_colors)]
        fig.add_trace(
            go.Scatter(
                x=pivot.index,
                y=pivot[col],
                name=col,
                line=dict(color=color),
                mode="lines"
            )
        )

    fig.update_yaxes(
        tickformat=",.2f",
        tickcolor="white",
        gridcolor="#DFDFDF",
        zerolinecolor="black",
        zerolinewidth=2,
        showline=True,
        linewidth=2,
        linecolor="black",
        showgrid=True,
        tickfont=dict(size=15),
        title=dict(text=yaxis, font=dict(size=15)),
        nticks=20
    )
    fig.update_xaxes(
        showgrid=True,
        tickmode="auto",
        tickfont=dict(size=15),
        title=dict(text=xaxis, font=dict(size=15)),
        nticks=20
    )
    fig.update_layout(
        margin=dict(l=0, r=20, t=80, b=80),
        separators=",.0f",
        plot_bgcolor="white",
        height=700,
        barmode="relative",
        title=dict(
            text=title,
            font=dict(size=24)
        ),
        legend=dict(
            font=dict(size=15),
            orientation="h",
            yanchor="top",
            xanchor="center",
            x=0.5
        )
    )

    if vertical_line:
        fig.add_shape(
            type="line",
            x0=vertical_line, x1=vertical_line,
            y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(
                color="grey",
                width=2,
                dash="dash"
            )
        )

    return fig



def compute_graph_dual_axis(df, col1, col2, title, col3 = None):
    fig = go.Figure()

    # Première série (axe Y1)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[col1],
            name=col1,
            mode='lines',
            yaxis="y1",
            line=dict(color="green")
        )
    )

    if col3:
        # Première série (axe Y1)
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col3],
                name=col3,
                mode='lines',
                yaxis="y1",
                line=dict(color="red")
            )
        )

    # Deuxième série (axe Y2)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[col2],
            name=col2,
            mode='lines',
            yaxis="y2",
            line=dict(color="blue")
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Date",
            showgrid=False
        ),

        yaxis=dict(
            title=col1,
            showgrid=False
        ),

        yaxis2=dict(
            title=col2,
            overlaying='y',
            side='right',
            showgrid=False
        ),

        legend=dict(x=0.01, y=0.99)
    )

    return fig


def style_dataframe(df, percent_cols=None, decimals=2):
    """Formatte un DataFrame pour affichage (colonnes en % + arrondi)."""
    percent_cols = percent_cols or []
    fmt = {col: (f"{{:.{decimals}f}}%" if col in percent_cols else f"{{:.{decimals}f}}") for col in df.columns}
    return df.style.format(fmt)

