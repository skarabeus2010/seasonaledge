# apply_i18n_attributes.ps1
# Adds data-i18n attributes to HTML elements across all landing pages.
# Safe to run multiple times (patterns include the full original tag, so already-replaced
# elements won't match).

param([switch]$DryRun)

$htmlFiles = @(Get-ChildItem "c:\dev\Seasonaledge\landing\pages\*.html" -File)
$htmlFiles += Get-Item "c:\dev\Seasonaledge\landing\index.html"

# ── Exact string replacements ─────────────────────────────────────────────────
$exact = [ordered]@{

  # H3 sidebar / section headers
  '<h3>Ticker</h3>'                              = '<h3 data-i18n="sidebar.ticker">Ticker</h3>'
  '<h3>Zeitraum</h3>'                            = '<h3 data-i18n="sidebar.period">Zeitraum</h3>'
  '<h3>Analysezeitraum</h3>'                     = '<h3 data-i18n="sidebar.period">Analysezeitraum</h3>'
  '<h3>Datengrundlage</h3>'                      = '<h3 data-i18n="common.data_basis">Datengrundlage</h3>'
  '<h3>Outlier-Filter</h3>'                      = '<h3 data-i18n="sidebar.outlier_filter">Outlier-Filter</h3>'
  '<h3>Technischer Filter</h3>'                  = '<h3 data-i18n="common.tech_filter">Technischer Filter</h3>'
  '<h3>Technische Filter</h3>'                   = '<h3 data-i18n="sidebar.tech_filters">Technische Filter</h3>'
  '<h3>Event-Window</h3>'                        = '<h3 data-i18n="common.event_window">Event-Window</h3>'
  '<h3>Event-Fenster</h3>'                       = '<h3 data-i18n="common.event_window">Event-Fenster</h3>'
  '<h3>Berechnung</h3>'                          = '<h3 data-i18n="common.calculation">Berechnung</h3>'
  '<h3>Berechnungen</h3>'                        = '<h3 data-i18n="common.calculations">Berechnungen</h3>'
  '<h3>Darstellung</h3>'                         = '<h3 data-i18n="sidebar.display">Darstellung</h3>'
  '<h3>Stop-Loss</h3>'                           = '<h3 data-i18n="common.stop_loss">Stop-Loss</h3>'
  '<h3>Fenster</h3>'                             = '<h3 data-i18n="common.window">Fenster</h3>'
  '<h3>Pr&auml;sidentenzyklus</h3>'              = '<h3 data-i18n="sidebar.pres_cycle">Pr&auml;sidentenzyklus</h3>'
  '<h3>Präsidentenzyklus</h3>'                   = '<h3 data-i18n="sidebar.pres_cycle">Präsidentenzyklus</h3>'
  '<h3>Pr&auml;sidentenzyklus-Filter</h3>'       = '<h3 data-i18n="sidebar.pres_cycle_filter">Pr&auml;sidentenzyklus-Filter</h3>'
  '<h3>Präsidentenzyklus-Filter</h3>'            = '<h3 data-i18n="sidebar.pres_cycle_filter">Präsidentenzyklus-Filter</h3>'
  '<h3>Rendite-Analyse</h3>'                     = '<h3 data-i18n="common.return_analysis">Rendite-Analyse</h3>'
  '<h3>Hinweis</h3>'                             = '<h3 data-i18n="common.hint">Hinweis</h3>'
  '<h3>Chart-Anzeige</h3>'                       = '<h3 data-i18n="common.chart_display">Chart-Anzeige</h3>'
  '<h3>Backtest</h3>'                            = '<h3 data-i18n="common.backtest">Backtest</h3>'
  '<h3>Kennzahlen</h3>'                          = '<h3 data-i18n="common.metrics">Kennzahlen</h3>'
  '<h3>Interpretation</h3>'                      = '<h3 data-i18n="common.interpretation">Interpretation</h3>'
  '<h3>Gl&auml;ttung</h3>'                       = '<h3 data-i18n="sidebar.smoothing_h3">Gl&auml;ttung</h3>'
  '<h3>Drawdown-Analyse</h3>'                    = '<h3 data-i18n="common.drawdown_analysis">Drawdown-Analyse</h3>'
  '<h3>Drawdown &amp; Volatilit&auml;t</h3>'     = '<h3 data-i18n="common.drawdown_vola">Drawdown &amp; Volatilit&auml;t</h3>'
  '<h3>Saisonalchart</h3>'                       = '<h3 data-i18n="sidebar.seasonal_chart">Saisonalchart</h3>'
  '<h3>Suche</h3>'                               = '<h3 data-i18n="sidebar.search">Suche</h3>'
  '<h3>Signal</h3>'                              = '<h3 data-i18n="sidebar.signal">Signal</h3>'
  '<h3>Score-Range</h3>'                         = '<h3 data-i18n="sidebar.score_range">Score-Range</h3>'
  '<h3>Kategorie</h3>'                           = '<h3 data-i18n="sidebar.category">Kategorie</h3>'
  '<h3>Monats-Saisonalchart</h3>'               = '<h3 data-i18n="sidebar.month_seasonal_chart">Monats-Saisonalchart</h3>'
  '<h3>Pressure Chart</h3>'                      = '<h3 data-i18n="sidebar.pressure_chart">Pressure Chart</h3>'
  '<h3>Rolling-Vola Fenster</h3>'                = '<h3 data-i18n="sidebar.rolling_vola_h3">Rolling-Vola Fenster</h3>'
  '<h3>Monats-Filter</h3>'                       = '<h3 data-i18n="sidebar.month_filter">Monats-Filter</h3>'
  '<h3>Anzeige</h3>'                             = '<h3 data-i18n="sidebar.display_opts">Anzeige</h3>'
  '<h3>Rendite-Berechnung</h3>'                  = '<h3 data-i18n="sidebar.return_calc">Rendite-Berechnung</h3>'
  '<h3>Two-Week Split</h3>'                      = '<h3 data-i18n="sidebar.two_week_split">Two-Week Split</h3>'
  '<h3>Datenquelle</h3>'                         = '<h3 data-i18n="common.data_source">Datenquelle</h3>'
  '<h3>Dekadenjahre ein/ausblenden</h3>'         = '<h3 data-i18n="sidebar.decade_years">Dekadenjahre ein/ausblenden</h3>'

  # Summary section headers
  '<summary>Methodik</summary>'                                = '<summary data-i18n="common.methodology">Methodik</summary>'
  '<summary>📚 Methodik</summary>'                            = '<summary data-i18n="common.methodology_emoji">📚 Methodik</summary>'
  '<summary>Anomalie-Radar (KI Quick-Check)</summary>'        = '<summary data-i18n="section.anomaly_radar">Anomalie-Radar (KI Quick-Check)</summary>'
  '<summary>Signifikanztest</summary>'                        = '<summary data-i18n="section.significance_test">Signifikanztest</summary>'
  '<summary>Detrend-Indikator / Saisonaler Druck</summary>'   = '<summary data-i18n="section.detrend">Detrend-Indikator / Saisonaler Druck</summary>'
  '<summary>Heatmap: Monat &times; Offset</summary>'          = '<summary data-i18n="section.heatmap_month_offset">Heatmap: Monat &times; Offset</summary>'
  '<summary>Streak-Analyse nach Monat</summary>'              = '<summary data-i18n="section.streak_by_month">Streak-Analyse nach Monat</summary>'
  '<summary>Alle Trades</summary>'                            = '<summary data-i18n="section.all_trades">Alle Trades</summary>'
  '<summary>Max Drawdown: Dekade &times; Monat</summary>'     = '<summary data-i18n="section.max_dd_decade_month">Max Drawdown: Dekade &times; Monat</summary>'
  '<summary>Streak-Analyse</summary>'                         = '<summary data-i18n="section.streak_analysis">Streak-Analyse</summary>'
  '<summary>Monats-Performance</summary>'                     = '<summary data-i18n="section.monthly_perf">Monats-Performance</summary>'
  '<summary>Quartals-Performance</summary>'                   = '<summary data-i18n="section.quarterly_perf">Quartals-Performance</summary>'
  '<summary>Monats-Detailtabelle</summary>'                   = '<summary data-i18n="section.monthly_detail">Monats-Detailtabelle</summary>'
  '<summary>Methodik &amp; Daten</summary>'                   = '<summary data-i18n="section.methodology_data">Methodik &amp; Daten</summary>'
  '<summary>Methodik &amp; Datenquelle</summary>'             = '<summary data-i18n="section.methodology_source">Methodik &amp; Datenquelle</summary>'
  '<summary>Saisonaler Jahresverlauf</summary>'               = '<summary data-i18n="section.annual_progression">Saisonaler Jahresverlauf</summary>'
  '<summary>Drawdown &amp; Volatilit&auml;t</summary>'        = '<summary data-i18n="section.drawdown_vola">Drawdown &amp; Volatilit&auml;t</summary>'
  '<summary>Statistische Signifikanz</summary>'               = '<summary data-i18n="section.stat_significance">Statistische Signifikanz</summary>'

  # Loading spinner (inside loading overlay)
  '<span>Lade Daten&hellip;</span>'   = '<span data-i18n="common.loading">Lade Daten&hellip;</span>'

  # Common simple TH table headers
  '<th>Monat</th>'       = '<th data-i18n="table.month">Monat</th>'
  '<th>Win-Rate</th>'    = '<th data-i18n="table.win_rate">Win-Rate</th>'
  '<th>Median</th>'      = '<th data-i18n="table.median">Median</th>'
  '<th>Datum</th>'       = '<th data-i18n="table.date">Datum</th>'
  '<th>&Oslash; Rendite</th>' = '<th data-i18n="table.avg_return">&Oslash; Rendite</th>'
  '<th>Wochentag</th>'   = '<th data-i18n="table.weekday">Wochentag</th>'
  '<th>Max Gewinn</th>'  = '<th data-i18n="table.max_gain">Max Gewinn</th>'
  '<th>Max Verlust</th>' = '<th data-i18n="table.max_loss">Max Verlust</th>'
  '<th>Std.Abw.</th>'    = '<th data-i18n="table.std_dev">Std.Abw.</th>'
  '<th>Aktion</th>'      = '<th data-i18n="table.action">Aktion</th>'
  '<th>Quartal</th>'     = '<th data-i18n="table.quarter">Quartal</th>'
  '<th>Strategie</th>'   = '<th data-i18n="table.strategy">Strategie</th>'
  '<th>Feiertag</th>'    = '<th data-i18n="table.holiday">Feiertag</th>'
}

