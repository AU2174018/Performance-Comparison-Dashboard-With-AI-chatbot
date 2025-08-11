import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import io
import os
import openai
from pypdf import PdfReader
import docx 
from dotenv import load_dotenv


# Load environment variables from a .env file if it exists
load_dotenv()

# Page configuration must be the first Streamlit command.
st.set_page_config(page_title="Performance Comparison Dashboard", layout="wide")

# --- THEME AND STYLING ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;700&display=swap');

        :root {
            --gemini-blue: #4285F4;
            --gemini-purple: #8950FC;
            --gemini-teal: #00BCD4;
            --gemini-orange: #FBBC04;
            --primary-color: var(--gemini-blue);
            --secondary-color: var(--gemini-teal);
            --text-color-dark: #202124;
            --text-color-light: #5f6368;
            --background-color: #f8f9fa;
            --card-background-color: #ffffff;
            --border-color: #e0e0e0;
        }

        html, body, [class*="st-"] {
            font-family: 'Google Sans', 'Roboto', sans-serif;
            font-size: 22px;
        }
        .stApp {
            background: var(--background-color);
        }
        .st-emotion-cache-16txtl3 { /* Main content area */
            background-image: radial-gradient(circle at top left, rgba(66, 133, 244, 0.08), transparent 40%),
                              radial-gradient(circle at bottom right, rgba(137, 80, 252, 0.08), transparent 40%);
            padding-top: 2rem;
        }
        .stMetric {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            padding: 1.5em;
            border-radius: 16px; /* More rounded */
            color: #333333;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .stMetric:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }
        .stMetric .st-bf { /* Label */
            font-size: 1.5rem;
            color: var(--text-color-light);
            font-weight: 500;
        }
        .stMetric .st-c5 { /* Value */
            font-size: 3.8rem;
            font-weight: 700;
            color: var(--text-color-dark);
        }
        h1 {
            color: var(--text-color-dark); 
            font-size: 4.0rem;
            font-weight: 700;
        }
        h3 {
            font-weight: 700;
            color: var(--text-color-dark);
            font-size: 2.6rem;
            border-bottom: 4px solid;
            border-image-slice: 1;
            border-width: 4px;
            border-image-source: linear-gradient(to right, var(--gemini-blue), var(--gemini-teal));
            padding-bottom: 0.5em;
            margin-top: 2.5rem;
            margin-bottom: 1.5rem;
        }
        .st-expander {
            background-color: var(--card-background-color);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        .st-expander header {
            font-size: 1.2rem;
            font-weight: 700;
        }
        /* Style for tabs */
        .stTabs [data-baseweb="tab-list"] { 
            gap: 16px;
            border-bottom: 2px solid var(--border-color);
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: transparent;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            font-size: 1.4rem;
            font-weight: 500;
            color: var(--text-color-light);
            border: none;
            border-bottom: 4px solid transparent;
            margin-bottom: -2px;
        }
        .stTabs [aria-selected="true"] {
            background-color: transparent;
            color: var(--primary-color);
            border-image-slice: 1;
            border-width: 4px;
            border-image-source: linear-gradient(to right, var(--gemini-blue), var(--gemini-teal));
            box-shadow: none;
        }
        /* Style for captions to make them more readable */
        div[data-testid="stCaptionContainer"] {
            font-size: 1.0rem;
            font-style: italic;
            color: #6c757d;
        }
        /* Assistant Expander Styling */
        div[data-testid="stExpander"] {
            border: 1px solid var(--border-color);
            border-radius: 12px;
            background-color: var(--card-background-color);
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        /* Style for search/text inputs to make them more visible */
        div[data-testid="stTextInput"] > div > div > input, div[data-testid="stNumberInput"] > div > div > input {
            border: 1px solid #ced4da;
            border-radius: 8px;
            padding: 12px;
            font-size: 1.1rem;
            background-color: #ffffff;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        div[data-testid="stTextInput"] > div > div > input:focus, div[data-testid="stNumberInput"] > div > div > input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.25);
        }
        div[data-testid="stTextInput"] > label, div[data-testid="stNumberInput"] > label {
            font-weight: 500;
            font-size: 1.1rem;
        }
        /* Style for selectbox to make it more visible */
        div[data-testid="stSelectbox"] > div > div {
            border: 1px solid #ced4da;
            border-radius: 8px;
            padding: 8px;
            background-color: #ffffff;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        /* Ensure the text inside the selectbox doesn't get cut off */
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
            background-color: transparent;
            white-space: normal !important;
            height: auto !important;
            min-height: 2.5rem;
        }
        div[data-testid="stSelectbox"] > div:has(> div[data-baseweb="select"][aria-expanded="true"]) > div {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.25);
        }
        div[data-testid="stSelectbox"] > label {
            font-weight: 500;
            font-size: 1.1rem;
        }

        /* New class for the insights box */
        .insights-box {
            background-color: #e8f0fe; /* Lighter Google blue */
            color: #174ea6; /* Darker Google blue text */
            padding: 25px;
            border-radius: 12px;
            border-left: 8px solid var(--gemini-blue);
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }
        .insights-box ul {
            padding-left: 20px;
            margin-bottom: 0;
        }
        .insights-box li {
            margin-bottom: 12px;
            line-height: 1.6;
        }
        
        /* --- Gemini Chat UI --- */
        /* Assistant messages */
        div[data-testid="stChatMessage"]:has(span[aria-label="🤖"]) {
            background-color: #f0f4f9;
            border-radius: 1.2em;
            padding: 1em 1.2em;
        }

        /* User messages */
        div[data-testid="stChatMessage"]:has(span[aria-label="🧑‍💻"]) {
            background-color: #e8f0fe;
            border-radius: 1.2em;
            padding: 1em 1.2em;
        }
    </style>
""", unsafe_allow_html=True)

# --- DATA PROCESSING FUNCTIONS ---
@st.cache_data
def load_and_process_data(current_file: io.BytesIO, previous_file: io.BytesIO) -> tuple[pd.DataFrame, list, list]:
    """Loads, cleans, merges, and calculates differences between two report CSVs. Caches the result."""
    df_current = pd.read_csv(current_file)
    df_previous = pd.read_csv(previous_file)

    df_current.columns = df_current.columns.str.strip()
    df_previous.columns = df_previous.columns.str.strip()

    # Exclude the 'Total' row if it exists, common in performance reports
    if 'Label' in df_current.columns:
        df_current = df_current[~df_current['Label'].str.contains('Total', case=False, na=False)]
    if 'Label' in df_previous.columns:
        df_previous = df_previous[~df_previous['Label'].str.contains('Total', case=False, na=False)]

    # --- New/Missing Transaction Analysis ---
    current_labels = set(df_current['Label'])
    previous_labels = set(df_previous['Label'])
    new_transactions = list(current_labels - previous_labels)
    missing_transactions = list(previous_labels - current_labels)

    # Define columns
    required_cols = ["Label", "Average"]
    # Add new optional columns for detailed view and percentile comparison
    optional_cols = ["Error %", "Throughput", "Min", "Max", "90% Line", "95% Line", "99% Line"]
    time_cols_ms = ["Average", "Min", "Max", "90% Line", "95% Line", "99% Line"]

    # Check for required columns
    for col in required_cols:
        if col not in df_current.columns or col not in df_previous.columns:
            raise KeyError(f"Missing required column '{col}' in one of the files.")

    # Convert time columns from ms to seconds where they exist
    for df in [df_current, df_previous]:
        for col in time_cols_ms:
            if col in df.columns:
                df[col] = df[col] / 1000

    # Select only the columns that are present in the files
    cols_to_use_current = required_cols + [col for col in optional_cols if col in df_current.columns]
    cols_to_use_previous = required_cols + [col for col in optional_cols if col in df_previous.columns]

    df_current = df_current[cols_to_use_current]
    df_previous = df_previous[cols_to_use_previous]

    merged = pd.merge(df_current, df_previous, on="Label", suffixes=('_Current', '_Previous'))

    # Calculate differences and percentage changes using (Previous - Current) so that positive values indicate improvement.
    merged["Avg_Diff"] = merged["Average_Previous"] - merged["Average_Current"]
    denominator_avg = merged["Average_Previous"].replace(0, np.nan)
    merged["Avg_Change_%"] = (merged["Avg_Diff"] / denominator_avg) * 100
    merged["Avg_Change_%"].fillna(0, inplace=True)

    # Calculate 90% Line difference if column exists
    if '90% Line_Current' in merged.columns and '90% Line_Previous' in merged.columns:
        merged["90th_Diff"] = merged["90% Line_Previous"] - merged["90% Line_Current"]
        denominator_90_line = merged["90% Line_Previous"].replace(0, np.nan)
        merged["90th_Change_%"] = (merged["90th_Diff"] / denominator_90_line) * 100
        merged["90th_Change_%"].fillna(0, inplace=True)
    
    if 'Min_Current' in merged.columns and 'Min_Previous' in merged.columns:
        merged['Min_Diff'] = merged['Min_Previous'] - merged['Min_Current']

    if 'Max_Current' in merged.columns and 'Max_Previous' in merged.columns:
        merged['Max_Diff'] = merged['Max_Previous'] - merged['Max_Current']

    return merged, new_transactions, missing_transactions

@st.cache_data
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Converts a dataframe to a CSV byte string for downloads."""
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def filter_dataframe(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
    """Filters the dataframe based on a search term in the 'Label' column. Caches the result."""
    if not search_term:
        return df.copy() # Return a copy to prevent modifying the cached object
    return df[df["Label"].str.contains(search_term, case=False)].copy()

@st.cache_data
def extract_text_from_file(uploaded_file):
    """Extracts text from an uploaded file (PDF, DOCX, TXT, XLSX)."""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        pdf_reader = PdfReader(uploaded_file)
        return "".join(page.extract_text() for page in pdf_reader.pages)
    elif file_extension == 'docx':
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file_extension == 'txt':
        return uploaded_file.read().decode('utf-8')
    elif file_extension in ['xlsx', 'xls']:
        excel_file = pd.ExcelFile(uploaded_file)
        sheets_content = []
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            # Add sheet name as a header
            sheets_content.append(f"--- SHEET: {sheet_name} ---\n")
            # Convert dataframe to markdown format for better AI understanding
            sheets_content.append(df.to_markdown(index=False))
        return "\n\n".join(sheets_content)
    else:
        st.warning(f"Unsupported file type: .{file_extension}. Please upload a PDF, DOCX, TXT, or XLSX file.")
        return None

@st.cache_data
def create_comparison_fig(df: pd.DataFrame, y_current: str, y_previous: str, title: str, y_axis_title: str, sort_by: str) -> go.Figure:
    """Creates an attractive grouped bar chart for comparing current vs. previous metrics. Caches the result."""
    # Sorting logic based on user selection
    if sort_by == 'Current Value':
        sort_col, ascending = y_current, False # Descending for values
    elif sort_by == 'Previous Value':
        sort_col, ascending = y_previous, False # Descending for values
    else: # Default to transaction name
        sort_col, ascending = 'Label', True # Ascending for labels (A-Z)

    df_sorted = df.sort_values(by=sort_col, ascending=ascending)

    # --- Interactive Chart Annotations ---
    # Create custom hover text for rich tooltips
    hover_text_current = [
        f"<b>{row['Label']}</b><br>Current: {row[y_current]:.3f}<br>Previous: {row[y_previous]:.3f}<br>Change: {row[y_previous] - row[y_current]:+.3f}<extra></extra>"
        for _, row in df_sorted.iterrows()
    ]
    hover_text_previous = [
        f"<b>{row['Label']}</b><br>Previous: {row[y_previous]:.3f}<br>Current: {row[y_current]:.3f}<br>Change: {row[y_previous] - row[y_current]:+.3f}<extra></extra>"
        for _, row in df_sorted.iterrows()
    ]

    # Dynamically adjust height to prevent label overlapping
    chart_height = max(400, len(df_sorted) * 25)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted["Label"],
        x=df_sorted[y_previous],
        name="Previous",
        marker_color='#ff9800',
        opacity=0.8,
        hoverinfo="text",
        hovertext=hover_text_previous,
        orientation='h'
    ))
    fig.add_trace(go.Bar(
        y=df_sorted["Label"],
        x=df_sorted[y_current],
        name="Current",
        marker_color='#00bcd4',
        opacity=0.8,
        hoverinfo="text",
        hovertext=hover_text_current,
        orientation='h'
    ))
    fig.update_layout(
        barmode='group',
        title_text=f"<b>{title} (Sorted by {sort_by})</b>",
        xaxis_title=y_axis_title, # This is now the value axis
        yaxis_title=None, # Labels are on this axis, title is redundant
        height=chart_height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        xaxis=dict(gridcolor='#e0e0e0'),
        yaxis=dict(autorange="reversed"), # Ensures sorted items appear from top to bottom
        font=dict(color="#333333"),
        hovermode="y unified",
        margin=dict(l=250) # Add left margin to prevent y-axis labels from being cut off
    )
    return fig

# --- AUTHENTICATION & LOGIN PAGE ---
def login_page():
    """Displays the login page and handles authentication."""
    # This CSS is scoped to the login page only.
    st.markdown("""
        <style>
            /* This style block is only for the login page */
            [data-testid="stHeader"], [data-testid="stSidebar"] { display: none; }
            
            .stApp {
                background-image: linear-gradient(135deg, #4285F4 0%, #8950FC 100%);
            }

            /* Make the block-container (the content area) a full-screen flexbox to center the form */
            .stApp .main .block-container {
                display: flex;
                flex-direction: column;
                justify-content: center; /* Vertical centering */
                align-items: center;    /* Vertical centering */
                height: 100vh;          /* Full viewport height */
                padding: 0 !important;
                margin: 0 !important;
                width: 100% !important;
                max-width: 100% !important;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: scale(0.95); }
                to { opacity: 1; transform: scale(1); }
            }

            /* Style the form container itself as the card */
            div[data-testid="stForm"] {
                background-color: rgba(255, 255, 255, 0.98);
                padding: 4rem 5rem;
                border-radius: 1rem;
                box-shadow: 0 15px 35px rgba(0,0,0,0.2);
                width: 1000px;
                border: 1px solid rgba(255,255,255,0.2);
                backdrop-filter: blur(10px);
                animation: fadeIn 0.5s ease-out;
            }

            /* Header inside the form */
            .login-header {
                text-align: center;
                margin-bottom: 3rem;
            }
            .login-logo {
                font-size: 6rem;
                line-height: 1;
            }
            .login-title {
                font-size: 2.5rem;
                font-weight: 700;
                color: #333;
                margin-top: 1rem;
            }

            /* Inputs inside the form */
            div[data-testid="stForm"] .stTextInput input,
            div[data-testid="stForm"] .stTextInput input[type="password"] {
                font-size: 1.2rem;
                padding: 25px;
            }
            div[data-testid="stForm"] .stTextInput input:focus,
            div[data-testid="stForm"] .stTextInput input[type="password"]:focus {
                border-color: #0d6efd;
                box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25);
            }

            /* Button inside the form */
            div[data-testid="stForm"] .stButton>button {
                height: 3.2em;
                font-size: 1.2rem;
                font-weight: 700;
                margin-top: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # The CSS above targets the .block-container and turns it into a full-screen centering box for the form.
    with st.form("login_form"):
        st.markdown("""
            <div class="login-header">
                <div class="login-logo">⚖️</div>
                <h2 class="login-title">Sign in to Performance Comparison Dashboard</h2>
            </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username or email", placeholder="admin", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="password", label_visibility="collapsed")
        submitted = st.form_submit_button("Log In")

        if submitted:
            # Use environment variables for credentials with a fallback for local testing.
            valid_username = os.environ.get("APP_USERNAME", "admin")
            valid_password = os.environ.get("APP_PASSWORD", "password")
            if username == valid_username and password == valid_password:
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Invalid username or password.")
# --- UI DISPLAY FUNCTIONS ---
def get_openai_client():
    """Initializes and returns the AzureOpenAI client, handling errors."""
    try:
        # Read credentials exclusively from environment variables for security.
        api_key = os.environ.get("OPENAI_API_KEY")
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_version = os.environ.get("AZURE_API_VERSION")
        deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT")

        # Check if all required variables are set.
        if not all([api_key, azure_endpoint, api_version, deployment_name]):
             raise KeyError("One or more required OpenAI environment variables are not set.")

        client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        return client, deployment_name
    except KeyError:
        st.error("OpenAI credentials are not set up correctly in the environment.")
        st.info("For local development, create a `.env` file in your project root. For deployment, set these as Application Settings in your hosting provider.")
        return None, None

def display_summary_metrics(df: pd.DataFrame):
    """Displays summary metrics in columns."""
    st.markdown("### 📋 Summary Metrics")
    # Create up to 3 columns for metrics
    cols = st.columns(3)

    avg_resp_time = df['Average_Current'].mean()
    avg_resp_change = df['Avg_Change_%'].mean()
    cols[0].metric(
        "📊 Avg Response Time",
        f"{avg_resp_time:.2f} s",
        f"{avg_resp_change:.1f}%",
        delta_color="normal"
    )

    # Conditionally display throughput metric
    if 'Throughput_Current' in df.columns:
        avg_throughput = df['Throughput_Current'].mean()
        # Note: Percentage change for throughput is not calculated in this version.
        cols[1].metric("🚀 Avg Throughput", f"{avg_throughput:.2f} req/s")

    # Conditionally display error rate metric
    if 'Error %_Current' in df.columns:
        # Attempt to calculate mean for error rate, handle non-numeric data
        try:
            # Clean the series for calculation without modifying the original DataFrame
            error_series = pd.to_numeric(df['Error %_Current'].astype(str).str.replace('%', '', regex=False), errors='coerce')
            if not error_series.isnull().all():
                avg_error_rate = error_series.mean()
                cols[2].metric("📉 Avg Error Rate", f"{avg_error_rate:.2f}%")
        except (TypeError, AttributeError):
            pass # If conversion fails, do not display the metric

PERFORMANCE_SYSTEM_PROMPT = """You are 'Vibe', a friendly and insightful AI performance engineering assistant. Your personality is helpful, enthusiastic, and you love using emojis to make data fun 📊.
Your primary goal is to help users analyze performance test data.
- When asked for summaries or comparisons, present the data in clear markdown tables.
- Use bullet points for lists of findings.
- Start your responses with a friendly greeting (e.g., "Hello there!").
- Be concise but don't be afraid to add a concluding insightful comment.
You will be given a data summary as context with every user question. Use it to answer.
"""

def generate_proactive_summary(client, deployment_name, df: pd.DataFrame) -> str:
    """Generates a proactive, initial summary of the data for the chatbot."""
    # Create data context (similar to the main chat logic)
    context_parts = ["CONTEXT: Here is a summary of the performance data. Use this to generate a welcoming, proactive summary of the most important findings."]
    sort_col_diff = '90th_Diff' if '90th_Diff' in df.columns else 'Avg_Diff'
    basis = "90% Line" if '90th_Diff' in df.columns else "Average"

    downgraded_df = df[df[sort_col_diff] < 0].sort_values(by=sort_col_diff, ascending=True).head(3)
    if not downgraded_df.empty:
        context_parts.append(f"\n**Top 3 Downgrades (based on {basis} change in seconds):**")
        context_parts.append(downgraded_df[['Label', sort_col_diff]].to_markdown(index=False, floatfmt=".3f"))

    improved_df = df[df[sort_col_diff] > 0].sort_values(by=sort_col_diff, ascending=False).head(3)
    if not improved_df.empty:
        context_parts.append(f"\n**Top 3 Improvements (based on {basis} change in seconds):**")
        context_parts.append(improved_df[['Label', sort_col_diff]].to_markdown(index=False, floatfmt=".3f"))
    
    data_context = "\n".join(context_parts)

    prompt = "Hello Vibe! I've just analyzed the performance data. Please provide a brief, welcoming summary of the most important findings. Address the user directly and present the key changes clearly."
    
    api_messages = [
        {"role": "system", "content": PERFORMANCE_SYSTEM_PROMPT},
        {"role": "user", "content": f"{data_context}\n\n**Request:** {prompt}"}
    ]

    try:
        response = client.chat.completions.create(model=deployment_name, messages=api_messages, stream=False)
        return response.choices[0].message.content
    except Exception:
        return "Hello! I've analyzed your data and I'm ready to help. What would you like to know?"

def display_chatbot(df: pd.DataFrame):
    """Displays an interactive, proactive, and user-friendly chatbot powered by OpenAI."""
    client, deployment_name = get_openai_client()
    if not client:
        return

    # Initialize chat history and mode in session state
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": PERFORMANCE_SYSTEM_PROMPT}]
    # Ensure initial_summary_generated is always initialized
    if "initial_summary_generated" not in st.session_state:
        st.session_state.initial_summary_generated = False
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = "performance"
    
    # --- UI Header ---
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("### 🤖 AI Assistant")
    with col2:
        if st.button("🗑️ New Chat", use_container_width=True, help="Clears the chat and resets to Performance Analysis mode."):
            st.session_state.chat_mode = "performance"
            st.session_state.messages = [{"role": "system", "content": PERFORMANCE_SYSTEM_PROMPT}]
            st.session_state.initial_summary_generated = False
            if "processed_chat_doc_name" in st.session_state:
                del st.session_state["processed_chat_doc_name"]
            if "document_context" in st.session_state:
                del st.session_state["document_context"]
            st.rerun()

    # --- Mode Controller and File Uploader in a styled container ---
    with st.container(border=True):
        mode_text = "Performance Data Analysis"
        if st.session_state.chat_mode == "document":
            mode_text = f"Document Analysis: **{st.session_state.get('processed_chat_doc_name', 'N/A')}**"
        
        st.markdown(f"**Mode:** {mode_text}")
        
        uploaded_file = st.file_uploader(
            "To analyze a document, upload it here",
            type=['pdf', 'docx', 'txt', 'xlsx', 'xls'],
            key="chat_doc_uploader",
            label_visibility="collapsed"
        )

    # Process a new document if uploaded
    if uploaded_file and st.session_state.get("processed_chat_doc_name") != uploaded_file.name:
        with st.spinner(f"Analyzing '{uploaded_file.name}'..."):
            doc_text = extract_text_from_file(uploaded_file)
            st.session_state.chat_mode = "document"
            st.session_state.processed_chat_doc_name = uploaded_file.name
            st.session_state.document_context = doc_text
            st.session_state.messages = [
                {"role": "system", "content": f"You are an expert assistant analyzing the document '{uploaded_file.name}'. Answer questions based on its content, which will be provided with each prompt. Be helpful and answer accurately based on the provided text."}
            ]
            st.rerun()

    # --- Proactive Initial Analysis ---
    if not st.session_state.initial_summary_generated and not df.empty and st.session_state.chat_mode == "performance":
        with st.spinner("🤖 Vibe is performing an initial analysis..."):
            summary = generate_proactive_summary(client, deployment_name, df)
            if summary:
                st.session_state.messages.append({"role": "assistant", "content": summary})
        st.session_state.initial_summary_generated = True
        st.rerun()


    # Display chat messages from history
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message["content"])

    # Welcome message if chat is empty
    if len(st.session_state.messages) <= 1 and df.empty:
        st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #5f6368;">
                <h2 style="color: #202124; font-weight: 700;">Welcome to the AI Assistant!</h2>
                <p style="font-size: 1.2rem;">Upload your performance reports to get started.</p>
            </div>
        """, unsafe_allow_html=True)
    elif len(st.session_state.messages) <= 1 and not df.empty:
         st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #5f6368;">
                <h2 style="color: #202124; font-weight: 700;">Initial analysis complete!</h2>
                <p style="font-size: 1.2rem;">Ask me anything about the results, or upload a document to change modes.</p>
            </div>
        """, unsafe_allow_html=True)

    # --- Chat Input and Logic ---
    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            # --- Start of existing logic ---
            full_response = ""
            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            if st.session_state.get("chat_mode") == "document":
                doc_context = st.session_state.get("document_context", "")
                api_messages[-1]['content'] = f"CONTEXT: Here is the content of the document '{st.session_state.processed_chat_doc_name}'. Use it to answer the user's question.\n\n---\n\n{doc_context}\n\n---\n\n**User's Question:** {prompt}"
            else:
                data_context = ""
                if not df.empty:
                    context_parts = ["CONTEXT: Here is a summary of the performance data the user is looking at. Use this to answer their question."]
                    sort_col_diff = '90th_Diff' if '90th_Diff' in df.columns else 'Avg_Diff'
                    basis = "90% Line" if '90th_Diff' in df.columns else "Average"
                    downgraded_df = df[df[sort_col_diff] < 0].sort_values(by=sort_col_diff, ascending=True).head(3)
                    if not downgraded_df.empty:
                        context_parts.append(f"\n**Top 3 Downgrades (based on {basis} change in seconds):**")
                        context_parts.append(downgraded_df[['Label', sort_col_diff]].to_markdown(index=False, floatfmt=".3f"))
                    improved_df = df[df[sort_col_diff] > 0].sort_values(by=sort_col_diff, ascending=False).head(3)
                    if not improved_df.empty:
                        context_parts.append(f"\n**Top 3 Improvements (based on {basis} change in seconds):**")
                        context_parts.append(improved_df[['Label', sort_col_diff]].to_markdown(index=False, floatfmt=".3f"))
                    data_context = "\n".join(context_parts)
                api_messages[-1]['content'] = f"{data_context}\n\n**User's Question:** {prompt}"
            
            message_placeholder.markdown("🤖 Vibe is analyzing...")
            full_response = ""
            try:
                stream = client.chat.completions.create(model=deployment_name, messages=api_messages, stream=True)
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"An error occurred with the OpenAI API: {e}")
                full_response = "I'm sorry, I encountered an error. Please check your API credentials and connection."
                message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()

