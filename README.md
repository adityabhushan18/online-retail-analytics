# Online Retail Analytics

**Sales Performance & Customer Segmentation Analysis**

A data analytics portfolio project analyzing the [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online+retail)
(541,909 transactions from a UK-based online gift retailer, Dec 2010–Dec 2011). Two tasks are
completed: a sales performance dashboard and an RFM/K-Means customer segmentation analysis.

## Project Overview

```text
Raw Dataset
     |
     v
Cleaning (remove cancellations, invalid qty/price, blank descriptions)
     |
     +--> Task 1: Sales Performance Dashboard
     |         Revenue, orders, AOV, repeat rate, monthly trend,
     |         top products, regional sales, weekday/hourly patterns
     |
     +--> Task 2: Customer Segmentation Analysis
               RFM scoring (8 named segments) + K-Means clustering
```

Both tasks share the same cleaned dataset and the same core logic in `src/analysis_core.py`.
Everything downstream — the dashboards, PDF reports, and notebook outputs — is generated
directly from that pipeline, so the numbers are consistent across every file in the project.

## Dataset

- **Source:** [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online+retail)
- **Rows:** 541,909 raw transactions
- **Fields:** `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country`
- **Location:** `notebooks/OnlineRetail.csv`

## Tasks Completed

1. ✅ **Task 1 — Sales Performance Dashboard**
2. ✅ **Task 2 — Customer Segmentation Analysis**

## Methodology

### Task 1: Sales Performance

1. Remove rows with a missing/blank `Description`.
2. Flag cancelled invoices (`InvoiceNo` starting with `C`) and exclude them.
3. Remove `Quantity <= 0` and `UnitPrice <= 0` rows.
4. Compute `TotalPrice = Quantity * UnitPrice`.
5. Aggregate: monthly revenue, top products (by revenue and by quantity), regional sales,
   weekday/hourly purchasing patterns, new-vs-repeat customer revenue.

### Task 2: Customer Segmentation

1. Start from the Task 1 cleaned data, keep only rows with a non-null `CustomerID`.
2. Compute **RFM** per customer: Recency (days since last order), Frequency (distinct orders),
   Monetary (total spend).
3. Score each of R/F/M into quintiles (1–5) and map combinations to 8 named segments
   (Champions, Loyal Customers, At Risk, Can't Lose Them, New Customers, Potential Loyalists,
   Needs Attention, Hibernating / Lost).
4. Independently cross-check with **K-Means** clustering (`k=4`, `random_state=42`, `n_init=10`)
   on `log1p`-transformed, `StandardScaler`-standardized RFM values, elbow-validated. Clusters
   are deterministically relabeled by descending average Monetary value (High/Mid/Low/Lowest-Value)
   so re-running produces identical output every time.

> **Bug fixed during this audit:** the rule-based segmentation originally checked the broader
> `"At Risk"` condition (`R<=2, F>=3, M>=3`) *before* the more specific `"Can't Lose Them"`
> condition (`R<=2, F>=4, M>=4`). Since `F>=4` implies `F>=3` and `M>=4` implies `M>=3`, every
> "Can't Lose Them" customer was always being caught by "At Risk" first — the segment was
> mathematically unreachable (0 customers). Fixed by evaluating the more specific rule first.
> After the fix: **"Can't Lose Them" = 166 customers / £369,840**, and **"At Risk"** drops from
> 454 to a correct **288 customers / £372,310**. All dashboards, reports, and notebook outputs
> in this project reflect the corrected numbers.

## Project Structure

```text
online-retail-analytics/
├── README.md
├── requirements.txt
├── .gitignore
├── vercel.json
├── index.html                     # Landing page (deployment entry point)
├── validate_project.py            # Structure/consistency validation script
│
├── dashboard/
│   ├── sales_dashboard.html                     # Static, self-contained (Plotly via CDN)
│   └── customer_segmentation_dashboard.html
│
├── notebooks/
│   ├── OnlineRetail.csv
│   ├── Task1_Sales_Performance_Dashboard.ipynb  # Executed, with outputs
│   └── Task2_Customer_Segmentation_Analysis.ipynb
│
├── src/
│   ├── analysis_core.py           # Shared cleaning / RFM / K-Means logic
│   ├── generate_task1_assets.py   # Regenerates data/ + figures/ for Task 1
│   ├── generate_task2_assets.py   # Regenerates data/ + figures/ for Task 2
│   ├── build_dashboard1.py        # Regenerates dashboard/sales_dashboard.html
│   ├── build_dashboard2.py        # Regenerates dashboard/customer_segmentation_dashboard.html
│   ├── build_report1.py           # Regenerates reports/Sales_Business_Insights_Report.pdf
│   ├── build_report2.py           # Regenerates reports/Customer_Segmentation_Report.pdf
│   ├── build_notebook1.py         # Regenerates notebooks/Task1_*.ipynb from scratch (unexecuted)
│   └── build_notebook2.py         # Regenerates notebooks/Task2_*.ipynb from scratch (unexecuted)
│
├── data/                          # Cleaned/aggregated CSV + JSON (source of truth for dashboards/reports)
├── reports/                       # PDF business insights reports
└── figures/                       # Static chart images used in the PDF reports
```