# ── Regex replacements for checkbox labels ────────────────────────────────────
# Pattern: <label class="toggle-row"><input[^>]+> TEXT</label>
# → add data-i18n="checkbox.KEY" to label
$checkboxRules = @(
  @{ Text = ' Einzelne Jahre zeigen'; Key = 'checkbox.show_individual' },
  @{ Text = ' Einzeljahre anzeigen'; Key = 'checkbox.show_individual' },
  @{ Text = ' Konfidenzband (&plusmn;1&sigma;)'; Key = 'checkbox.confidence_band' },
  @{ Text = ' Konfidenzband (&#177;1&#963;)'; Key = 'checkbox.confidence_band' },
  @{ Text = ' Perzentil-B&auml;nder (25./75.)'; Key = 'checkbox.percentile_bands' },
  @{ Text = ' Aktuelles Jahr hervorheben'; Key = 'checkbox.highlight_current_yr' },
  @{ Text = ' Aktuelles Jahr einblenden'; Key = 'checkbox.show_current_yr' },
  @{ Text = ' Gann Pressurechart'; Key = 'checkbox.pressure_chart' }
)

# ── Apply to all files ─────────────────────────────────────────────────────────
$totalChanges = 0
foreach ($f in $htmlFiles) {
  $c = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $orig = $c

  # Exact replacements
  foreach ($entry in $exact.GetEnumerator()) {
    $c = $c.Replace($entry.Key, $entry.Value)
  }

  # Checkbox regex replacements
  foreach ($rule in $checkboxRules) {
    $textEsc = [regex]::Escape($rule.Text)
    $pattern = '<label class="toggle-row">(<input[^>]+>)' + $textEsc + '</label>'
    $repl    = '<label class="toggle-row" data-i18n="' + $rule.Key + '">$1' + $rule.Text + '</label>'
    $c = [regex]::Replace($c, $pattern, $repl)
  }

  if ($c -ne $orig) {
    $totalChanges++
    if (-not $DryRun) {
      [System.IO.File]::WriteAllText($f.FullName, $c, [System.Text.Encoding]::UTF8)
    }
    Write-Host "$(if($DryRun){'[DRY]'} else {'[OK]'}) $($f.Name)"
  }
}
Write-Host ""
Write-Host "Files changed: $totalChanges"