def display_deep_dive(df: pd.DataFrame):
    """Displays a detailed analysis view for a single selected transaction."""
    st.markdown("### 🔎 Transaction Deep Dive")
    st.write("Select a single transaction to see a detailed performance breakdown and comparison.")

    # --- Transaction Selector ---
    # Add a search box to filter the transaction list, making it easier to find an item in a long list.
    search_query = st.text_input(
        "Search for a transaction to analyze below",
        key="deep_dive_search",
        placeholder="e.g., login, add_to_cart"
    )

    if search_query:
        transaction_list = sorted([label for label in df['Label'].unique() if search_query.lower() in label.lower()])
    else:
        transaction_list = sorted(df['Label'].unique())


    selected_transaction = st.selectbox("Select a Transaction from the (filtered) list", transaction_list, index=None, placeholder="Choose a transaction...", help="The list is filtered by your search above.")

    if not selected_transaction:
        st.info("Please select a transaction from the dropdown to see the deep dive analysis.")
        return

    # Filter data for the selected transaction
    transaction_data = df[df['Label'] == selected_transaction].iloc[0]

    st.markdown(f"#### Analysis for: **{selected_transaction}**")

    # --- Key Metrics Comparison ---
    with st.container(border=True):
        st.markdown("##### ⚖️ Key Metrics Comparison")
        cols = st.columns(4)
        if 'Min_Diff' in transaction_data:
            cols[0].metric("Min Response Time", f"{transaction_data['Min_Current']:.2f}s", f"{transaction_data['Min_Diff']:.2f}s", delta_color="normal")
        if '90th_Diff' in transaction_data:
            cols[1].metric("90% Line Response Time", f"{transaction_data['90% Line_Current']:.2f}s", f"{transaction_data['90th_Diff']:.2f}s", delta_color="normal")
        if 'Max_Diff' in transaction_data:
            cols[2].metric("Max Response Time", f"{transaction_data['Max_Current']:.2f}s", f"{transaction_data['Max_Diff']:.2f}s", delta_color="normal")
        if 'Error %_Current' in transaction_data and 'Error %_Previous' in transaction_data:
            err_curr = float(str(transaction_data.get('Error %_Current', '0.0')).replace('%',''))
            err_prev = float(str(transaction_data.get('Error %_Previous', '0.0')).replace('%',''))
            err_diff = err_prev - err_curr # Flipped to show improvement as positive
            cols[3].metric("Error Rate", f"{err_curr:.2f}%", f"{err_diff:.2f}%", delta_color="normal")

    # --- Percentile Shape Plot ---
    with st.container(border=True):
        st.markdown("##### 📈 Percentile Shape Comparison")
        st.markdown("This chart compares different percentile points to show how the *shape* of the response time distribution has changed. A large gap in the higher percentiles (90%, 99%) indicates more outliers in one test.")
        
        percentile_metrics = {'Min': 'Min', '90% Line': '90% Line', '95% Line': '95% Line', '99% Line': '99% Line', 'Max': 'Max'}
        current_values, previous_values, labels = [], [], []

        for label, col_name in percentile_metrics.items():
            if f"{col_name}_Current" in transaction_data and f"{col_name}_Previous" in transaction_data:
                labels.append(label)
                current_values.append(transaction_data[f"{col_name}_Current"])
                previous_values.append(transaction_data[f"{col_name}_Previous"])

        if labels:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=labels, y=previous_values, name="Previous", marker_color='#ff9800'))
            fig.add_trace(go.Bar(x=labels, y=current_values, name="Current", marker_color='#00bcd4'))
            fig.update_layout(barmode='group', yaxis_title="Response Time (s)", template="plotly_white", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough percentile data (e.g., 90% Line, 95% Line) available in both reports to generate a shape comparison chart.")

def display_new_missing_transactions(new: list, missing: list):
    """Displays lists of new and missing transactions in columns."""
    if not new and not missing:
        return # Don't show the section if there's nothing to report

    st.markdown("### 🔄 Transaction Changes")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown(f"#### ✨ {len(new)} New Transactions")
            st.markdown("These transactions are in the 'Current' report but not in the 'Previous' one.")
            st.json(new, expanded=False)
    with col2:
        with st.container(border=True):
            st.markdown(f"#### 💨 {len(missing)} Missing Transactions")
            st.markdown("These transactions were in the 'Previous' report but are missing from the 'Current' one.")
            st.json(missing, expanded=False)

def display_observations(df: pd.DataFrame, sla_breach_count: int, sla_threshold: float):
    """Analyzes the data and provides a detailed summary of observations based on 90% Line comparison."""
    st.markdown("### 📝 Key Comparison Insights")

    # The entire observation section will be based on 90% Line data if available.
    if '90th_Change_%' not in df.columns:
        st.info("Detailed observations require the '90% Line' column in both reports.")
        return

    observations = []

    # Overall Trend based on 90% Line
    avg_90th_change = df['90th_Change_%'].mean()
    if avg_90th_change > 5: # Positive is now improvement
        observations.append(f"<li>✅ **Overall 90% Line Improvement:** On average, the 90% Line response time has improved by **{avg_90th_change:.1f}%**.</li>")
    elif avg_90th_change < -5: # Negative is now regression
        observations.append(f"<li>🚨 **Overall 90% Line Regression:** On average, the 90% Line response time has regressed by **{abs(avg_90th_change):.1f}%**, indicating a general performance degradation.</li>")
    else:
        observations.append(f"<li>⚖️ **Stable Overall 90% Line Performance:** The average change in 90% Line response time is minimal (**{avg_90th_change:.1f}%**).</li>")

    # Count of Improved vs. Regressed
    improved_df = df[df['90th_Diff'] > 0] # Positive diff is now improvement
    downgraded_df = df[df['90th_Diff'] < 0] # Negative diff is now downgrade
    observations.append(f"<li>📊 **Transaction-Level Changes:** Out of {len(df)} transactions, **{len(improved_df)} improved** while **{len(downgraded_df)} downgraded** based on the 90% Line.</li>")

    # Magnitude of Change
    if not improved_df.empty:
        avg_improvement = improved_df['90th_Change_%'].mean()
        observations.append(f"<li>📈 **Magnitude of Improvement:** The improved transactions saw an average performance gain of **{avg_improvement:.1f}%**.</li>")
    if not downgraded_df.empty:
        avg_downgrade = abs(downgraded_df['90th_Change_%'].mean())
        observations.append(f"<li>📉 **Magnitude of Downgrade:** The downgraded transactions saw an average performance loss of **{avg_downgrade:.1f}%**.</li>")

    # SLA Breach Summary
    if sla_breach_count > 0:
        observations.append(f"<li>⚠️ **SLA Breaches:** **{sla_breach_count}** transaction(s) are exceeding the 90% Line SLA threshold of **{sla_threshold:.1f}s** in the current test.</li>")
    else:
        observations.append(f"<li>👍 **No SLA Breaches:** All transactions are within the 90% Line SLA threshold.</li>")

    # Top Movers Analysis
    if not downgraded_df.empty:
        top_downgraded = downgraded_df.sort_values(by='90th_Diff', ascending=True).head(3)
        obs_text = "<li>🔻 **Most Significant Downgrades:** The following transactions showed the largest performance decrease:<ul style='margin-left: 20px;'>"
        for _, row in top_downgraded.iterrows():
            obs_text += f"<li>**{row['Label']}** downgraded by **{abs(row['90th_Diff']):.2f}s** (from {row['90% Line_Previous']:.2f}s to {row['90% Line_Current']:.2f}s).</li>"
        obs_text += "</ul></li>"
        observations.append(obs_text)

    if not improved_df.empty:
        top_improved = improved_df.sort_values(by='90th_Diff', ascending=False).head(3)
        obs_text = "<li>🔺 **Most Significant Improvements:** The following transactions showed the largest performance improvement:<ul style='margin-left: 20px;'>"
        for _, row in top_improved.iterrows():
            obs_text += f"<li>**{row['Label']}** improved by **{row['90th_Diff']:.2f}s** (from {row['90% Line_Previous']:.2f}s to {row['90% Line_Current']:.2f}s).</li>"
        obs_text += "</ul></li>"
        observations.append(obs_text)

    if observations:
        st.markdown("<div class='insights-box'>"
                    "<ul>" + "".join(observations) + "</ul></div>", unsafe_allow_html=True)

def display_sla_breaches(df: pd.DataFrame, threshold: float):
    """Filters and displays transactions breaching the 90% Line SLA."""
    st.markdown("### ⚠️ SLA Breaches (Based on 90% Line)")

    if 'SLA' not in df.columns or df['SLA'].eq('N/A').all():
        st.info("SLA breach analysis requires '90% Line' column in both reports.")
        return

    sla_breaches = df[df["SLA"].str.contains("BREACH")]
    if not sla_breaches.empty:
        st.dataframe(
            sla_breaches[["Label", "90% Line_Current", "SLA"]].rename(
                columns={
                    "Label": "Transaction",
                    "90% Line_Current": f"90% Line (s) > {threshold:.1f}s"
                }
            )
        )
        st.caption("💡 Click on column headers to sort the table.")
    else:
        st.success("✅ No SLA breaches found.")

def display_detailed_transaction_table(df: pd.DataFrame):
    """Displays a detailed, filterable table of current performance metrics."""
    st.markdown("### 🔎 Current Test - Detailed Transaction View")

    cols_to_display = {"Label": "Transaction"}
    if 'Min_Current' in df.columns:
        cols_to_display['Min_Current'] = "Min (s)"
    if 'Average_Current' in df.columns:
        cols_to_display['Average_Current'] = "Average (s)"
    if 'Max_Current' in df.columns:
        cols_to_display['Max_Current'] = "Max (s)"
    if '90% Line_Current' in df.columns:
        cols_to_display['90% Line_Current'] = "90% Line (s)"
    if 'Error %_Current' in df.columns:
        cols_to_display['Error %_Current'] = "Error %"

    if len(cols_to_display) > 1:
        detailed_df = df[list(cols_to_display.keys())].rename(columns=cols_to_display)

        # Add a search box for this specific table
        table_search_term = st.text_input("Filter transactions in the table below:", key="detailed_table_search")
        if table_search_term:
            detailed_df = detailed_df[detailed_df["Transaction"].str.contains(table_search_term, case=False)]

        st.dataframe(detailed_df, use_container_width=True)
        st.caption("💡 Click on column headers to sort the table.")
    else:
        st.info("Detailed transaction data (Min, Max, 90% Line, Error %) not found in the current report.")

def display_average_comparison(df: pd.DataFrame):
    """Displays a single, filterable, and sortable table for Average response time comparison."""
    if 'Avg_Diff' not in df.columns:
        return  # Don't display section if data is not available

    st.markdown("### ⚖️ Average Response Time Comparison")

    # Create the comparison dataframe
    comparison_df = df[['Label', 'Average_Previous', 'Average_Current', 'Avg_Diff', 'Avg_Change_%']].copy()
    comparison_df.rename(columns={
        'Label': 'Transaction',
        'Average_Previous': 'Previous Average (s)',
        'Average_Current': 'Current Average (s)',
        'Avg_Diff': 'Change (s)',
        'Avg_Change_%': 'Change (%)'
    }, inplace=True)

    # Add status column
    comparison_df['Status'] = np.where(comparison_df['Change (s)'] > 0, '✅ Improved', '❌ Downgraded')
    comparison_df.loc[comparison_df['Change (s)'] == 0, 'Status'] = '⚖️ No Change'

    # Reorder columns to place 'Change (%)' before 'Status'
    comparison_df = comparison_df[['Transaction', 'Previous Average (s)', 'Current Average (s)', 'Change (s)', 'Change (%)', 'Status']]

    # Add filtering and sorting controls
    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("Search Transaction", key="avg_search")
    with col2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=sorted(comparison_df['Status'].unique()),
            default=sorted(comparison_df['Status'].unique()),
            key="avg_status_filter"
        )
    with col3:
        sort_by = st.selectbox("Sort by", options=['Transaction', 'Change (s)', 'Change (%)'], key="avg_sort")

    # Apply filters and sorting
    filtered_df = comparison_df
    if search_query:
        filtered_df = filtered_df[filtered_df['Transaction'].str.contains(search_query, case=False)]
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    sorted_df = filtered_df.sort_values(by=sort_by, ascending=(sort_by == 'Transaction'))

    # Add download button for the filtered and sorted data
    csv = convert_df_to_csv(sorted_df)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name='average_comparison.csv',
        mime='text/csv',
        key='download_avg_csv'
    )

    # Style and display the dataframe
    def color_change(val):
        # Positive is green (good), negative is red (bad)
        color = '#4caf50' if val > 0 else ('#f44336' if val < 0 else '#333333')
        return f'color: {color}; font-weight: bold;'

    st.dataframe(sorted_df.style.format({
        'Previous Average (s)': "{:.3f}",
        'Current Average (s)': "{:.3f}",
        'Change (s)': "{:+.3f}",
        'Change (%)': '{:+.2f}%'
    }).map(color_change, subset=['Change (s)', 'Change (%)']), use_container_width=True)

