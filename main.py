import os
import io
import asyncio
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from google import genai
from fpdf import FPDF

# Force matplotlib to use a non-interactive backend (Thread-safe for servers)
matplotlib.use('Agg')

app = FastAPI(title="Automated EDA API")

# Initialize Gemini Client using environment variables for security
# Set GEMINI_API_KEY in your system environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


# -----------------------------
# Chart Generation (Safe & Non-blocking)
# -----------------------------
def _sync_generate_charts(df: pd.DataFrame) -> List[str]:
    """Generates charts sequentially in a thread-safe manner."""
    charts = []
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns

    for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
        plt.figure(figsize=(6, 4))
        sns.histplot(df[col], kde=True)
        plt.title(f"Distribution of {col}")
        plt.tight_layout()
        
        filename = f"{col}_hist.png"
        plt.savefig(filename)
        plt.close()
        charts.append(filename)
        
    return charts

async def generate_charts(df: pd.DataFrame) -> List[str]:
    """Offloads CPU-bound chart generation to an external thread worker."""
    return await asyncio.to_thread(_sync_generate_charts, df)


# -----------------------------
# Generate AI Insights
# -----------------------------
async def generate_insights(summary: str) -> str:
    """Fetches insights from Gemini API asynchronously."""
    if not client:
        return "AI insights unavailable: GEMINI_API_KEY environment variable not configured."

    prompt = f"""
    You are a professional Data Scientist.
    Analyze the dataset summary below and generate insights.

    Dataset Summary:
    {summary}

    Provide:
    1. Important Trends
    2. Data Quality Issues
    3. Business Insights
    4. Recommendations
    """
    try:
        # Offload external network request to thread pool to avoid blocking the event loop
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI insights unavailable due to API error: {str(e)}"


# -----------------------------
# Generate PDF Report
# -----------------------------
def _sync_generate_pdf(summary: str, insights: str, charts: List[str]) -> str:
    """Assembles the PDF report synchronously."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title Page
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 15, "Automated EDA Report", ln=True, align="C")
    pdf.ln(10)

    # Data Summary
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "DATA SUMMARY:", ln=True)
    pdf.set_font("Courier", size=9)  # Monospaced font helps alignment for tables/summaries
    pdf.multi_cell(0, 6, summary)
    pdf.ln(10)

    # AI Insights
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "AI INSIGHTS:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, insights)

    # Append Visual Charts
    for chart in charts:
        if os.path.exists(chart):
            pdf.add_page()
            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(0, 10, f"Visualization: {chart.replace('_hist.png', '')}", ln=True)
            pdf.image(chart, x=15, y=25, w=180)
            
    filename = "EDA_Report.pdf"
    pdf.output(filename)
    return filename

async def generate_pdf(summary: str, insights: str, charts: List[str]) -> str:
    """Offloads PDF rendering to a background thread."""
    return await asyncio.to_thread(_sync_generate_pdf, summary, insights, charts)


# -----------------------------
# MAIN API ENDPOINT
# -----------------------------
@app.post("/eda")
async def run_eda(file: UploadFile = File(...)):
    # Validate uploaded file extension types
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        # Read file contents completely in-memory (No slow local disk writes)
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse CSV file: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded CSV file is empty.")

    summary = str(df.describe())

    # Concurrent Execution: Run chart rendering and Gemini analysis at the same time
    charts, insights = await asyncio.gather(
        generate_charts(df),
        generate_insights(summary)
    )

    # Build the PDF file
    report_path = await generate_pdf(summary, insights, charts)

    # Optional: Clean up isolated temporary image files generated on disk
    for chart in charts:
        if os.path.exists(chart):
            os.remove(chart)

    # Direct File Streaming Download Response
    return FileResponse(
        path=report_path, 
        filename="EDA_Report.pdf", 
        media_type="application/pdf"
    )