All `src/*.py` scripts are designed to be run **from the project root**.

## Installation

```bash
python -m venv .venv
```

Activate it:

- macOS/Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

Then install dependencies:

```bash
pip install -r requirements.txt
```

## Run Dashboards

The dashboards are static HTML files (Plotly loaded from a pinned CDN version — no backend,
no build step). Serve the project root with any static file server:

```bash
python -m http.server 8000
```

Open:

```text
http://localhost:8000
```

This opens the landing page (`index.html`), which links to both dashboards, both notebooks,
and both PDF reports.

## Run Notebooks

```bash
jupyter notebook notebooks/
```

Open either notebook and run all cells top to bottom. Each notebook locates
`OnlineRetail.csv` automatically (it checks the notebook's own directory, the current working
directory, and `<cwd>/notebooks/`), so it works whether Jupyter is launched from the project
root or from `notebooks/` directly.

To re-run headlessly and regenerate outputs (used to validate this project):

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/Task1_Sales_Performance_Dashboard.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/Task2_Customer_Segmentation_Analysis.ipynb
```

To regenerate the aggregated data, figures, dashboards, and PDF reports from the pipeline
(instead of the notebooks) after any change to `src/analysis_core.py`:

```bash
python src/generate_task1_assets.py
python src/generate_task2_assets.py
python src/build_dashboard1.py
python src/build_dashboard2.py
python src/build_report1.py
python src/build_report2.py
```

## Validate

```bash
python validate_project.py
```

Checks project structure, required files, dashboard/report integrity, absence of broken
local filesystem paths, and that core dependencies import correctly.

## Deployment (Vercel)

This is a plain static site — no build framework, no React/Next.js, no backend.

1. Push this repository to GitHub (or GitLab/Bitbucket).
2. In Vercel: **New Project → Import** the repository.
3. Framework preset: **Other** (static). Leave the build command empty and set the output
   directory to the project root (`.`).
4. Deploy.

The site will be available at `https://<your-project>.vercel.app` with:

```text
/                                                     → index.html
/dashboard/sales_dashboard.html                       → Sales dashboard
/dashboard/customer_segmentation_dashboard.html       → Segmentation dashboard
/reports/Sales_Business_Insights_Report.pdf           → Sales report
/reports/Customer_Segmentation_Report.pdf             → Segmentation report
/notebooks/Task1_Sales_Performance_Dashboard.ipynb    → Notebook download
/notebooks/Task2_Customer_Segmentation_Analysis.ipynb → Notebook download
```

`vercel.json` sets correct `Content-Type`/`Content-Disposition` headers for the `.ipynb` and
`.pdf` files so they download/open cleanly.

## Key Results

**Task 1 — Sales Performance**
- Total Revenue: **£10,666,684.54** across **19,960 orders** and **4,338 customers**
- Average Order Value: **£534.40**
- Repeat purchase rate: **65.6%** of customers ordered more than once
- Revenue is strongly seasonal, peaking in **Q4 (Sep–Nov)**
- The **UK** dominates revenue; Netherlands, EIRE, Germany, and France are the top international markets
- Orders peak between **10:00–15:00**; there is effectively no Saturday order volume

**Task 2 — Customer Segmentation**
- **4,338 customers** segmented, covering **£8,911,407.90** of transaction revenue
- **Champions** (962 customers, ~22%) generate **~65%** of total segmented revenue
- **At Risk** (288 customers / £372,310) and **Can't Lose Them** (166 customers / £369,840)
  together represent high-value customers who have gone quiet — the top win-back priority
- K-Means clustering (4 clusters, data-driven) independently confirms the same High/Mid/Low/
  Lowest-value structure as the rule-based RFM segments

## Tools Used

Python, pandas, NumPy, scikit-learn (K-Means, StandardScaler), Matplotlib, Plotly (interactive
dashboards), Jupyter Notebook, ReportLab (PDF report generation).