def display_percentile_comparison(df: pd.DataFrame):
    """Displays a single, filterable, and sortable table for 90% Line comparison."""
    if '90th_Diff' not in df.columns or '90th_Change_%' not in df.columns:
        return  # Don't display section if data is not available

    st.markdown("### ⚖️ 90% Line Performance Comparison")

    # Create the comparison dataframe
    comparison_df = df[['Label', '90% Line_Previous', '90% Line_Current', '90th_Diff', '90th_Change_%']].copy()
    comparison_df.rename(columns={
        'Label': 'Transaction',
        '90% Line_Previous': 'Previous 90% Line (s)',
        '90% Line_Current': 'Current 90% Line (s)',
        '90th_Diff': 'Change (s)',
        '90th_Change_%': 'Change (%)'
    }, inplace=True)

    # Add status column
    comparison_df['Status'] = np.where(comparison_df['Change (s)'] > 0, '✅ Improved', '❌ Downgraded')
    comparison_df.loc[comparison_df['Change (s)'] == 0, 'Status'] = '⚖️ No Change'

    # Reorder columns to place 'Change (%)' before 'Status'
    comparison_df = comparison_df[['Transaction', 'Previous 90% Line (s)', 'Current 90% Line (s)', 'Change (s)', 'Change (%)', 'Status']]

    # Add filtering and sorting controls
    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("Search Transaction", key="p90_search")
    with col2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=sorted(comparison_df['Status'].unique()),
            default=sorted(comparison_df['Status'].unique()),
            key="p90_status_filter"
        )
    with col3:
        sort_by = st.selectbox("Sort by", options=['Transaction', 'Change (s)', 'Change (%)'], key="p90_sort")

    # Apply filters and sorting
    filtered_df = comparison_df
    if search_query:
        filtered_df = filtered_df[filtered_df['Transaction'].str.contains(search_query, case=False)]
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    sorted_df = filtered_df.sort_values(by=sort_by, ascending=(sort_by == 'Transaction'))

    # Add download button for the filtered and sorted data
    csv = convert_df_to_csv(sorted_df)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name='90th_line_comparison.csv',
        mime='text/csv',
        key='download_p90_csv'
    )

    # Style and display the dataframe
    def color_change(val):
        # Positive is green (good), negative is red (bad)
        color = '#4caf50' if val > 0 else ('#f44336' if val < 0 else '#333333')
        return f'color: {color}; font-weight: bold;'

    st.dataframe(sorted_df.style.format({
        'Previous 90% Line (s)': "{:.3f}", 'Current 90% Line (s)': "{:.3f}", 'Change (s)': "{:+.3f}", 'Change (%)': '{:+.2f}%'
    }).map(color_change, subset=['Change (s)', 'Change (%)']), use_container_width=True)

