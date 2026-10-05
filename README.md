📊 Automated EDA & AI Insights Generator
An asynchronous, production-ready FastAPI application that automates Exploratory Data Analysis (EDA). Users can upload any CSV dataset to instantly generate statistical summaries, key distribution charts, and high-level business recommendations powered by Google's Gemini 2.0 Flash model—all compiled into a clean, downloadable PDF report.

🚀 Key Features
• Instant PDF Reports: Compiles dataset statistics, AI insights, and visual graphs into a publication-ready document on the fly.
• Smart AI Insights: Leverages the Gemini API to analyze numerical data structures and extract important trends, data quality issues, business insights, and tactical recommendations.
• Memory-Optimized Engine: Reads and streams uploaded data vectors purely in-memory (io.BytesIO) rather than writing heavy user files directly to the server disk.
• Server-Safe Visualizations: Configured with a non-interactive matplotlib backend (Agg) to securely isolate charts and prevent concurrent thread crashes.
• Zero Disk Footprint: Utilizes async background tasks to immediately purge images and PDF files after serving them to the client, keeping server storage lightweight and safe.

🛠️ Architecture & Tech Stack
text
[ User CSV Upload ] ──> [ FastAPI Endpoint ]
                               │
            ┌──────────────────┴──────────────────┐ (Async Concurrency)
            ▼                                     ▼
   [ Pandas Data Profiling ]             [ Google Gemini API ]
            │                                     │
            ▼                                     ▼
   [ Seaborn Charts (Agg) ]             [ Markdown Insights ]
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                    [ FPDF2 Report Builder ] ──> [ Stream Response ] ──> [ Auto-Cleanup Task ]


• Backend Framework: FastAPI & Uvicorn (High-performance, async Python web ecosystem).
• Data Science & Plots: Pandas, Matplotlib, and Seaborn.
• Large Language Model: google-genai SDK targeting the gemini-2.0-flash model.
• Document Engine: fpdf2 for clean, programmatically styled PDF generation.
                    
