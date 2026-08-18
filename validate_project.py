#!/usr/bin/env python3
"""
Validation script for the Online Retail Analytics project.

Run from the project root:
    python validate_project.py

Checks project structure, required files, dashboard/report presence,
absence of broken local filesystem paths in deployed HTML, and that
core Python dependencies import correctly.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
results = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, label, detail))
    return condition


def section(title):
    print(f"\n--- {title} ---")


def run():
    print("=" * 40)
    print("ONLINE RETAIL PROJECT VALIDATION")
    print("=" * 40)

    # 1. Project structure
    section("Project structure")
    required_dirs = ["dashboard", "notebooks", "src", "data", "reports", "figures"]
    for d in required_dirs:
        check(f"Directory exists: {d}/", (ROOT / d).is_dir())

    required_files = [
        "index.html", "README.md", "requirements.txt", ".gitignore", "vercel.json",
    ]
    for f in required_files:
        check(f"File exists: {f}", (ROOT / f).is_file())

    # No leftover nested zip / project archives
    zips = list(ROOT.rglob("*.zip"))
    check("No nested ZIP archives in project", len(zips) == 0,
          detail=str([str(z.relative_to(ROOT)) for z in zips]) if zips else "")

    # No __pycache__ / checkpoints / OS junk
    junk_patterns = ["__pycache__", ".ipynb_checkpoints", ".DS_Store"]
    junk_found = []
    for pat in junk_patterns:
        junk_found += list(ROOT.rglob(pat))
    check("No __pycache__/.ipynb_checkpoints/.DS_Store", len(junk_found) == 0,
          detail=str([str(j.relative_to(ROOT)) for j in junk_found]))

    # 2. Dataset
    section("Dataset")
    dataset = ROOT / "notebooks" / "OnlineRetail.csv"
    check("Dataset present: notebooks/OnlineRetail.csv", dataset.is_file())
    if dataset.is_file():
        check("Dataset non-trivial size (> 1MB)", dataset.stat().st_size > 1_000_000)

    # 3. Notebooks
    section("Notebooks")
    nb1 = ROOT / "notebooks" / "Task1_Sales_Performance_Dashboard.ipynb"
    nb2 = ROOT / "notebooks" / "Task2_Customer_Segmentation_Analysis.ipynb"
    check("Task 1 notebook exists", nb1.is_file())
    check("Task 2 notebook exists", nb2.is_file())

    for label, nb_path in [("Task 1", nb1), ("Task 2", nb2)]:
        if not nb_path.is_file():
            continue
        try:
            nb = json.loads(nb_path.read_text())
            code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
            errors = 0
            for c in code_cells:
                for o in c.get("outputs", []):
                    if o.get("output_type") == "error":
                        errors += 1
            check(f"{label} notebook has code cells", len(code_cells) > 0)
            check(f"{label} notebook has no error outputs", errors == 0, detail=f"{errors} error(s)")
        except Exception as e:
            check(f"{label} notebook is valid JSON", False, detail=str(e))

    # 4. Dashboards
    section("Dashboards")
    dash1 = ROOT / "dashboard" / "sales_dashboard.html"
    dash2 = ROOT / "dashboard" / "customer_segmentation_dashboard.html"
    check("Sales dashboard exists", dash1.is_file())
    check("Segmentation dashboard exists", dash2.is_file())

    local_path_pattern = re.compile(r"[A-Za-z]:\\\\|[A-Za-z]:\\|/mnt/user-data|/home/[a-zA-Z0-9_]+/|C:\\\\Users")
    for label, path in [("Sales dashboard", dash1), ("Segmentation dashboard", dash2), ("index.html", ROOT / "index.html")]:
        if not path.is_file():
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        check(f"{label}: valid DOCTYPE", html.strip().startswith("<!DOCTYPE"))
        check(f"{label}: has viewport meta (mobile-responsive)", "viewport" in html)
        check(f"{label}: no broken local filesystem paths", not local_path_pattern.search(html))

    # Plotly CDN pinned to a specific version (not "latest")
    for label, path in [("Sales dashboard", dash1), ("Segmentation dashboard", dash2)]:
        if not path.is_file():
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"cdn\.plot\.ly/plotly-([0-9][0-9a-zA-Z.\-]*)\.min\.js", html)
        check(f"{label}: Plotly CDN uses pinned version (not 'latest')",
              bool(m) and "latest" not in html.lower().split("cdn.plot.ly")[-1][:40] if m else False,
              detail=m.group(1) if m else "no pinned version found")

    # 5. Reports
    section("Reports")
    rep1 = ROOT / "reports" / "Sales_Business_Insights_Report.pdf"
    rep2 = ROOT / "reports" / "Customer_Segmentation_Report.pdf"
    check("Sales report PDF exists", rep1.is_file())
    check("Segmentation report PDF exists", rep2.is_file())
    for label, p in [("Sales report", rep1), ("Segmentation report", rep2)]:
        if p.is_file():
            check(f"{label}: looks like a real PDF (%PDF header)", p.read_bytes()[:4] == b"%PDF")

    # 6. Data files
    section("Data files")
    expected_data_files = [
        "data_kpis.json", "data_monthly_revenue.csv", "data_regional_sales.csv",
        "data_top_products_revenue.csv", "data_top_products_qty.csv",
        "data_weekday_pattern.csv", "data_hourly_pattern.csv", "data_rfm_full.csv",
        "data_rfm_summary.json", "data_rfm_segment_summary.csv",
        "data_kmeans_cluster_summary.csv",
    ]
    for f in expected_data_files:
        check(f"data/{f} exists", (ROOT / "data" / f).is_file())

    # RFM segmentation sanity check: "Can't Lose Them" must be reachable
    seg_csv = ROOT / "data" / "data_rfm_segment_summary.csv"
    if seg_csv.is_file():
        text = seg_csv.read_text()
        cant_lose_present = "Can't Lose Them" in text and not re.search(r"Can't Lose Them,0,", text)
        check("RFM segment 'Can't Lose Them' is reachable (bug fix verified)", cant_lose_present)

    # 7. index.html links resolve to real files
    section("index.html link validation")
    index_path = ROOT / "index.html"
    if index_path.is_file():
        html = index_path.read_text(encoding="utf-8")
        hrefs = re.findall(r'href="([^"]+)"', html)
        relative_hrefs = [h for h in hrefs if not h.startswith(("http://", "https://", "#", "mailto:"))]
        broken = [h for h in relative_hrefs if not (ROOT / h).is_file()]
        check("All relative links in index.html resolve to real files", len(broken) == 0,
              detail=str(broken))

    # 8. Required Python imports work
    section("Required dependencies")
    for mod in ["pandas", "numpy", "matplotlib", "sklearn", "plotly", "json"]:
        try:
            __import__(mod)
            check(f"import {mod}", True)
        except ImportError as e:
            check(f"import {mod}", False, detail=str(e))

    # ---- Summary ----
    print()
    for status, label, detail in results:
        line = f"[{status}] {label}"
        if detail and status == "FAIL":
            line += f"  -> {detail}"
        print(line)

    print()
    print("=" * 40)
    failed = [r for r in results if r[0] == "FAIL"]
    if not failed:
        print("ALL CHECKS PASSED")
        print("=" * 40)
        return 0
    else:
        print(f"{len(failed)} CHECK(S) FAILED")
        print("=" * 40)
        return 1


if __name__ == "__main__":
    sys.exit(run())
