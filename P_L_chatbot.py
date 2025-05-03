import pandas as pd
import streamlit as st
import base64
from openai import OpenAI
import io
import time
import traceback
from PIL import Image
import re  # Added for regex processing
import json
import datetime  # Added for datetime handling

# --- Page Configuration ---
st.set_page_config(
    page_title="omniINSIGHTS",
    initial_sidebar_state="expanded",
    layout="wide"
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
# Initialize file-related session state variables
if 'pl_data_file' not in st.session_state:
    st.session_state['pl_data_file'] = None
if 'pos_data_file' not in st.session_state:
    st.session_state['pos_data_file'] = None
if 'file_upload_processed' not in st.session_state:
    st.session_state['file_upload_processed'] = False
# Add chatbot mode selection
if 'chatbot_mode' not in st.session_state:
    st.session_state['chatbot_mode'] = "Chatbot Analysis"

# --- Login Credentials ---
CORRECT_USERNAME = "omnixm123"
CORRECT_PASSWORD = "1234567"

# --- Authentication function ---
def authenticate(username, password):
    return username == CORRECT_USERNAME and password == CORRECT_PASSWORD

# --- Custom CSS Styling including Login styles ---
def local_css():
    # Updated CSS to match the image
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
        color: #33475b;
    }
    
    /* App Background and Layout */
    .stApp {
        background: white;
    }
    
    /* Main Content Container */
    .main .block-container {
        padding: 0 !important;
        max-width: 100%;
        margin: 0;
    }
    
    /* Header */
    .header {
        background-color: #0057B8;
        color: white;
        padding: 30px;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* Upload Section */
    .upload-section {
        padding: 20px;
        background-color: #f9f9f9;
        border-bottom: 1px solid #eaeaea;
        text-align: center;
    }
    
    /* Chat Interface */
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    
    .chat-input {
        border: 1px solid #ddd;
        border-radius: 30px;
        padding: 15px 20px;
        margin-top: 20px;
        display: flex;
        align-items: center;
        background-color: #f9f9f9;
    }
    
    .mic-button {
        background-color: #0057B8;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        margin-left: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Prebuilt Questions */
    .prebuilt-questions {
        max-width: 900px;
        margin: 20px auto;
        margin-bottom: 30px;
    }
    
    .question-button {
        background-color: #f0f0f0;
        border: none;
        border-radius: 8px;
        padding: 12px 20px;
        margin: 8px;
        text-align: left;
        cursor: pointer;
    }
    
    .question-button:hover {
        background-color: #e0e0e0;
    }
    
    /* Category Buttons */
    .category-button {
        background-color: #e0e0e0;
        border: none;
        border-radius: 20px;
        padding: 8px 16px;
        margin: 4px;
        cursor: pointer;
    }
    
    .category-button:hover {
        background-color: #d0d0d0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f9f9f9;
        border-right: 1px solid #eaeaea;
    }
    
    /* Logo */
    .logo {
        color: white;
        font-weight: bold;
        font-size: 24px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        font-size: 12px;
        color: #999;
        margin-top: 40px;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* Additional styles to match the image */
    .insights-logo {
        color: white;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .insights-logo span {
        color: white;
    }
    
    .upload-text {
        font-size: 1.2rem;
        font-weight: normal;
        margin: 10px 0;
    }
    
    .ask-container {
        border: 2px solid #0057B8;
        border-radius: 15px;
        padding: 20px;
        margin: 20px auto;
        max-width: 900px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Styling for the query input box */
    .query-input {
        border-radius: 30px;
        border: 1px solid #ddd;
        padding: 15px 20px;
        width: 100%;
        font-size: 1rem;
        background-color: #f5f5f5;
    }
    
    /* Smart question buttons */
    .smart-question {
        background-color: #f5f5f5;
        border: none;
        border-radius: 8px;
        padding: 15px;
        margin: 5px;
        text-align: left;
        cursor: pointer;
        display: block;
        width: 100%;
        font-size: 0.9rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .smart-question:hover {
        background-color: #e0e0e0;
    }
    
    .powered-by {
        text-align: right;
        font-size: 0.8rem;
        color: #666;
        margin-top: 20px;
        padding-right: 50px;
        margin-bottom: 30px;
    }

    /* Button styles */
    .profit-loss-button {
        background-color: transparent;
        border: 1px solid #0057B8;
        color: #0057B8;
        border-radius: 20px;
        padding: 8px 20px;
        margin-right: 10px;
        font-size: 0.9rem;
    }
    
    .point-of-sale-button {
        background-color: transparent;
        border: 1px solid #0057B8;
        color: #0057B8;
        border-radius: 20px;
        padding: 8px 20px;
        font-size: 0.9rem;
    }
    
    /* Thinking Process Styles */
    .thinking-container {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #0057B8;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .thinking-container h4 {
        font-size: 1.2rem;
        font-weight: 600;
        color: #33475b;
        margin-bottom: 1rem;
        margin-top: 0;
    }
    
    .thinking-step {
        padding: 0.5rem 0;
        border-bottom: 1px dashed #eaeef2;
        font-size: 0.9rem;
    }
    
    .thinking-step:last-child {
        border-bottom: none;
    }
    
    .thinking-title {
        font-weight: 600;
        color: #0057B8;
        margin-bottom: 0.3rem;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# Apply the CSS
local_css()

# --- Helper Functions ---
# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, pd.Timestamp)):
            return obj.isoformat()
        return super().default(obj)

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

# New helper function to verify Excel files
def verify_excel_file(uploaded_file):
    """
    Verifies if the uploaded file is a valid Excel file and returns information about it.
    Returns a tuple of (is_valid, message, file_data)
    """
    if uploaded_file is None:
        return False, "No file uploaded", None
    
    try:
        # Try to read the file content
        file_data = uploaded_file.getvalue()
        if len(file_data) == 0:
            return False, "File is empty", None
        
        # Check file signature for Excel files
        if not (file_data.startswith(b"PK") or  # XLSX signature
                file_data.startswith(b"\xd0\xcf\x11\xe0")):  # XLS signature
            return False, "File does not appear to be a valid Excel file", None
        
        # Try to open as Excel
        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_data))
            sheet_names = excel_file.sheet_names
            return True, f"Valid Excel file with sheets: {', '.join(sheet_names)}", file_data
        except Exception as e:
            return False, f"File appears to be Excel but cannot be parsed: {str(e)}", None
            
    except Exception as e:
        return False, f"Error reading file: {str(e)}", None

# Helper function to load POS data with caching
@st.cache_data(ttl=3600)
def load_pos_data():
    """Load POS data with caching for improved performance"""
    try:
        # Prefer CSV format as it's usually faster to load
        pos_file_path = "POS_Orders_Data_2025.csv"
        return pd.read_csv(pos_file_path)
    except Exception:
        try:
            # Fall back to Excel if CSV not available
            pos_file_path = "POS_Orders_Data_2025.xlsx"
            return pd.read_excel(pos_file_path)
        except Exception as e:
            # Silently log error instead of displaying warning
            print(f"Could not load POS data: {e}")
            return None

# --- Data Loading and Preparation Cache ---
@st.cache_data(ttl=3600)  # Cache data for 1 hour to improve performance
def load_and_prepare_data():
    # Return cached data if already processed
    if 'pl_data' in st.session_state and st.session_state['pl_data'] is not None:
        return st.session_state['pl_data']
    
    pl_data = {}
    pos_orders_data_2025 = None
    pl_combined_data = None

    # First try to read the file directly from filesystem
    try:
        excel_file_path = "PL_Data(Jan2023-March2025).xlsx"
        # Silently load data without displaying info messages
        excel_file = pd.ExcelFile(excel_file_path)
        sheet_names = excel_file.sheet_names
        
        # Process sheets silently
        for sheet in sheet_names:
            pl_data[sheet] = excel_file.parse(sheet)
    except FileNotFoundError:
        # Silent handling of file not found
        # Fall back to using uploaded file if available
        if 'pl_data_file' in st.session_state and st.session_state.pl_data_file is not None:
            try:
                pl_data_file = st.session_state.pl_data_file
                # Silently process uploaded file
                file_data = pl_data_file.getvalue()
                excel_file = pd.ExcelFile(io.BytesIO(file_data))
                sheet_names = excel_file.sheet_names
                
                for sheet in sheet_names:
                    pl_data[sheet] = excel_file.parse(sheet)
            except Exception as e:
                # Log error to console instead of showing in UI
                print(f"Error reading uploaded P&L data file: {e}")
                return None
        else:
            # Log error to console instead of showing in UI
            print("P&L data file not found in directory and no file was uploaded.")
            return None
    except Exception as e:
        # Log error to console instead of showing in UI
        print(f"Error reading P&L data file: {e}")
        return None

    # --- Old POS data check (remove) ---
    # Check if POS data is uploaded and available
    if 'pos_orders_data_2025' in st.session_state and st.session_state.pos_orders_data_2025 is not None:
        pos_orders_data_2025 = st.session_state.pos_orders_data_2025
    # --- End old POS data check ---

    # Load POS data using the cached function
    pos_orders_data_2025 = load_pos_data()
    if pos_orders_data_2025 is not None:
        # Set flag indicating POS data is available
        st.session_state['pos_orders_data_2025'] = pos_orders_data_2025
        st.session_state['pos_data_available'] = True
    else:
        # Silently set flag without warning
        st.session_state['pos_data_available'] = False

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
                # Log error to console instead of showing in UI
                print("Error merging P&L data: Unit ID mismatch.")
                pl_combined_data = None
        else:
            available_sheets = ", ".join(list(pl_data.keys()))
            # Log error to console instead of showing in UI
            print(f"Error: One or more required P&L sheets not found. Required sheets: P&L_Details, P&L_Mapping, P&L_Units. Available sheets: {available_sheets}")
            pl_combined_data = None
    except Exception as e:
        # Log error to console instead of showing in UI
        print(f"An error occurred during data preparation: {e}")
        pl_combined_data = None

    return pl_combined_data

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
            thinking_steps.append(("Data Upload", "Sending P&L data to the LLM..."))
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
                thinking_steps.append(("Data Upload", "Sending POS Orders data to the LLM..."))
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
            st.session_state.results_area.markdown("<h3 style='color:#0057B8;'>Financial Analysis Results</h3>", unsafe_allow_html=True)
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

# --- New function for Chatbot Asker mode ---
def run_chatbot_asker(df, prompt, api_key, model):
    """
    Run a direct chat completion on the P&L data without using the code interpreter.
    This function converts the data to JSON format and feeds it to the prompt.
    """
    if df is None:
        st.error("P&L data not loaded. Cannot run analysis.")
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
    status_placeholder = progress_container.empty()
    status_placeholder.info("⏳ Preparing data for analysis...")
    
    try:
        # Convert data to JSON format
        # Limit the data size to avoid token limits
        # If POS data is available, include a sample of it too
        
        # For P&L data - take a sample of the most recent months
        recent_months = 6  # Adjust based on your needs
        
        # Sort by month and get the most recent months
        if 'Month' in df.columns:
            df_sample = df.sort_values('Month', ascending=False).head(recent_months * 50)  # Estimate 50 rows per month
        else:
            df_sample = df.head(300)  # Just take the top 300 rows if no month column
        
        # Convert to JSON - handling datetime serialization
        df_json = df_sample.to_dict(orient='records')
        
        # Add POS data sample if available
        pos_data_json = None
        if 'pos_data_available' in st.session_state and st.session_state.get('pos_data_available', False):
            if 'pos_orders_data_2025' in st.session_state:
                pos_data = st.session_state['pos_orders_data_2025']
                pos_data_sample = pos_data.head(200)  # Just take first 200 rows as a sample
                pos_data_json = pos_data_sample.to_dict(orient='records')
        
        # Prepare the combined system message
        system_message = f"""You are a financial analyst expert specializing in P&L statements.
As a financial data assistant, your role is to directly answer questions about the financial data provided.
Focus on providing specific answers from the data rather than general advice.

The P&L data is provided as a JSON array. The data includes:
- Monthly financial metrics
- Revenue and expense categories
- Unit-level information

When answering:
- Be concise and direct
- Cite specific numbers from the data
- Clearly identify any subsidy-related insights
- If uncertain about something in the data, be transparent about it
- Do not create visualizations since you don't have that capability in this mode
"""

        if pos_data_json:
            system_message += "\nPOS (Point of Sale) data is also provided as a separate JSON array. Use this to enrich your analysis where relevant."
        
        # Prepare the data message
        data_message = "Here is the P&L data sample:\n"
        data_message += json.dumps(df_json, cls=DateTimeEncoder)  # Use custom encoder for datetime objects
        
        if pos_data_json:
            data_message += "\n\nHere is the POS data sample:\n"
            data_message += json.dumps(pos_data_json, cls=DateTimeEncoder)  # Use custom encoder
        
        # Prepare the user question
        user_question = f"Based on the financial data provided, please answer the following: {prompt}"
        
        status_placeholder.info("⏳ Sending request to the LLM...")
        
        # Make the ChatCompletion API call
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": data_message},
            {"role": "user", "content": user_question}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.,
            max_tokens=1500
        )
        
        # Process and display response
        status_placeholder.empty()
        
        if response and response.choices:
            answer = response.choices[0].message.content
            # Apply subsidy highlighting
            highlighted_answer = highlight_subsidy(answer)
            
            # Display results in a card
            st.session_state.results_area.markdown("<div class='results-card'>", unsafe_allow_html=True)
            st.session_state.results_area.markdown("<h3 style='color:#0057B8;'>Financial Analysis Results</h3>", unsafe_allow_html=True)
            st.session_state.results_area.markdown(highlighted_answer, unsafe_allow_html=True)
            st.session_state.results_area.markdown("</div>", unsafe_allow_html=True)
        else:
            st.session_state.results_area.error("No response was generated. Please try again.")
            
    except Exception as e:
        status_placeholder.error(f"An error occurred during analysis: {str(e)}")
        st.code(traceback.format_exc())

# --- Login Page ---
if not st.session_state.authenticated:
    # Custom header for login page
    st.markdown('<div class="header"><span class="insights-logo">omni<span>INSIGHTS</span></span></div>', unsafe_allow_html=True)
    
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
    # Display the header that matches the image
    st.markdown('<div class="header"><span class="insights-logo">omni<span>INSIGHTS</span></span></div>', unsafe_allow_html=True)
    
    # Upload section
    st.markdown("""
    <div class="upload-section">
        <p class="upload-text">Upload your <strong>monthly P&L statements</strong> and <strong>POS exports</strong> (CSV, Excel, or image-to-table conversion)<br>
        Bot automatically parses, standardizes, and stores structured data.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
        
        # Chatbot Mode selection
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4>Chatbot Mode</h4>", unsafe_allow_html=True)
        chatbot_mode = st.radio(
            "Select chatbot mode",
            options=["Chatbot Analysis", "Chatbot Asker"],
            index=0 if st.session_state.chatbot_mode == "Chatbot Analysis" else 1,
            help="Choose between advanced analysis with visualizations (Analysis) or direct Q&A about the data (Asker)",
            label_visibility="collapsed"
        )
        
        if chatbot_mode != st.session_state.chatbot_mode:
            st.session_state.chatbot_mode = chatbot_mode
            st.rerun()  # Refresh the interface when changing modes
            
        # Data Files Info
        st.markdown("<hr>", unsafe_allow_html=True)
        st.info("P&L and POS data are loaded automatically from files in the application directory.")
        
        st.markdown("<hr>", unsafe_allow_html=True)

        # Model selection
        st.markdown("<h4>Model Selection</h4>", unsafe_allow_html=True)
        model_options = [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1",  
            "gpt-4.1-mini",
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

        # Add logout button at the bottom
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # --- Main Chat Interface ---
    # "What's on your mind today?" section using Streamlit widgets
    st.markdown("""
    <div class="chat-container">
        <h2>What's on your mind today?</h2>
    """, unsafe_allow_html=True)

    # Example questions - moved up to be right after "What's on your mind today?"
    st.markdown("""
        <h3>Ask Anything. Literally.</h3>
        <p>Natural language queries supported:</p>
        <ul>
            <li>"What was our labor cost as a % of sales last month?"</li>
            <li>"Compare March and February subsidy."</li>
            <li>"Which Food Hall has the highest product cost?"</li>
            <li>"Show trends in transaction count by daypart."</li>
            <li>"Forecast April sales based on Q1 trends."</li>
        </ul>
    """, unsafe_allow_html=True)

    with st.container(): # Use a container to help with layout
        st.markdown("<div class='ask-container'>", unsafe_allow_html=True)
        
        # Use full width for the text input
        specific_question = st.text_area(
            "Ask Anything", 
            placeholder="Ask Anything", 
            key="specific_question_main_input",
            label_visibility="collapsed",
            height=68, # Minimum height allowed by Streamlit
            help="Type your financial question here and click 'Run Financial Analysis'"
        )
        # Update session state if the input changes
        if specific_question != st.session_state.specific_question:
             st.session_state.specific_question = specific_question
             
        st.markdown("</div>", unsafe_allow_html=True) # Close ask-container

    st.markdown("</div>", unsafe_allow_html=True) # Close chat-container
    
    # Prebuilt Smart Questions section
    st.markdown("""
    <div class="prebuilt-questions">
        <h3>Prebuilt Smart Questions</h3>
        <p>Quick tap-to-ask prompts:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Define a function to set question and trigger analysis
    def set_smart_question(question):
        # Set the question and immediately trigger analysis
        st.session_state.specific_question = question
        st.session_state.run_analysis = True  # Add a flag to trigger analysis
    
    # Create two columns for the smart questions
    col_q1, col_q2 = st.columns(2)
    
    with col_q1:
        if st.button("Show quarter over quarter sales trend", key="q1_button", use_container_width=True):
            set_smart_question("Show quarter over quarter sales trend")
            st.rerun()  # Force a rerun to trigger analysis
            
        if st.button("Predict subsidy impact next month", key="q3_button", use_container_width=True):
            set_smart_question("Predict subsidy impact next month")
            st.rerun()  # Force a rerun to trigger analysis
            
    with col_q2:
        if st.button("Average product cost as a percentage of sales by month", key="q2_button", use_container_width=True):
            set_smart_question("Average product cost as a percentage of sales by month")
            st.rerun()  # Force a rerun to trigger analysis
            
        if st.button("Which month has the highest labor cost as a percentage of sales", key="q4_button", use_container_width=True):
            set_smart_question("Which month has the highest labor cost as a percentage of sales")
            st.rerun()  # Force a rerun to trigger analysis
    
    # Add Run Analysis button after smart questions
    st.markdown("<div style='margin-top: 15px; text-align: center;'>", unsafe_allow_html=True)
    analyze_button = st.button("🚀 Run", use_container_width=True, key="run_analysis_button_main")
    st.markdown("</div>", unsafe_allow_html=True)

    # Footer with powered by
    st.markdown("""
    <div class="powered-by">
        Powered by <img src="https://omnixm.com/wp-content/uploads/2023/07/OmniXM_Logo_Color_RGB.png" height="30px" style="vertical-align: middle;">
    </div>
    """, unsafe_allow_html=True)

    # Example of where analyze_button definition should be (adjust placement as needed for UI)
    st.markdown("<!-- Placeholder for UI elements like text input -->", unsafe_allow_html=True)

    # Load data only after authentication
    pl_combined_data = None
    with st.container(): # Use a container to manage data loading visibility if needed
        pl_combined_data = load_and_prepare_data()

    # --- Analysis Output Section ---
    st.markdown("<h2 class='results-header'>Analysis Output Section</h2>", unsafe_allow_html=True)
    st.session_state.results_area = st.container()

    # --- Button Click Logic --- (Correctly placed after button definition and function definitions)
    # Check if either the main button was clicked OR a smart question triggered the analysis
    run_analysis_triggered = analyze_button or st.session_state.get('run_analysis', False)
    
    if run_analysis_triggered:
        # Reset the smart question trigger flag if it was set
        if st.session_state.get('run_analysis', False):
            st.session_state['run_analysis'] = False
            
        # Prepare the final prompt
        final_prompt = st.session_state.analysis_prompt
        # Access specific_question from session state
        specific_question = st.session_state.specific_question
        if specific_question:
            final_prompt += f"\n\nSPECIFIC QUESTION TO FOCUS ON: {specific_question}"
        
        # Mark that initial display should be hidden
        st.session_state['initial_display'] = False
        
        # Store data in session state to ensure it persists between runs
        if 'pl_data' not in st.session_state:
            st.session_state['pl_data'] = pl_combined_data
        
        # Call the appropriate analysis function based on the selected mode
        if st.session_state.chatbot_mode == "Chatbot Analysis":
            # Safely get show_thinking, default to True if not set
            show_thinking = True  # Default value
            # Use code interpreter analysis
            run_openai_analysis(
                df=pl_combined_data,
                prompt=final_prompt,
                api_key=st.session_state.openai_key,
                model=st.session_state.model_choice,
                show_thinking=show_thinking
            )
        else:
            # Use direct chat completion analysis
            run_chatbot_asker(
                df=pl_combined_data,
                prompt=final_prompt if specific_question else "Provide a general overview of the financial data.",
                api_key=st.session_state.openai_key,
                model=st.session_state.model_choice
            )

    # Display initial state (data overview or error) in the results_area
    elif pl_combined_data is not None and st.session_state.get('initial_display', True):
        # Leave the results area empty until user runs an analysis
        pass
        
    # Handle data loading failure state
    elif pl_combined_data is None:
        with st.session_state.results_area:
            st.error("Data could not be loaded or prepared. Please check the P&L file format and ensure it contains the required sheets: P&L_Details, P&L_Mapping, and P&L_Units.")






