# IV Group Project: Multiview Visualisation

An interactive, multi-view data visualization project developed for the Information Visualisation (IV) course. This project evaluates three distinct visualization systems (System A, B, and C) to explore and analyze the **Taiwan Credit Card Client Default dataset**.

## Project Overview
The core objective of this project is to explore how different Information Visualisation design decisions impact user efficiency and comprehension. We designed three systems to perform the exact same four tasks, ranging from basic filtering to advanced anomaly detection. 

All systems support **multi-view composition** and **brushing and linking**.System C additionally features a powerful **generalised selection** mechanism using hierarchical semantic abstraction.

### The Four Analytical Tasks
1.  **T1: Search and Select**: Isolate a specific high-risk demographic.
2.  **T2: Summarize and Compare**: Compare the distribution of the Credit Limit between defaulting and non-defaulting customers.
3.  **T3: Find Outliers**: Identify the most dangerous outliers (high bill amount but low payment amount).
4.  **T4: Analyze Trends**: Observe the repayment status trends over a 6-month period.

---

## System Designs

* **System A**: Designed for intuitive, everyday UI interactions. Uses Multi-dropdowns (T1) , Histograms (T2) , Scatterplots (T3) , and Stacked Bar Charts (T4).
* **System B**: Designed for statistical comparison. Uses 1D Group Selection (T1) , Boxplots (T2) , 2D Heatmaps (T3) , and Heatmap Grids (T4).
* **System C**: Designed for complex algorithmic insights and data abstraction. Uses a Hierarchical Tree for generalised selection (T1) , Density Plots (T2) , Anomaly Score Bar Charts (T3) , and Line Charts (T4).

---

## Tech Stack
* **Framework**: [Streamlit](https://streamlit.io/) (for interactive web app deployment)
*  **Visualization**: [Altair](https://altair-viz.github.io/) (Vega-Lite Python wrapper for declarative statistical visualization)
* **Data Processing**: Pandas, NumPy

---

## How to Run Locally

### 1. Prerequisites
Ensure you have Python 3.8+ installed. Install the required dependencies:
```bash
pip install streamlit altair pandas numpy openpyxl xlrd
```
### 2. Run the App
Make sure you are in the project’s root directory (i.e. the folder containing `app.py`), then run the following command in the Terminal to start the project:
```bash
streamlit run app.py
