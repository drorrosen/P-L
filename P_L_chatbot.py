import pandas as pd
import streamlit as st
import base64
from openai import OpenAI
import io
import time
import traceback
from PIL import Image
import re  # Added for regex processing

# --- Page Configuration ---
st.set_page_config(
    page_title="omniXM Financial Insights",
    initial_sidebar_state="expanded",

)

# --- Initialize Session State ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'openai_key' not in st.session_state:
    st.session_state.openai_key = ""
if 'model_choice' not in st.session_state:
    st.session_state.model_choice = "gpt-4o-mini"
if 'analysis_prompt' not in st.session_state:
    # Default analysis prompt updated with more concise, analyst-focused language
    st.session_state.analysis_prompt = """You are a financial analyst expert in P&L statement analysis.

Analyze this dataset and provide concise, actionable insights focusing on:
- Key trends in profitability and revenue
- Notable changes in expenses (OPEX, labor costs, etc.)
- Highlight any subsidy impacts
- Create visualizations that best illustrate important patterns

Be direct and business-focused in your analysis. Clearly label insights and recommendations."""
if 'results_area' not in st.session_state:
    st.session_state['results_area'] = None  # Will be set in the main UI section
if 'initial_display' not in st.session_state:
    st.session_state['initial_display'] = True
if 'specific_question' not in st.session_state:
    st.session_state['specific_question'] = ""

# --- Login Credentials ---
CORRECT_USERNAME = "omnixm123"
CORRECT_PASSWORD = "1234567"

# --- Authentication function ---
def authenticate(username, password):
    return username == CORRECT_USERNAME and password == CORRECT_PASSWORD

