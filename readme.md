# IV Group Project: Multiview Visualisation

[cite_start]An interactive, multi-view data visualization project developed for the Information Visualisation (IV) course[cite: 279]. [cite_start]This project evaluates three distinct visualization systems (System A, B, and C) to explore and analyze the **Taiwan Credit Card Client Default dataset**[cite: 283].

## Project Overview
The core objective of this project is to explore how different Information Visualisation design decisions impact user efficiency and comprehension. We designed three systems to perform the exact same four tasks, ranging from basic filtering to advanced anomaly detection. 

[cite_start]All systems support **multi-view composition** and **brushing and linking**[cite: 30]. [cite_start]System C additionally features a powerful **generalised selection** mechanism using hierarchical semantic abstraction[cite: 33, 34, 35].

### The Four Analytical Tasks
1. [cite_start]**T1: Search and Select**: Isolate a specific high-risk demographic[cite: 293].
2. [cite_start]**T2: Summarize and Compare**: Compare the distribution of the Credit Limit between defaulting and non-defaulting customers[cite: 310].
3. [cite_start]**T3: Find Outliers**: Identify the most dangerous outliers (high bill amount but low payment amount)[cite: 328].
4. [cite_start]**T4: Analyze Trends**: Observe the repayment status trends over a 6-month period[cite: 331, 332].

---

## System Designs

* **System A**: Designed for intuitive, everyday UI interactions. [cite_start]Uses Multi-dropdowns (T1) [cite: 294][cite_start], Histograms (T2) [cite: 312][cite_start], Scatterplots (T3) [cite: 330][cite_start], and Stacked Bar Charts (T4)[cite: 335].
* **System B**: Designed for statistical comparison. [cite_start]Uses 1D Group Selection (T1) [cite: 294][cite_start], Boxplots (T2) [cite: 312][cite_start], 2D Heatmaps (T3) [cite: 330][cite_start], and Heatmap Grids (T4)[cite: 335].
* **System C**: Designed for complex algorithmic insights and data abstraction. [cite_start]Uses a Hierarchical Tree for generalised selection (T1) [cite: 294][cite_start], Density Plots (T2) [cite: 312][cite_start], Anomaly Score Bar Charts (T3) [cite: 330][cite_start], and Line Charts (T4)[cite: 335].

---

## Tech Stack
* **Framework**: [Streamlit](https://streamlit.io/) (for interactive web app deployment)
* [cite_start]**Visualization**: [Altair](https://altair-viz.github.io/) (Vega-Lite Python wrapper for declarative statistical visualization) [cite: 5]
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