# 40GP pipe loading dashboard

A local Python dashboard for the pipe loading assessment. Streamlit provides the interface; Plotly provides interactive charts. No account, API key or AI service is required.

## Run on Windows

Install Python 3.11 or newer. Extract the complete folder, open a terminal in it, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m streamlit run app.py
```

Open http://localhost:8501. Keep the terminal running; press Ctrl+C to stop. Dependencies require internet on first install. The dashboard runs locally afterward.

## Interview demonstration

1. Start with carbon steel, NPS 4, SCH 40, 12 m. Explain the payload constraint.
2. Save that scenario. Change to stainless steel to demonstrate dependent schedule selection and density.
3. Select stainless NPS 30, 10S, 6 m to show geometry controlling capacity.
4. Compare 6 m and 12 m lengths, then enter an order and actual freight quote.
5. Export the scenarios or a JSON calculation record including assumptions.

The Excel workbook remains useful as the familiar handover artifact. Use this dashboard as the interactive demonstration. Do not describe it as an AI prediction: the loading model is deterministic and auditable. AI could later assist with extracting quote requests, subject to human validation, without replacing the loading calculations.

## Scope and differences from Excel

The supplied dataset contains 378 combinations across 36 nominal sizes: carbon steel through NPS 48 and stainless S-schedules through NPS 30. It is not exhaustive commercial availability or inventory. Sources appear in the application. Weights are calculated, not copied from the source weight column.

The dashboard compares square packing and both staggered orientations. It can improve on the earlier workbook's single staggered orientation, particularly for large pipes. Results can therefore differ from that workbook. It still does not solve the unrestricted global circle-packing problem. Clearances and payload use the same initial assumptions as Excel. A diagram shows geometry capacity, not an approved loading arrangement; partial-load support and securement require logistics review.

Very small pipes can produce tens of thousands of positions. The diagram shows at most 600 outlines and explicitly labels this limit. All positions remain included in calculations. Saved scenarios persist only in the current browser session; export to keep them.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Freight is manually entered and uses one rate for every required container, including a partial last container. The model does not include duties, insurance or conversion between currencies.