def display_comparison_charts(df: pd.DataFrame):
    """Displays all comparison charts for available data."""
    st.markdown("### 📈 Performance Comparison Charts")

    # Add sort option for the main chart
    sort_option = st.selectbox(
        "Sort charts by:",
        ('Transaction Name', 'Current Value', 'Previous Value'),
        key='chart_sort'
    )
    # Display 90% Line chart if available
    if '90% Line_Current' in df.columns and '90% Line_Previous' in df.columns:
        fig = create_comparison_fig(df, '90% Line_Current', '90% Line_Previous', '90% Line Response Time Comparison', 'Response Time (s)', sort_option)
        st.plotly_chart(fig, use_container_width=True)

    # Always display the Average chart as it's a required metric
    fig = create_comparison_fig(df, 'Average_Current', 'Average_Previous', 'Average Response Time Comparison', 'Response Time (s)', sort_option)
    st.plotly_chart(fig, use_container_width=True)

    chart_configs = {
        "Throughput": {"emoji": "🚀", "unit": "Requests/sec"},
        "Error %": {"emoji": "📉", "unit": "Error Rate (%)"}
    }

    # Create a copy for manipulation to avoid changing the original dataframe
    df_for_charts = df.copy()

    for metric, config in chart_configs.items():
        current_col = f'{metric}_Current'
        previous_col = f'{metric}_Previous'

        if current_col in df_for_charts.columns and previous_col in df_for_charts.columns:
            # For Error %, attempt to convert to numeric for plotting.
            if metric == "Error %":
                try:
                    df_for_charts[current_col] = pd.to_numeric(df_for_charts[current_col].astype(str).str.replace('%', '', regex=False), errors='coerce')
                    df_for_charts[previous_col] = pd.to_numeric(df_for_charts[previous_col].astype(str).str.replace('%', '', regex=False), errors='coerce')
                except (TypeError, AttributeError):
                    # If conversion fails for any reason, skip this chart
                    continue

            # Check if there is anything to plot after potential coercion
            if df_for_charts[current_col].notna().any() or df_for_charts[previous_col].notna().any():
                st.markdown(f"### {config['emoji']} {metric} Comparison")
                fig = create_comparison_fig(df_for_charts, current_col, previous_col, f'{metric} Comparison', config['unit'], sort_option)
                st.plotly_chart(fig, use_container_width=True)