# --- Custom CSS Styling including Login styles ---
def local_css():
    # Updated CSS to match code_interpreter_app.py (HubSpot/SaaS style)
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
        color: #33475b; /* HubSpot dark blue text */
    }
    
    /* App Background and Layout */
    .stApp {
        /* Keep the gradient background from P_L_chatbot original */
        background: linear-gradient(145deg, #ff7a59 0%, #ff9980 30%, #eaf5ff 70%, #ffffff 100%);
    }
    
    /* Main Content Container */
    .main .block-container {
        padding: 2rem 3rem !important; /* Ensure padding */
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Login styles */
    /* Center the login card within the layout */
    section[data-testid="stSidebar"] + section div[data-testid="stVerticalBlock"] {
        display: flex;
        flex-direction: column;
        align-items: center; /* Center children horizontally */
        padding-top: 0;      /* Remove top padding */
    }
    
    .login-card {
        background-color: white;
        padding: 2.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        width: 100%;         /* Fill container width */
        margin-top: 1rem;    /* Reduced top margin */
    }
    
    /* Remove default margins and padding from Streamlit columns in login */
    [data-testid="column"] {
        padding: 0 !important;
        margin-top: 0 !important;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-title {
        color: #33475b;
        font-weight: 600;
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
    }
    
    .login-subtitle {
        color: #516f90;
        font-size: 1rem;
    }
    
    .error-message {
        color: #e34c4c;
        background-color: #ffeae5;
        border-left: 3px solid #e34c4c;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        margin-bottom: 1.5rem;
        font-size: 0.9rem;
    }
    
    .login-footer {
        text-align: center;
        margin-top: 2rem;
        color: #516f90;
        font-size: 0.85rem;
    }
    
    /* Header Styling */
    h1, h2, h3, h4, h5, h6 {
        color: #33475b;
        font-weight: 600;
    }
    
    h1 { /* Your custom header handles H1, keep this less specific */
        font-size: 2.2rem;
        margin-bottom: 1.5rem;
    }
    
    h2 { /* Section headers like "Ask a Specific Question", "Analysis Output" */
        font-size: 1.8rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #eaf0f6; /* Lighter border */
        padding-bottom: 0.5rem;
    }
    
    h3 { /* Sub-headers like "Data Summary" */
        font-size: 1.4rem;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
    }
    
    /* Custom Header Specific Styling (Keep Existing Structure) */
    .app-header {
        padding: 1.5rem 0; /* Reduced padding */
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 0.5rem;
        margin-bottom: 1rem; /* Reduced margin */
        text-align: center;
        background: transparent; /* Ensure transparent background */
    }
    .logo-text {
        font-size: 3rem; font-weight: 700; color: white; margin: 0; padding: 0; letter-spacing: -0.05em;
    }
    .logo-text span { color: #00a4bd; }
    .logo-subtitle {
        font-size: 1.2rem; color: white; margin: 0; padding: 0; font-weight: 400; letter-spacing: 0.05em;
    }
    .main-tagline {
        font-size: 1.4rem; /* Slightly smaller */
        text-align: center; 
        color: white; 
        margin-top: 0.5rem; /* Reduced margin */
        margin-bottom: 1rem; /* Reduced margin */
        font-weight: 500;
    }

    /* Sidebar Styling (Merge Styles) */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eaeef2;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding: 1rem; /* Use padding from code_interpreter_app */
    }
    [data-testid="stSidebar"] h2 { /* Settings title */
        font-size: 1.5rem; color: #33475b; /* Match main headers */
        margin-top: 0; margin-bottom: 1rem; padding-bottom: 0.75rem;
        border-bottom: 1px solid #eaeef2;
    }
    [data-testid="stSidebar"] h4 { /* API Key, Model, Prompt titles */
        font-size: 1.1rem; color: #33475b; margin-top: 1rem;
        margin-bottom: 0.5rem; font-weight: 600;
    }

    /* Buttons - Use HubSpot orange primary */
    .stButton > button {
        background-color: #ff7a59; /* HubSpot orange */
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        font-weight: 600;
        color: white;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(255, 122, 89, 0.2);
        width: 100%;
        margin-bottom: 0.5rem; /* Keep bottom margin */
    }
    .stButton > button:hover {
        background-color: #ff8f73; /* Lighter orange */
        box-shadow: 0 4px 8px rgba(255, 122, 89, 0.3);
        transform: translateY(-1px);
    }
    .stButton > button:active {
        background-color: #e05e39; /* Darker orange */
        transform: translateY(0);
    }
    /* Apply secondary style to the main analysis button if needed, otherwise primary */
    /* Your code uses secondary-button class - let's style it explicitly */
    .secondary-button button { /* Make Run Analysis button primary */
        /* Inherits primary style above */
    }
    /* Style for Reset button in sidebar (like secondary) */
    [data-testid="stSidebar"] .stButton:has(button > div > p:contains('Reset')) button {
         background-color: #fff;
         color: #33475b;
         border: 1px solid #cbd6e2;
         box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
     [data-testid="stSidebar"] .stButton:has(button > div > p:contains('Reset')) button:hover {
         background-color: #f5f8fa;
         box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
         transform: translateY(-1px); /* Keep hover effect */
    }
    
    /* Text Inputs */
    .stTextInput > div > div > input, .stTextArea textarea {
        border-radius: 4px;
        border: 1px solid #cbd6e2;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    .stTextInput > div > div > input:focus, .stTextArea textarea:focus {
        border-color: #ff7a59; /* Orange focus */
        box-shadow: 0 0 0 2px rgba(255, 122, 89, 0.2);
        outline: none;
    }
    .stTextArea textarea {
        min-height: 150px; /* Adjust default height */
        font-size: 0.9rem;
    }
    
    /* Cards (Use HubSpot style) */
    .card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        padding: 1.5rem; /* Use padding from code_interpreter_app */
        margin-bottom: 1.5rem;
    }
    /* Apply card style to specific question section */
    /* Handled by adding class='card' in the markdown */

    /* Results section styling */
    .results-header { /* Keep this selector for the H2 */
        color: #33475b; /* Match other H2s */
        border-bottom: 2px solid #eaf0f6; /* Match H2 style */
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1.8rem; /* Ensure size consistency */
    }
    
    /* Results card styling (Use standard card style) */
    .results-card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        padding: 1.5rem;
        margin-bottom: 1.5rem; /* Add margin if needed */
        /* border-left: 4px solid #00a4bd; /* Remove specific border */
    }
    
    /* Thinking Process Display (Adapt from progress-container) */
    .thinking-container {
        background-color: white; /* Match card background */
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05); /* Match card shadow */
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #00a4bd; /* Keep the accent color */
        max-height: 400px;
        overflow-y: auto;
    }
    .thinking-container h4 { /* Style the title */
        font-size: 1.2rem;
        font-weight: 600;
        color: #33475b;
        margin-bottom: 1rem;
        margin-top: 0; /* Remove extra top margin */
    }
    .thinking-step {
        padding: 0.5rem 0;
        border-bottom: 1px dashed #eaeef2;
        font-size: 0.9rem;
    }
    .thinking-step:last-child { border-bottom: none; }
    .thinking-title { /* Step type like "Data Preparation" */
        font-weight: 600;
        color: #00a4bd; /* Use accent color */
        margin-bottom: 0.3rem;
        display: block; /* Ensure block display */
    }
    /* Status Placeholder Styling (Adapt from info/error boxes) */
    .stAlert {
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
        border-left-width: 4px;
        border-left-style: solid;
    }
    .stAlert[data-baseweb="alert"][role="alert"] > div:first-child { display: none; } /* Hide default icon */
    
    .stAlert[data-testid="stInfo"] {
        background-color: #eaf5ff; border-left-color: #0091ae; color: #33475b;
    }
    .stAlert[data-testid="stSuccess"] {
        background-color: #edf8f0; border-left-color: #00bf6f; color: #33475b;
    }
    .stAlert[data-testid="stWarning"] {
        background-color: #fef8e3; border-left-color: #ffc21d; color: #33475b;
    }
     .stAlert[data-testid="stError"] {
        background-color: #ffeae5; border-left-color: #ff7a59; /* Orange error */ color: #33475b;
    }

    /* For DataFrames */
    .stDataFrame {
        border: 1px solid #eaf0f6;
        border-radius: 6px;
        overflow: hidden;
        margin-bottom: 1rem; /* Add margin */
    }
    .stDataFrame [data-testid="stTable"] {
        border-collapse: separate; border-spacing: 0;
    }
    .stDataFrame th {
        background-color: #f5f8fa; color: #33475b; font-weight: 600;
        padding: 12px; text-align: left; border-bottom: 1px solid #eaf0f6;
        font-size: 0.9rem; /* Match code_interpreter */
    }
    .stDataFrame td {
        padding: 12px; border-bottom: 1px solid #f5f8fa; font-size: 0.9rem;
    }
    
    /* Plots / Images */
    [data-testid="stPlotlyChart"], .stImage {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05); /* Match card shadow */
        margin-bottom: 1rem;
    }
    
    /* Dividers */
    hr {
        border-color: #eaf0f6; /* Lighter divider */
        margin: 1.5rem 0;
    }
    
    /* Expander styling (for Debug section) */
    .streamlit-expanderHeader {
        font-size: 0.9rem;
        color: #516f90; /* Match code_interpreter footer/secondary text */
        background-color: #f5f8fa; /* Match background */
        border-radius: 4px;
        padding: 0.5rem 1rem;
        border: 1px solid #eaf0f6; /* Add light border */
    }
    .debug-section { /* Style content inside expander */
         font-size: 0.8rem; color: #516f90; padding: 0.5rem;
    }
    
    /* Highlight subsidy (Keep specific style but use orange) */
    .highlight-subsidy {
        font-weight: 600;
        color: #e05e39; /* Darker orange */
        background-color: rgba(255, 122, 89, 0.1);
        padding: 0.1rem 0.3rem;
        border-radius: 3px; /* Slightly rounder */
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        margin-top: 3rem;
        color: #7c98b6; /* Match code_interpreter footer */
        font-size: 0.9rem;
        border-top: 1px solid #eaf0f6; /* Lighter top border */
        /* background: linear-gradient(90deg, #00a4bd 0%, #0091ae 100%); /* Remove gradient */
    }
     .footer span { /* Style colored spans in footer */
          font-weight: 500;
     }

    /* KPI Cards (Adapt from card style) */
    .kpi-card {
        background-color: white;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: all 0.2s ease;
        border-top: 3px solid #00a4bd; /* Keep top border accent */
    }
    .kpi-card:hover {
        transform: translateY(-3px); /* Slightly more lift */
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    .kpi-value {
        font-size: 2rem; /* Slightly smaller */
        font-weight: 700;
        color: #33475b; /* Dark blue value */
        margin-bottom: 0.25rem;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #516f90; /* Secondary text color */
    }
    
    /* Negative/Positive values (Keep existing) */
    .negative-value { color: #e34c4c; }
    .positive-value { color: #00bf6f; }
    
    /* Custom spinner (Keep existing) */
    .stSpinner > div > div {
        border-top-color: #ff7a59 !important;
    }
    
    /* Specific Question Input */
    .stTextInput[aria-label="Your specific question:"] input { /* Target specifically */
        /* Inherits general input style */
        font-size: 1rem; /* Ensure font size */
    }
     label[for^="specific_question_input"] { /* Style the label */
          font-weight: 600;
          color: #33475b;
          margin-bottom: 0.5rem;
          display: block;
     }

    /* Example Questions Styling */
    .stColumns h5 { /* Style the "Example Questions:" header */
         font-size: 1rem;
         font-weight: 600;
         color: #516f90;
         margin-top: 1rem;
         margin-bottom: 0.5rem;
     }
     .stColumns ul {
         font-size: 0.9rem;
         color: #5a6e84;
         padding-left: 1.2rem; /* Indent list */
         margin-top: 0;
         margin-bottom: 1rem;
     }
     .stColumns li {
         margin-bottom: 0.3rem;
     }

    /* Markdown Content in results */
    .results-card .stMarkdown h1, .results-card .stMarkdown h2, .results-card .stMarkdown h3, 
    .results-card .stMarkdown h4, .results-card .stMarkdown h5, .results-card .stMarkdown h6 {
        color: #33475b; margin-top: 1.5rem; margin-bottom: 1rem;
    }
    .results-card .stMarkdown p {
        color: #5a6e84; line-height: 1.6; margin-bottom: 1rem;
    }
    .results-card .stMarkdown a {
        color: #ff7a59; text-decoration: none;
    }
    .results-card .stMarkdown a:hover { text-decoration: underline; }
    .results-card .stMarkdown ul, .results-card .stMarkdown ol {
        margin-bottom: 1rem; color: #5a6e84; padding-left: 1.5rem;
    }

    /* Login page specific overrides */
    .stApp [data-testid="block-container"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove white space in login page */
    .stApp [data-testid="element-container"] {
        margin-bottom: 0 !important;
    }
    
    /* Make sure login form elements align nicely */
    .login-card .stTextInput, .login-card .stButton, .login-card .stCheckbox {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    </style>
    """, unsafe_allow_html=True)

# Apply the CSS
local_css()

# --- Helper Functions ---
def format_currency(value):
    if pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"

def format_percentage(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2%}"

def highlight_subsidy(text):
    """Adds highlight styling to the word 'subsidy' in text."""
    if not isinstance(text, str):
        return text
    
    # Use regex for more robust replacement (case-insensitive)
    pattern = re.compile(r'subsid(y|ies)', re.IGNORECASE)
    return pattern.sub(r'<span class="highlight-subsidy">\g<0></span>', text)

# Custom logo and header - Updated to match omnixm.com
def create_header():
    st.markdown("""
    <div class="app-header">
        <div>
            <h1 class="logo-text">omni<span>XM</span></h1>
            <p class="logo-subtitle">FINANCIAL INSIGHTS PLATFORM</p>
        </div>
        <div class="main-tagline">Every Financial Insight Matters</div>
    </div>
    """, unsafe_allow_html=True)

# --- Login Page ---
if not st.session_state.authenticated:
    # Create custom header for login page
    create_header()
    
    # Container for the full login layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:  # Center column for login card
        # Login error container
        login_error = st.empty()
        
        # Login card with proper styling
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Login header
        st.markdown("""
            <div class="login-header">
                <h1 class="login-title">Sign In</h1>
                <p class="login-subtitle">Access your financial insights dashboard</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Login form
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        remember_me = st.checkbox("Remember me for 30 days")
        
        # Login button
        login_pressed = st.button("Sign In", key="login_button")
        
        # Login footer
        st.markdown("""
            <div class="login-footer">
                © 2025 omniXM Financial Insights • All rights reserved
            </div>
        """, unsafe_allow_html=True)
        
        # Close the card
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Authentication check
    if login_pressed:
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.rerun()  # Rerun to show the main app
        else:
            # Display error message
            login_error.markdown("""
            <div class="error-message" style="max-width: 450px; width: 100%; margin: 0 auto 1rem auto;">
                Invalid username or password. Please try again.
            </div>
            """, unsafe_allow_html=True)

else:
    # --- Main Application ---
    # Display the header
    create_header()
    
    # --- Data Loading and Preparation Cache ---
    @st.cache_data
    def load_and_prepare_data():
        # Return cached data if already processed
        if 'pl_data' in st.session_state and st.session_state['pl_data'] is not None:
            return st.session_state['pl_data']
        
        pl_data = {}
        pos_orders_data_2025 = None
        pl_combined_data = None

        # Check if P&L data file has been uploaded
        if 'pl_data_file' not in st.session_state or st.session_state.pl_data_file is None:
            st.warning("🔍 Please upload the P&L data file (PL_Data(Jan2023-March2025).xlsx) in the sidebar.")
            return None

        # Load data from the uploaded file
        try:
            pl_data_file = st.session_state.pl_data_file
            excel_file = pd.ExcelFile(pl_data_file)
            sheet_names = excel_file.sheet_names
            for sheet in sheet_names:
                pl_data[sheet] = excel_file.parse(sheet)
            st.success(f"✅ Successfully read {len(sheet_names)} sheets from P&L data file.")
        except Exception as e:
            st.error(f"Error reading P&L data file: {e}")
            return None

        # Check if POS data is uploaded and available
        if 'pos_orders_data_2025' in st.session_state and st.session_state.pos_orders_data_2025 is not None:
            pos_orders_data_2025 = st.session_state.pos_orders_data_2025
            st.info("✓ Using uploaded POS Orders Data for enhanced analysis")

        # Data Preparation: Combine P&L Sheets
        try:
            if 'P&L_Details' in pl_data and 'P&L_Mapping' in pl_data and 'P&L_Units' in pl_data:
                df_details = pl_data['P&L_Details'].copy()
                df_mapping = pl_data['P&L_Mapping'].copy()
                df_units = pl_data['P&L_Units'].copy()

                df_details['Month'] = pd.to_datetime(df_details['Month'])
                if 'UnitID' in df_units.columns:
                     df_units = df_units.rename(columns={'UnitID': 'UnitId'})

                pl_combined = pd.merge(df_details, df_mapping, on='Level1', how='left')
                if 'UnitId' in pl_combined.columns and 'UnitId' in df_units.columns:
                    pl_combined_data = pd.merge(pl_combined, df_units[['UnitId', 'UnitName']], on='UnitId', how='left')
                    
                    # If POS data is available, add a flag to indicate it's available for analysis
                    if pos_orders_data_2025 is not None:
                        # Store POS data in session state for use in analysis
                        st.session_state['pos_orders_data_2025'] = pos_orders_data_2025
                        # Add a flag to the combined data indicating POS data is available
                        st.session_state['pos_data_available'] = True
                    
                    # Store in session state for future use
                    st.session_state['pl_data'] = pl_combined_data
                else:
                    st.error("Error merging P&L data: Unit ID mismatch.")
                    pl_combined_data = None
            else:
                st.error("Error: One or more required P&L sheets not found. Required sheets: P&L_Details, P&L_Mapping, P&L_Units")
                if sheet_names:
                    st.info(f"Available sheets in the uploaded file: {', '.join(sheet_names)}")
                pl_combined_data = None
        except Exception as e:
            st.error(f"An error occurred during data preparation: {e}")
            pl_combined_data = None

        return pl_combined_data

    # Load data using the cached function
    pl_combined_data = load_and_prepare_data()


    # --- display_thinking_process function ---
    def display_thinking_process(thinking_placeholder, thinking_steps):
        """Update the single progress card in-place with the latest thinking steps."""
        if thinking_placeholder is not None:
            html = "<div class='thinking-container'><h4>AI Analysis Process</h4>"
            for step_type, step_content in thinking_steps:
                html += f"<div class='thinking-step'><div class='thinking-title'>{step_type}</div>{step_content}</div>"
            html += "</div>"
            thinking_placeholder.markdown(html, unsafe_allow_html=True)

    # --- OpenAI Analysis Function ---
    def run_openai_analysis(df, prompt, api_key, model, show_thinking=True):
        if df is None:
            st.error("P&L data not loaded. Cannot run analysis.")
            if 'pl_data' in st.session_state:
                # Try to recover from session state if available
                df = st.session_state['pl_data']
                if df is not None:
                    st.info("Recovered data from previous session. Proceeding with analysis.")
                else:
                    return
            else:
                return
        
        if not api_key:
            st.error("OpenAI API Key not provided. Please enter it in the sidebar.")
            return

        try:
            client = OpenAI(api_key=api_key)
        except Exception as e:
            st.error(f"Failed to initialize OpenAI client: {e}")
            return

        # Clear any previous content in results area
        if st.session_state.results_area:
            st.session_state.results_area.empty()
        
        # Create a container for progress updates inside the results area
        progress_container = st.session_state.results_area
        
        # Create fixed placeholders for status and thinking process
        status_placeholder = progress_container.empty()
        thinking_placeholder = progress_container.empty() if show_thinking else None
        
        file_id = None
        pos_file_id = None  # For POS data if available
        assistant_id = None
        thread_id = None
        thinking_steps = []
        analysis_successful = False

        try:
            # Step 1: Upload Data
            status_placeholder.info("⏳ Preparing & Uploading Data...")
            if show_thinking:
                thinking_steps.append(("Data Preparation", "Converting P&L data to CSV format..."))
                display_thinking_process(thinking_placeholder, thinking_steps)
            
            # Prepare and upload P&L data
            csv_data = df.to_csv(index=False)
            file_bytes = io.BytesIO(csv_data.encode('utf-8'))
            if show_thinking:
                thinking_steps.append(("Data Upload", "Sending P&L data to OpenAI..."))
                display_thinking_process(thinking_placeholder, thinking_steps)
            file_response = client.files.create(file=file_bytes, purpose="assistants")
            file_id = file_response.id
            
            # Check if POS data is available and upload it as well
            pos_data_available = st.session_state.get('pos_data_available', False)
            if pos_data_available and 'pos_orders_data_2025' in st.session_state:
                if show_thinking:
                    thinking_steps.append(("Additional Data", "Preparing POS Orders data..."))
                    display_thinking_process(thinking_placeholder, thinking_steps)
                
                pos_data = st.session_state['pos_orders_data_2025']
                pos_csv_data = pos_data.to_csv(index=False)
                pos_file_bytes = io.BytesIO(pos_csv_data.encode('utf-8'))
                
                if show_thinking:
                    thinking_steps.append(("Data Upload", "Sending POS Orders data to OpenAI..."))
                    display_thinking_process(thinking_placeholder, thinking_steps)
                
                pos_file_response = client.files.create(file=pos_file_bytes, purpose="assistants")
                pos_file_id = pos_file_response.id
                status_placeholder.info("✅ P&L and POS Data Uploaded. Initializing Analyst...")
            else:
                status_placeholder.info("✅ P&L Data Uploaded. Initializing Analyst...")
            
            time.sleep(0.5)

            # Step 2: Create Assistant
            if show_thinking:
                thinking_steps.append(("Assistant Setup", f"Initializing AI Analyst ({model})..."))
                display_thinking_process(thinking_placeholder, thinking_steps)
            
            # Update instructions based on whether POS data is available
            instructions_base = """You are an expert financial analyst specializing in P&L statements. 
                Analyze the data thoroughly but provide concise, business-focused insights. 
                Use visualizations strategically to highlight key trends and patterns.
                Always highlight subsidy-related insights as they're of particular importance.
                Present your analysis in a structured format with clear section headers.
                Focus on actionable recommendations based on the data."""
            
            if pos_data_available:
                instructions = instructions_base + """
                Additionally, you have access to POS (Point of Sale) Orders data that you can use to enrich your analysis.
                This data can help correlate sales performance with P&L metrics to provide deeper insights.
                When applicable, integrate POS data into your analysis to identify relationships between ordering patterns and financial performance."""
            else:
                instructions = instructions_base
            
            assistant = client.beta.assistants.create(
                name="Financial Analysis Expert",
                instructions=instructions,
                model=model,
                tools=[{"type": "code_interpreter"}]
            )
            assistant_id = assistant.id
            status_placeholder.info("✅ AI Analyst Initialized. Creating thread...")
            time.sleep(0.5)

            # Step 3: Create Thread
            if show_thinking:
                thinking_steps.append(("Thread Creation", "Setting up analysis workflow..."))
                display_thinking_process(thinking_placeholder, thinking_steps)
            thread = client.beta.threads.create()
            thread_id = thread.id
            status_placeholder.info("✅ Thread Created. Sending request...")
            time.sleep(0.5)

            # Step 4: Add Message and Run
            if show_thinking:
                thinking_steps.append(("Query Processing", f"Sending analysis request: '{prompt[:100]}...'"))
                display_thinking_process(thinking_placeholder, thinking_steps)
            
            # Update prompt if POS data is available
            if pos_data_available:
                enhanced_prompt = f"{prompt}\n\nNote: POS (Point of Sale) Orders data is also available for this analysis. Please incorporate this data where relevant."
            else:
                enhanced_prompt = prompt
            
            # Create message with P&L data attachment
            message_attachments = [{"file_id": file_id, "tools": [{"type": "code_interpreter"}]}]
            
            # Add POS data attachment if available
            if pos_file_id is not None:
                message_attachments.append({"file_id": pos_file_id, "tools": [{"type": "code_interpreter"}]})
                if show_thinking:
                    thinking_steps.append(("Data Integration", "Including both P&L and POS data in analysis..."))
                    display_thinking_process(thinking_placeholder, thinking_steps)
            
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=[{"type": "text", "text": enhanced_prompt}],
                attachments=message_attachments
            )
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            status_placeholder.info(f"🚀 Analysis Running (Run ID: {run.id})... Please wait.")

            # Step 5: Poll for Results
            start_time = time.time()
            logged_steps = set()
            while run.status in ["queued", "in_progress", "requires_action"]:
                elapsed_time = int(time.time() - start_time)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                current_status = run.status
                status_placeholder.info(f"⏳ Analysis Status: {current_status} ({elapsed_time}s)")

                if show_thinking:
                    try:
                        run_steps = client.beta.threads.runs.steps.list(thread_id=thread.id, run_id=run.id, order="asc")
                        new_step_added = False
                        for step in run_steps.data:
                            step_id = step.id
                            if step_id not in logged_steps and step.status == "in_progress":
                                if step.type == "tool_calls":
                                    for tool_call in step.step_details.tool_calls:
                                        if tool_call.type == "code_interpreter":
                                            thinking_steps.append(("Code Execution", "Running Python code for analysis..."))
                                            logged_steps.add(step_id)
                                            new_step_added = True
                                            break
                                elif step.type == "message_creation":
                                    thinking_steps.append(("Message Creation", "Compiling analysis results..."))
                                    logged_steps.add(step_id)
                                    new_step_added = True
                                if new_step_added:
                                    break
                        if new_step_added:
                            display_thinking_process(thinking_placeholder, thinking_steps)
                    except Exception as step_err:
                        print(f"Warning: Could not retrieve run steps: {step_err}")

                if current_status == "completed":
                    status_placeholder.success(f"✅ Analysis Complete! ({elapsed_time}s)")
                    if show_thinking:
                        thinking_steps.append(("Completion", "Analysis finished successfully."))
                        display_thinking_process(thinking_placeholder, thinking_steps)
                    analysis_successful = True
                    time.sleep(1)
                    break
                elif current_status in ["failed", "cancelled", "expired"]:
                    error_message = run.last_error.message if run.last_error else f'Run {current_status}'
                    status_placeholder.error(f"❌ Analysis Failed: {error_message}")
                    if show_thinking:
                        thinking_steps.append(("Error", f"Analysis failed: {error_message}"))
                        display_thinking_process(thinking_placeholder, thinking_steps)
                    return
                elif current_status == "requires_action":
                    status_placeholder.info("⏳ Assistant requires action (submitting tool outputs)...")
                    try:
                        client.beta.threads.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=[])
                    except Exception as tool_err:
                        status_placeholder.error(f"❌ Error submitting tool outputs: {tool_err}")
                        return

                time.sleep(2)

            # When complete:
            if analysis_successful:
                # Clear the progress placeholders before displaying results
                status_placeholder.empty()
                if thinking_placeholder:
                    thinking_placeholder.empty()
                
                # Create new results directly in the results area
                st.session_state.results_area.markdown("<div class='results-card'>", unsafe_allow_html=True)
                st.session_state.results_area.markdown("<h3 style='color:#00a4bd;'>Financial Analysis Results</h3>", unsafe_allow_html=True)
                messages = client.beta.threads.messages.list(thread_id=thread.id, order='asc')
                assistant_responded = False
                for msg in messages.data:
                    if msg.role == "assistant":
                        assistant_responded = True
                        for content_part in msg.content:
                            if content_part.type == "text":
                                highlighted_text = highlight_subsidy(content_part.text.value)
                                st.session_state.results_area.markdown(highlighted_text, unsafe_allow_html=True)
                            elif content_part.type == "image_file":
                                try:
                                    image_file_id = content_part.image_file.file_id
                                    image_data = client.files.content(image_file_id)
                                    image_bytes = image_data.read()
                                    st.session_state.results_area.image(Image.open(io.BytesIO(image_bytes)), use_column_width=True, caption="Generated Visualization")
                                except Exception as img_err:
                                    st.session_state.results_area.warning(f"Unable to display image: {img_err}")
                        st.session_state.results_area.markdown("<hr>", unsafe_allow_html=True)
                if not assistant_responded:
                    st.session_state.results_area.warning("The assistant did not provide a response.")
                st.session_state.results_area.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            status_placeholder.error(f"An error occurred during analysis: {str(e)}")
            st.code(traceback.format_exc())
        finally:
            try:
                if assistant_id: client.beta.assistants.delete(assistant_id)
            except Exception as clean_e: print(f"Could not delete assistant: {clean_e}")
            try:
                if file_id: client.files.delete(file_id)
            except Exception as clean_e: print(f"Could not delete file: {clean_e}")
            try:
                if pos_file_id: client.files.delete(pos_file_id)
            except Exception as clean_e: print(f"Could not delete POS data file: {clean_e}")


    # --- Sidebar Settings ---
    with st.sidebar:
        st.markdown("<h2>Analysis Settings</h2>", unsafe_allow_html=True)

        # API Key input
        st.markdown("<h4>OpenAI API Key</h4>", unsafe_allow_html=True)
        api_key_input = st.text_input(
            "Enter your OpenAI API Key",
            type="password",
            value=st.session_state.openai_key,
            placeholder="sk-...",
            label_visibility="collapsed"
        )
        if api_key_input != st.session_state.openai_key:
            st.session_state.openai_key = api_key_input
        
        # Data File Upload Section
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4>Required Data Files</h4>", unsafe_allow_html=True)
        
        # P&L Data File Uploader
        st.markdown("<p style='font-size:0.9rem; color:#516f90;'><strong>1. P&L Data File</strong> (Required)</p>", unsafe_allow_html=True)
        pl_data_file = st.file_uploader(
            "Upload PL_Data(Jan2023-March2025).xlsx",
            type=["xlsx", "xls"],
            key="pl_data_uploader",
            help="This is the main P&L data file containing financial data needed for analysis"
        )
        
        if pl_data_file is not None:
            # Save the file to session state for use in analysis
            if 'pl_data_file' not in st.session_state or st.session_state.pl_data_file != pl_data_file:
                st.session_state.pl_data_file = pl_data_file
                # Read and store the data - will be processed in the load_and_prepare_data function
                st.success(f"✅ P&L data file uploaded: {pl_data_file.name}")
                # Reset cached data to ensure new file is processed
                if 'pl_data' in st.session_state:
                    del st.session_state['pl_data']
        
        # POS Data File Upload Section
        st.markdown("<p style='font-size:0.9rem; color:#516f90; margin-top:1rem;'><strong>2. POS Orders Data</strong> (Optional but recommended)</p>", unsafe_allow_html=True)
        pos_data_file = st.file_uploader(
            "Upload POS_Orders_Data_2025.xlsx",
            type=["xlsx", "xls"],
            key="pos_data_uploader",
            help="This file contains point-of-sale order data to enhance analysis with sales details"
        )
        
        if pos_data_file is not None:
            # Save the file to session state for use in analysis
            if 'pos_data_file' not in st.session_state or st.session_state.pos_data_file != pos_data_file:
                st.session_state.pos_data_file = pos_data_file
                # Read and store the data
                try:
                    pos_data = pd.read_excel(pos_data_file)
                    st.session_state.pos_orders_data_2025 = pos_data
                    st.success(f"✅ POS data loaded: {pos_data_file.name} ({pos_data.shape[0]} rows, {pos_data.shape[1]} columns)")
                except Exception as e:
                    st.error(f"Error reading POS data file: {e}")
        
        st.markdown("<hr>", unsafe_allow_html=True)

        # Model selection
        st.markdown("<h4>Model Selection</h4>", unsafe_allow_html=True)
        model_options = [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1",  
            "gpt-4.1-mini",
            #"o3-mini",
            #"gpt-o3"

            
        ]
        selected_model = st.selectbox(
            "Choose LLM Model",
            options=model_options,
            index=model_options.index(st.session_state.model_choice) if st.session_state.model_choice in model_options else 0,
            label_visibility="collapsed",
            help="Select the OpenAI model for analysis. More powerful models may provide better results but cost more."
        )
        if selected_model != st.session_state.model_choice:
            st.session_state.model_choice = selected_model

        # Show thinking process option
        show_thinking = st.checkbox("Show AI thinking process", value=True, 
                                  help="Display the AI's thought process during analysis")

        # Analysis Prompt Customization
        st.markdown("<h4>Base Analysis Instructions</h4>", unsafe_allow_html=True)
        custom_prompt = st.text_area(
            "Edit the baseline instructions for the AI:",
            value=st.session_state.analysis_prompt,
            height=200,
            label_visibility="collapsed",
            help="These are the base instructions for the AI analyst. They'll be combined with any specific question you ask."
        )
        if custom_prompt != st.session_state.analysis_prompt:
            st.session_state.analysis_prompt = custom_prompt

        if st.button("Reset to Default Instructions"):
            st.session_state.analysis_prompt = """You are a financial analyst expert in P&L statement analysis.

Analyze this dataset and provide concise, actionable insights focusing on:
- Key trends in profitability and revenue
- Notable changes in expenses (OPEX, labor costs, etc.)
- Highlight any subsidy impacts
- Create visualizations that best illustrate important patterns

Be direct and business-focused in your analysis. Clearly label insights and recommendations."""
            st.rerun()
            
        # Add logout button at the bottom
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

        # --- Display Data Structure Debug Info --- (Moved to bottom of sidebar)
        st.markdown("<hr>", unsafe_allow_html=True)
        with st.expander("🔍 P&L Data Structure (Debug)"):
            if pl_combined_data is not None:
                st.markdown("<div class='debug-section'>", unsafe_allow_html=True)
                st.write(f"Columns: {pl_combined_data.columns.tolist()}")
                st.write(f"Shape: {pl_combined_data.shape}")
                st.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)
                for level in ['Level1', 'Level2', 'Level3', 'Level4', 'Level5']:
                    if level in pl_combined_data.columns:
                        unique_vals = pl_combined_data[level].unique()
                        # Show limited sample if too many unique values
                        sample_vals = unique_vals[:15] if len(unique_vals) > 15 else unique_vals
                        st.write(f"**{level}** (Sample Values):")
                        st.write(list(sample_vals))
                        st.caption(f"Total unique in {level}: {len(unique_vals)}")
                        st.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.write("Data not loaded. Cannot display structure.")

    # === Main Application Interface ===
    # Wrap input section in a card, similar to code_interpreter_app
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # Check if P&L data file has been uploaded
    if 'pl_data_file' not in st.session_state or st.session_state.pl_data_file is None:
        st.markdown("<h2>Upload Required Data</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #5a6e84; line-height: 1.6;'>Please upload the <strong>P&L Data file</strong> in the sidebar to continue. The file is required to perform financial analysis.</p>", unsafe_allow_html=True)
        
        # Add helper information
        st.info("📄 The P&L Data file (PL_Data(Jan2023-March2025).xlsx) contains the financial data needed for analysis.")
        
        # Show a visual arrow/indicator pointing to the sidebar
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem;">
            <div style="font-size: 2rem; color: #ff7a59;">👈</div>
            <p style="color: #516f90;">Upload your data in the sidebar</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Show the normal interface when P&L data is available
        st.markdown("<h2>Ask a Specific Financial Question</h2>", unsafe_allow_html=True) 
        st.markdown("<p style='color: #5a6e84; line-height: 1.6;'>Enter a specific question about your P&L data, or leave blank to run the general analysis based on sidebar instructions.</p>", unsafe_allow_html=True)

        # Specific question input
        specific_question = st.text_area(
            "Your specific question:", 
            placeholder="E.g., 'Compare Q2 to Q1 sales and subsidy' or 'Highest labor costs month?'",
            value=st.session_state.specific_question,
            height=100,  # Set appropriate height for multiple lines
            key="specific_question_input"
        )

        # Save to session state when changed
        if specific_question != st.session_state.specific_question:
            st.session_state.specific_question = specific_question

        # Example questions
        st.markdown("<h5 style='font-size: 1rem; font-weight: 600; color: #516f90; margin-top: 1rem; margin-bottom: 0.5rem;'>Example Questions:</h5>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <ul style="font-size: 0.9rem; color: #5a6e84; padding-left: 1.2rem; margin-top: 0; margin-bottom: 1rem;">
                <li style="margin-bottom: 0.3rem;">Compare Q2 to Q1 for total sales and <span class='highlight-subsidy'>subsidy</span>.</li>
                <li style="margin-bottom: 0.3rem;">What were the top 3 OPEX categories last month?</li>
            </ul>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <ul style="font-size: 0.9rem; color: #5a6e84; padding-left: 1.2rem; margin-top: 0; margin-bottom: 1rem;">
                <li style="margin-bottom: 0.3rem;">Show food cost as % of sales over the last 12 months.</li>
                <li style="margin-bottom: 0.3rem;">Which month had the highest labor-to-sales ratio?</li>
            </ul>
            """, unsafe_allow_html=True)

        # Run analysis button
        st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
        analyze_button = st.button("🚀 Run Financial Analysis", use_container_width=True, key="run_analysis_button")
        st.markdown("</div>", unsafe_allow_html=True)

    # Close the input card
    st.markdown("</div>", unsafe_allow_html=True) 

    # --- Analysis Output Section ---
    # Create a header for the results section
    if 'pl_data_file' in st.session_state and st.session_state.pl_data_file is not None:
        st.markdown("<h2 class='results-header'>Analysis Output Section</h2>", unsafe_allow_html=True)

        # Create a designated results area (container instead of empty)
        # Reinitialize for each new session to avoid stale references
        st.session_state.results_area = st.container()

        # --- Button Click Logic ---
        if analyze_button:
            # Prepare the final prompt
            final_prompt = st.session_state.analysis_prompt
            if specific_question:
                final_prompt += f"\n\nSPECIFIC QUESTION TO FOCUS ON: {specific_question}"
            
            # Mark that initial display should be hidden
            st.session_state['initial_display'] = False
            
            # Store data in session state to ensure it persists between runs
            if 'pl_data' not in st.session_state:
                st.session_state['pl_data'] = pl_combined_data
            
            # Call the analysis function
            run_openai_analysis(
                df=pl_combined_data,
                prompt=final_prompt,
                api_key=st.session_state.openai_key,
                model=st.session_state.model_choice,
                show_thinking=show_thinking
            )

        # Display initial state (data overview or error) in the results_area
        elif pl_combined_data is not None and st.session_state.get('initial_display', True):
            # Display initial overview in the results area
            with st.session_state.results_area:
                # Wrap initial overview in a card
                st.markdown("<div class='results-card'>", unsafe_allow_html=True)
                st.markdown("<h3>P&L Data Overview</h3>", unsafe_allow_html=True)
                st.markdown("<p style='color: #5a6e84; line-height: 1.6;'>Data loaded successfully. Ask a specific question above or click 'Run Financial Analysis' to generate insights.</p>", unsafe_allow_html=True)
                st.dataframe(pl_combined_data.head(), use_container_width=True)

                # Show summary stats
                st.markdown("<h4 style='font-size: 1.1rem; font-weight: 600; color: #33475b; margin-top: 1.5rem; margin-bottom: 0.8rem;'>Data Summary</h4>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_units = pl_combined_data['UnitId'].nunique()
                    st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{total_units}</div><div class='kpi-label'>Total Units</div></div>", unsafe_allow_html=True)
                with col2:
                    min_date = pl_combined_data['Month'].min().strftime('%b %Y')
                    max_date = pl_combined_data['Month'].max().strftime('%b %Y')
                    date_range = f"{min_date} - {max_date}"
                    st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{date_range}</div><div class='kpi-label'>Date Range</div></div>", unsafe_allow_html=True)
                with col3:
                    total_rows = len(pl_combined_data)
                    st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{total_rows:,}</div><div class='kpi-label'>Total Records</div></div>", unsafe_allow_html=True)
                # Close the initial overview card
                st.markdown("</div>", unsafe_allow_html=True)

        # Handle data loading failure state
        elif pl_combined_data is None:
            with st.session_state.results_area:
                st.error("Data could not be loaded or prepared. Please check the P&L file format and ensure it contains the required sheets: P&L_Details, P&L_Mapping, and P&L_Units.")
                # Add a tip about expected file format
                st.info("The P&L data file should be an Excel file with multiple sheets including P&L_Details, P&L_Mapping, and P&L_Units. Please ensure your file matches this structure.")

    # --- Footer ---
    st.markdown("<div class='footer'>© 2025 omniXM Financial Insights | <span style='color:#ff7a59; font-weight:500;'>Measure</span> & <span style='font-weight:500;'>Manage</span> Every Financial Experience</div>", unsafe_allow_html=True)






