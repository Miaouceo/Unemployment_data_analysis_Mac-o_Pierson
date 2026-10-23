"""A simple regional unemployment dashboard. Run: streamlit run app.py"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Unemployment in France", page_icon="📊", layout="wide")
DATA = Path(__file__).parent / "data"
CODES = ["11", "24", "27", "28", "32", "44", "52", "53", "75", "76", "84", "93", "94"]
BLUE = "#176B87"
LABELS = {"rate": "Unemployment (%)", "poverty": "Poverty (%)", "region": "Region", "year": "Year"}


@st.cache_data
def load_data():
    """Keep the source files unchanged; prepare English column names in memory."""
    names = {"annee": "year", "geocode_region": "code", "libelle_region": "region",
             "valeur": "rate", "numerateur": "unemployed", "denominateur": "active"}
    raw_jobs = pd.read_csv(DATA / "taux-de-chomage-au-sens-du-recensement-region.csv",
                           dtype={"geocode_region": str}).rename(columns=names)
    raw_poverty = pd.read_csv(DATA / "taux-de-pauvrete-region.csv",
                              dtype={"geocode_region": str}).rename(columns=names)
    jobs = raw_jobs[raw_jobs.code.isin(CODES)].copy()
    poverty = raw_poverty[raw_poverty.code.isin(CODES)].copy()
    for frame, columns in [(jobs, ["year", "rate", "unemployed", "active"]),
                           (poverty, ["year", "rate"])]:
        for column in columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[columns].isna().any().any() or frame.duplicated(["code", "year"]).any():
            raise ValueError("Missing values or duplicate region/year records in the selected scope.")
        if not frame.rate.between(0, 100).all():
            raise ValueError("A rate is outside the valid 0–100% range.")
    expected = {(code, year) for code in CODES for year in [2012, 2017, 2023]}
    if set(zip(jobs.code, jobs.year)) != expected or set(zip(poverty.code, poverty.year)) != {(c, 2023) for c in CODES}:
        raise ValueError("The files do not cover the expected regions and years.")
    if not ((jobs.active > 0) & (jobs.unemployed >= 0) & (jobs.unemployed <= jobs.active)).all():
        raise ValueError("Invalid active population or unemployment count.")
    if ((100 * jobs.unemployed / jobs.active - jobs.rate).abs() > 0.011).any():
        raise ValueError("The rates disagree with the source counts.")
    geo = json.loads((DATA / "regions.geojson").read_text(encoding="utf-8"))
    geo["features"] = [f for f in geo["features"] if f["properties"]["code"] in CODES]
    if {f["properties"]["code"] for f in geo["features"]} != set(CODES):
        raise ValueError("The map is missing a metropolitan region.")
    quality = pd.DataFrame({
        "Dataset": ["Unemployment", "Poverty"],
        "Source rows": [len(raw_jobs), len(raw_poverty)],
        "Source missing rates": [int(raw_jobs.rate.isna().sum()), int(raw_poverty.rate.isna().sum())],
        "Retained rows": [len(jobs), len(poverty)],
        "Retained missing rates": [int(jobs.rate.isna().sum()), int(poverty.rate.isna().sum())],
        "Duplicate region/year rows": [int(jobs.duplicated(["code", "year"]).sum()), int(poverty.duplicated(["code", "year"]).sum())],
    })
    return jobs, poverty.rename(columns={"rate": "poverty"}), geo, quality


def weighted_rate(frame):
    """Combine counts, not percentages, when several regions are selected."""
    return 100 * frame.unemployed.sum() / frame.active.sum()


def show_chart(fig, description):
    fig.update_layout(font=dict(size=14), margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch", alt=description)


st.title("Unemployment in France")
st.markdown("**Has unemployment fallen everywhere?** Explore 13 metropolitan regions, then see how unemployment and poverty compare.")
st.caption("Census unemployment · 2012, 2017 and 2023 · Insee data via data.gouv.fr")

try:
    jobs, poverty, geo, quality = load_data()
except (OSError, ValueError, KeyError) as error:
    st.error(f"The data could not be loaded: {error}")
    st.stop()

with st.sidebar:
    st.header("Explore the data")
    year = st.selectbox("Comparison year", [2012, 2017, 2023], index=2)
    regions = st.multiselect("Regions", sorted(jobs.region.unique()), default=sorted(jobs.region.unique()))
    st.caption("The year changes the KPIs, map and ranking. The trend keeps all three dates. The poverty appendix always uses 2023.")
    st.info("These are census unemployment rates, not the official ILO unemployment rate.")

if not regions:
    st.info("Select at least one region in the sidebar to explore the dashboard.")
    st.stop()

selected = jobs[jobs.region.isin(regions)]
current = selected[selected.year == year]
baseline = selected[selected.year == 2012]
rate = weighted_rate(current)
change = rate - weighted_rate(baseline)
highest = current.loc[current.rate.idxmax()]
lowest = current.loc[current.rate.idxmin()]
scope = "Metropolitan France" if len(regions) == 13 else f"{len(regions)} selected region(s)"

st.subheader(f"1. Overview · {year}")
st.write(f"**{scope}: {rate:.2f}% unemployment**, a change of **{change:+.2f} percentage points** since 2012.")
col1, col2, col3 = st.columns(3)
col1.metric("Unemployment rate", f"{rate:.2f}%", f"{change:+.2f} pp vs 2012", delta_color="inverse")
col2.metric("Highest regional rate", f"{highest.rate:.2f}%")
col2.caption(highest.region)
col3.metric("Lowest regional rate", f"{lowest.rate:.2f}%")
col3.caption(lowest.region)
st.caption("Overall rate = total unemployed / total active population × 100. A percentage-point change is a difference between two rates.")

st.subheader("2. Change over time")
totals = selected.groupby("year", as_index=False)[["unemployed", "active"]].sum()
totals["rate"] = 100 * totals.unemployed / totals.active
end_change = totals.iloc[-1].rate - totals.iloc[0].rate
st.write(f"Across the selected regions, unemployment changed by **{end_change:+.2f} percentage points between 2012 and 2023**.")
fig = px.line(totals, x="year", y="rate", markers=True, labels=LABELS,
              color_discrete_sequence=[BLUE], height=310)
fig.update_traces(hovertemplate="Year: %{x}<br>Unemployment: %{y:.2f}%<extra></extra>")
fig.update_xaxes(tickvals=[2012, 2017, 2023])
fig.update_yaxes(rangemode="tozero")
fig.add_vline(x=year, line_dash="dot", line_color="#777777")
show_chart(fig, "Line chart of weighted unemployment in the selected regions at three census dates; the dotted line marks the comparison year.")
st.caption("Only three observations are available. Connecting lines are a visual guide, not measured annual values.")

st.subheader(f"3. Regional differences · {year}")
st.write(f"The gap between the highest and lowest selected region is **{highest.rate - lowest.rate:.2f} percentage points**.")
left, right = st.columns(2)
with left:
    fig = px.choropleth_map(current, geojson=geo, locations="code", featureidkey="properties.code",
                            color="rate", hover_name="region", hover_data={"code": False, "rate": ":.2f"},
                            color_continuous_scale="Blues", range_color=[8, 18], labels=LABELS,
                            map_style="white-bg", center={"lat": 46.5, "lon": 2.5}, zoom=3.6, height=510)
    fig.update_traces(marker_line_width=1, marker_line_color="#FFFFFF")
    show_chart(fig, f"Map of unemployment by selected metropolitan region in {year}. Darker blue indicates a higher rate; the scale stays fixed across years.")
    st.caption("Map: data.gouv.fr / IGN Admin Express, simplified 2026 boundaries. Unselected regions are not coloured.")
with right:
    ranking = current.sort_values("rate")
    fig = px.bar(ranking, x="rate", y="region", orientation="h", text="rate", labels=LABELS,
                 color_discrete_sequence=[BLUE], height=510)
    fig.update_traces(texttemplate="%{x:.2f}%", textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}<br>Unemployment: %{x:.2f}%<extra></extra>")
    fig.update_xaxes(range=[0, 20])
    fig.update_yaxes(title=None)
    show_chart(fig, f"Horizontal ranking of selected regions by unemployment in {year}, with exact rates printed beside each bar.")

st.subheader("4. Small appendix · Poverty in 2023")
st.write("**Do regions with higher unemployment also have higher poverty?** Each point represents one selected region.")
appendix = selected[selected.year == 2023].merge(poverty[["code", "year", "poverty"]],
                                                on=["code", "year"], validate="one_to_one")
fig = px.scatter(appendix, x="rate", y="poverty", hover_name="region", labels=LABELS,
                 color_discrete_sequence=[BLUE], height=350)
fig.update_traces(marker=dict(size=13, line=dict(width=1, color="white")))
fig.update_xaxes(range=[8, 15])
fig.update_yaxes(range=[10, 22])
show_chart(fig, "Scatter plot comparing regional unemployment and poverty in 2023. Hover over a point to identify the region and both rates.")
if len(appendix) >= 3 and appendix.rate.nunique() > 1 and appendix.poverty.nunique() > 1:
    correlation = appendix.rate.corr(appendix.poverty)
    st.write(f"For this selection, the Pearson correlation is **{correlation:.2f}** (−1 to +1). This describes association, not causation.")
else:
    st.caption("Select at least three regions with different rates to display a descriptive correlation.")
st.caption("Poverty = share of people below 60% of the median standard of living. This appendix uses 2023, regardless of the comparison-year filter.")

st.subheader("5. What can we take away?")
st.write(f"For the selected regions, the overall rate moved from **{totals.iloc[0].rate:.2f}% in 2012** to **{totals.iloc[-1].rate:.2f}% in 2023**. "
         f"In {year}, **{highest.region}** has the highest selected rate ({highest.rate:.2f}%).")
st.write("These comparisons can help students and local decision-makers identify places to investigate further. "
         "Before proposing an explanation or policy, examine local jobs, qualifications and living costs. "
         "Regional averages do not describe every person or neighbourhood.")

with st.expander("Data quality, methods and limitations"):
    st.dataframe(quality, hide_index=True, width="stretch")
    st.write("Validation passed: 39 unemployment records, 13 poverty records, unique region/year keys, rates between 0 and 100, positive denominators, matching map codes and complete 2023 joins.")
    st.markdown("""
    - Overseas regions are excluded consistently. No missing values are filled or estimated.
    - Column names are translated in memory and numbers converted to numeric values. The downloaded CSVs are preserved.
    - The unemployment metadata describes ages 15+, but its extraction filters specify ages 15–64. We use the published values and flag this inconsistency rather than changing the data.
    - Census unemployment differs from the ILO definition and from registered jobseekers.
    - Counts are survey estimates, so decimal counts are expected. The combined rate uses these counts, not an unweighted mean.
    - The three census dates use the source's current regional geography. There are no annual observations between them.
    - Poverty covers ordinary households and excludes collective accommodation. The 2023 Filosofi 2 method is not directly comparable with 2012–2021 Filosofi data.
    - The appendix is a regional association, based on at most 13 observations. It cannot establish causation or individual-level relationships.
    """)
    st.dataframe(appendix[["region", "year", "rate", "poverty"]].rename(columns=LABELS), hide_index=True, width="stretch")

with st.expander("Sources and downloads"):
    st.markdown("""
    Original statistics: **Insee**. CSV publisher: **Tableau de bord des mobilités durables**.
    - [Census unemployment](https://www.data.gouv.fr/datasets/taux-de-chomage-au-sens-du-recensement)
    - [Poverty](https://www.data.gouv.fr/datasets/taux-de-pauvrete)
    - [Map boundaries: data.gouv.fr / IGN](https://www.data.gouv.fr/datasets/contours-administratifs)

    Downloaded on 23 October 2026. These dataset listings use **ODbL**; see the README for attribution and licence links.
    """)
    st.download_button("Download selected unemployment data (CSV)", selected.to_csv(index=False).encode("utf-8-sig"),
                       file_name="selected_unemployment.csv", mime="text/csv")

st.caption("#EFREIDataStories2026 · A simple open-data story")
