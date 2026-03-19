# Migrationspfad — SeasonalEdge

## Phasen

```
Phase 1 (jetzt):     Streamlit stabilisieren + Deployment
Phase 2 (~500 User): Next.js Landingpage (SEO + Newsletter)
Phase 3 (~Wachstum): FastAPI-Backend für Berechnungslogik
Phase 4 (>500 Abo):  Vollmigration Next.js + Highcharts
```

## Ziel-Stack (Phase 4)

```
Frontend:  Next.js 14+, React 18, TailwindCSS, shadcn/ui, Highcharts 11+
Backend:   FastAPI 0.100+, Python 3.11+, Pydantic, SQLAlchemy, Supabase
KI:        LSTM, XGBoost, Transformer, Claude API
Services:  Stripe, Brevo, GitHub Actions, Sentry, Docker
Deploy:    Vercel (Next.js), Railway/Fly.io (FastAPI), Supabase (DB/Auth)
```

## Highcharts vs. Plotly

| Feature | Plotly (aktuell) | Highcharts (Ziel) |
|---------|-----------------|-------------------|
| Lizenz | Open Source | Commercial (~400 EUR/Jahr) |
| Dual Y-Axis | `yaxis2` + `overlaying:"y"` | `yAxis: [{}, {opposite:true}]` |
| Clip/Split | Manuell via CSS clip-path | Nativ: `plotBands` + Custom Renderer |
| Bundle Size | ~3MB | ~1MB (tree-shakeable) |
| SSR | Eingeschränkt | Vollständig via `highcharts/node` |

## Timing

- Next.js Landingpage: Sofort (SEO-Vorteil)
- FastAPI Backend: Ab ~100 täglichen Nutzern
- Highcharts: Ab ~500 zahlenden Abonnenten
