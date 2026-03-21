"""
shared/we_are_here.py — Globaler "We are here!" Marker
========================================================
Zentrale Orientierungshilfe fuer alle Charts.
Zeigt dem User wo er sich zeitlich befindet (aktueller Tag/Monat/TDoM).

Einmal aendern → wirkt auf allen Pages.
"""

# ── Farbe + Stil (zentral anpassbar) ─────────────────

MARKER_COLOR = "rgba(255,215,0,0.55)"
MARKER_COLOR_SOLID = "#FFD700"
ARROW_COLOR = "rgba(255,215,0,0.45)"
BORDER_COLOR = "rgba(255,215,0,0.35)"
BG_COLOR = "rgba(20,28,40,0.4)"
RECT_COLOR = "rgba(255,215,0,0.5)"


def annotation(x_val, y_val, above=True, text="We are here!"):
    """
    Erzeugt eine 'We are here!' Annotation mit Pfeil.
    Halbtransparent damit darunterliegende Daten sichtbar bleiben.

    Args:
        x_val: X-Position (Handelstag, Monat, TDoM etc.)
        y_val: Y-Position (Rendite, Score etc.)
        above: True = Pfeil zeigt nach unten, Text oben
        text: Beschriftungstext

    Returns:
        dict — direkt an fig.add_annotation(**) uebergeben
    """
    return dict(
        x=x_val, y=y_val,
        text=f"<b>{text}</b>",
        showarrow=True,
        arrowhead=2, arrowsize=1.5, arrowwidth=1.5,
        arrowcolor=ARROW_COLOR,
        ax=0, ay=-70 if above else 70,
        font=dict(size=11, color=MARKER_COLOR, family="Inter, sans-serif"),
        bgcolor=BG_COLOR,
        bordercolor=BORDER_COLOR,
        borderwidth=1,
        borderpad=5,
    )


def annotation_offset(x_val, y_val, ax=40, ay=-30, text="We are here!"):
    """
    Annotation mit frei waehlbarem Offset (fuer Heatmaps, Scatter etc.).

    Args:
        x_val, y_val: Position
        ax, ay: Pfeil-Offset in Pixeln
        text: Beschriftungstext
    """
    return dict(
        x=x_val, y=y_val,
        text=text,
        showarrow=True,
        arrowhead=2,
        arrowcolor=ARROW_COLOR,
        ax=ax, ay=ay,
        font=dict(color=MARKER_COLOR, size=11, family="Inter"),
        bordercolor=BORDER_COLOR,
        borderwidth=1,
        borderpad=3,
        bgcolor=BG_COLOR,
    )


def rect(x0, x1, y0, y1):
    """
    Erzeugt ein Highlight-Rechteck (fuer Heatmaps, Balkendiagramme).

    Args:
        x0, x1: X-Bereich
        y0, y1: Y-Bereich

    Returns:
        dict — direkt an fig.add_shape(**) uebergeben
    """
    return dict(
        type="rect",
        x0=x0, x1=x1,
        y0=y0, y1=y1,
        line=dict(color=RECT_COLOR, width=2.5),
        fillcolor="rgba(0,0,0,0)",
        layer="above",
    )


def vline(x_val):
    """
    Vertikale Markierungslinie (z.B. aktueller Handelstag).

    Returns:
        dict — direkt an fig.add_shape(**) uebergeben
    """
    return dict(
        type="line",
        x0=x_val, x1=x_val,
        y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color=RECT_COLOR, width=1.5, dash="dot"),
    )


def star_marker(x_val, y_val):
    """
    Stern-Marker fuer Scatter-Plots (z.B. Spot-Vol Beta).

    Returns:
        dict — direkt an fig.add_trace(go.Scatter(**)) uebergeben
    """
    return dict(
        x=[x_val], y=[y_val],
        mode="markers",
        marker=dict(
            size=14,
            color=MARKER_COLOR_SOLID,
            symbol="star",
            line=dict(width=2, color="white"),
        ),
        name="Heute",
        showlegend=False,
    )
