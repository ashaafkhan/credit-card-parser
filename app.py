import streamlit as st
import os
# MODIFICATION: Import the BANK_PATTERNS dictionary as well
from PdfParser import parse_credit_card_statement, configure_tesseract_cmd, BANK_PATTERNS

# --- PAGE CONFIG ---
st.set_page_config(
    layout="centered",
    page_title="Credit Card Statement Parser",
    page_icon="💳"
)

# --- TESSERACT CONFIG ---
try:
    configure_tesseract_cmd()
except Exception:
    pass # Will be handled gracefully if OCR is needed

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/344/344441.png", width=100)
    st.header("About This App")
    st.info(
        "This tool is designed to parse PDF credit card statements. "
        "It uses a combination of text extraction and regular expressions to find key data points. "
        "The project supports statements from several major Indian banks."
    )
    st.caption("Disclaimer: This is a demonstration project. Do not upload sensitive personal documents.")

# --- MAIN PAGE ---
st.title("Credit Card Statement Parser 📄")
st.info(
    "**For a reliable demo, please use the sample statements from the project's [GitHub repository](https://github.com/ashaafkhan/credit-card-parser/tree/main/samples).**",
    icon="💡"
)

# Display the initial view before a file is processed
if 'extracted_data' not in st.session_state:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Key Features:")
        st.markdown("""
        - **Automatic Bank Detection**
        - **Extracts 5 Key Data Points**
        - **Supports Image-based PDFs (via OCR)**
        - **Clean & Simple Interface**
        """)
        
        # --- NEW: Display supported banks ---
        st.subheader("Supported Banks:")
        # Dynamically create a markdown list from the keys of the BANK_PATTERNS dict
        bank_list_markdown = ""
        for bank in BANK_PATTERNS.keys():
            bank_list_markdown += f"- {bank}\n"
        st.markdown(bank_list_markdown)
        # --- END NEW SECTION ---

    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/1041/1041875.png", use_container_width=True)


uploaded_file = st.file_uploader(
    "Upload your PDF statement here", 
    type="pdf", 
    label_visibility="visible"
)

if uploaded_file is not None:
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("✨ Extract Information", use_container_width=True, type="primary"):
        with st.spinner("Analyzing statement... This might take a moment."):
            try:
                st.session_state.extracted_data = parse_credit_card_statement(temp_file_path)
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.extracted_data = None
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

# This block will only run if data has been extracted
if 'extracted_data' in st.session_state and st.session_state.extracted_data is not None:
    data = st.session_state.extracted_data
    
    st.subheader("✅ Extraction Complete!")

    if not data.get("issuer"):
        st.warning("Could not identify the bank/issuer. Results may be incomplete.")
    else:
        st.success(f"Detected Issuer: **{data.get('issuer')}**")

    tab1, tab2 = st.tabs(["📊 Summary", "📄 Raw Data"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="💳 Card (Last 4 Digits)", value=data.get("last_4_digits", "N/A"))
            st.metric(label="🗓️ Payment Due Date", value=data.get("payment_due_date", "N/A"))
        with col2:
            st.metric(label="📅 Billing Cycle Start", value=data.get('billing_cycle_start', 'N/A'))
            st.metric(label="📅 Billing Cycle End", value=data.get('billing_cycle_end', 'N/A'))
        
        balance = data.get("total_outstanding_balance", "0.00")
        st.error(f"**Total Amount Due:  ₹ {balance}**")

    with tab2:
        st.json(data)