# --- MAIN DASHBOARD PAGE ---
def main_dashboard():
    """The main dashboard application logic."""
    # Sidebar controls
    st.sidebar.title("🎛️ Dashboard Controls")
    if st.sidebar.button("🚪 Log out"):
        st.session_state.logged_in = False
        st.rerun()

    if st.sidebar.button("🔄 Refresh"):
        st.rerun()

    # Add a reset button
    if st.sidebar.button("🗑️ Reset & Upload New"):
        for key in ['current_file', 'previous_file']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    sla_threshold_s = st.sidebar.number_input("⏱️ SLA Threshold (s)", min_value=0.1, value=3.0, step=0.1)
    search_term = st.sidebar.text_input("🔍 Search Transaction", help="Filter transactions by name (case-insensitive).")

    # Title
    st.title("📊 Performance Comparison Dashboard")

    # File upload for performance comparison
    with st.expander("📁 Upload Performance Reports", expanded=True):
        col1, col2 = st.columns(2)
        current_file = col1.file_uploader("📤 Current Test Report", type=["csv"], key="current_file")
        previous_file = col2.file_uploader("📥 Previous Test Report", type=["csv"], key="previous_file")

    if current_file and previous_file:
        try:
            merged_df, new_transactions, missing_transactions = load_and_process_data(current_file, previous_file)

            # SLA Breach calculation based on 90% Line
            if '90% Line_Current' in merged_df.columns:
                merged_df["SLA"] = merged_df["90% Line_Current"].apply(lambda x: "🚨 BREACH" if x > sla_threshold_s else "✅ OK")
            else:
                # Fallback if column is missing
                merged_df["SLA"] = "N/A"

            display_df = filter_dataframe(merged_df, search_term)

            if display_df.empty:
                st.warning("No transactions match the search term.")
            else:
                sla_breach_count = display_df["SLA"].eq("🚨 BREACH").sum()

                st.markdown("---")
                display_summary_metrics(display_df)
                st.markdown("---")

                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "🤖 **AI Assistant**",
                    "📊 **Summary & Insights**",
                    "🔎 **Deep Dive**",
                    "📋 **Detailed Comparison**",
                    "📈 **Charts**",
                    "⚠️ **SLA Breaches**",
                ])

                with tab1: display_chatbot(display_df)
                with tab2:
                    display_observations(display_df, sla_breach_count, sla_threshold_s)
                    display_new_missing_transactions(new_transactions, missing_transactions)
                with tab3: display_deep_dive(display_df)
                with tab4:
                    display_detailed_transaction_table(display_df)
                    st.markdown("<br>", unsafe_allow_html=True)
                    display_average_comparison(display_df)
                    st.markdown("<br>", unsafe_allow_html=True)
                    display_percentile_comparison(display_df)
                with tab5: display_comparison_charts(display_df)
                with tab6: display_sla_breaches(display_df, sla_threshold_s)

        except (KeyError, Exception) as e:
            st.error(f"An error occurred while processing the files: {e}")
            st.info("Please ensure both CSV files contain the required columns: 'Label', 'Average'. Optional columns: 'Min', 'Max', '90% Line', 'Error %', 'Throughput'.")

    else:
        st.info("👋 Welcome! Please upload both current and previous test reports to begin analysis.")

# --- SCRIPT EXECUTION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    main_dashboard()
