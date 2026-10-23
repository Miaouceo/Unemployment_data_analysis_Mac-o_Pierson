# Unemployment in France

**Macéo PIERSON — EFREI — #EFREIDataStories2026**

Here is the link for the online streamlit : https://unemploymentdataanalysismac-opierson-j5rdctucbilxzqmzgpadez.streamlit.app/
And the link to the github projet : https://github.com/Miaouceo/Unemployment_data_analysis_Mac-o_Pierson

For this project, I built a simple Streamlit dashboard to explore unemployment in the 13 regions of metropolitan France. I compare 2012, 2017 and 2023, with a small section on poverty in 2023.

The main question is: **How has unemployment changed, and what differences remain between regions?**

## Run the project

With Python 3.13, run these commands from the project folder:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

Then open http://localhost:8501. The data files are already included.

## What the dashboard shows

- Unemployment figures for the selected year and regions.
- A line chart showing the three available dates.
- A regional map and ranking.
- A comparison between unemployment and poverty in 2023.

The filters are in the sidebar. The poverty section always uses 2023.

## Data sources

The unemployment and poverty data come from Insee, published on data.gouv.fr by the Tableau de bord des mobilités durables:

- [Unemployment data](https://www.data.gouv.fr/datasets/taux-de-chomage-au-sens-du-recensement)
- [Poverty data](https://www.data.gouv.fr/datasets/taux-de-pauvrete)
- [Regional boundaries — data.gouv.fr / IGN](https://www.data.gouv.fr/datasets/contours-administratifs)

Downloaded on 23 October 2026. The datasets are shared under the [ODbL licence](https://opendatacommons.org/licenses/odbl/1-0/). Exact download links are in `data/sources.json`.

## Method and main results

I kept the 13 metropolitan regions and checked for missing values, duplicates and invalid rates. The retained data contains 39 unemployment records and 13 poverty records, with no missing values. The overall unemployment rate is calculated from the total unemployed and active population counts.

Unemployment fell from **12.72% in 2012 to 11.03% in 2023**. In 2023, Hauts-de-France had the highest rate (**13.84%**) and Pays de la Loire the lowest (**9.07%**).

## Limits

These are census unemployment rates, which differ from the official ILO rate. Only three dates are available, and overseas regions are excluded. A relationship between unemployment and poverty does not prove that one causes the other. Further data notes are included in the dashboard.

## Main files

- `app.py`: dashboard code.
- `data/`: datasets and map boundaries.
- `requirements.txt`: Python dependencies.
- `STORYBOARD.md`: presentation and demo plan.

This is my student project work at EFREI, completed for the course taught by [Mano Joseph Mathew](https://www.linkedin.com/in/manomathew/).

**Macéo PIERSON** — [My LinkedIn](https://www.linkedin.com/in/mac%C3%A9o-pierson-316476294/)
