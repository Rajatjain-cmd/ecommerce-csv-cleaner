import streamlit as st
import pandas as pd
from io import BytesIO

# ----------------------------------------------------
# 1. INITIAL SYSTEM SETUP & STYLING
# ----------------------------------------------------
st.set_page_config(
    page_title="E-Com Validation Suite", 
    page_icon="🛍️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛍️ Smart E-Commerce Data Validator & Cleaner")
st.subheader("🚀 Free Public Beta Edition")
st.markdown("""
Easily repair messy **Etsy** and **Shopify** spreadsheet exports. 
Upload your files to run a free structural diagnostic audit and download your polished documents instantly.
""")

# ----------------------------------------------------
# 2. CORE UTILITY DATA PIPELINES
# ----------------------------------------------------
def validate_and_clean(df, platform_type):
    """
    Scans the spreadsheet for structural errors, logs diagnostics, 
    and returns a pristine, corrected dataframe.
    """
    cleaned_df = df.copy()
    errors_found = []
    
    zip_col = 'Shipping Zip' if platform_type == "Shopify" else 'Ship Zipcode'
    id_col = 'Name' if platform_type == "Shopify" else 'Order ID'
    
    # Check 1: Duplicate Row Purging
    duplicate_count = cleaned_df.duplicated().sum()
    if duplicate_count > 0:
        errors_found.append({
            "Issue Category": "Duplicate Records", 
            "Details": f"Detected {duplicate_count} identical duplicate rows. These have been purged automatically."
        })
        cleaned_df = cleaned_df.drop_duplicates()

    # Check 2: Core Identifier Validation
    if id_col in cleaned_df.columns:
        missing_ids = cleaned_df[id_col].isna().sum()
        if missing_ids > 0:
            errors_found.append({
                "Issue Category": "Missing Transaction IDs", 
                "Details": f"Found {missing_ids} rows missing order names/identifiers. These invalid records have been dropped."
            })
            cleaned_df = cleaned_df.dropna(subset=[id_col])

    # Check 3: Zip Code Truncation Fix (Restoring dropped leading zeros)
    if zip_col in cleaned_df.columns:
        corrupted_zips = 0
        fixed_zips = []
        for val in cleaned_df[zip_col]:
            if pd.isna(val):
                fixed_zips.append(val)
                continue
            # Handle float conversions (e.g., '90210.0' -> '90210')
            val_str = str(val).strip().split('.')[0]
            if val_str.isdigit() and 0 < len(val_str) < 5:
                corrupted_zips += 1
                fixed_zips.append(val_str.zfill(5))
            else:
                fixed_zips.append(val_str)
        cleaned_df[zip_col] = fixed_zips
        if corrupted_zips > 0:
            errors_found.append({
                "Issue Category": "Corrupted Zip Codes", 
                "Details": f"Restored dropped leading zeros for {corrupted_zips} postal codes to safeguard shipping routing."
            })

    # Check 4: Invisible Whitespace Trimming
    str_cols = cleaned_df.select_dtypes(include=['object']).columns
    space_errors = 0
    for col in str_cols:
        has_spaces = cleaned_df[col].astype(str) != cleaned_df[col].astype(str).str.strip()
        space_errors += has_spaces.sum()
        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
    if space_errors > 0:
        errors_found.append({
            "Issue Category": "Hidden Whitespace Errors", 
            "Details": f"Trimmed hidden leading/trailing whitespace errors in {space_errors} fields across the dataset."
        })

    errors_df = pd.DataFrame(errors_found) if errors_found else pd.DataFrame(columns=["Issue Category", "Details"])
    return cleaned_df, errors_df

def convert_df_to_excel(df):
    """Compiles the dataframe into an in-memory downloadable Excel stream."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Cleaned Output')
    return output.getvalue()

# ----------------------------------------------------
# 3. INTERACTIVE SIDEBAR CONTROL PANEL
# ----------------------------------------------------
st.sidebar.header("🕹️ App Control Panel")
platform = st.sidebar.selectbox("Source Platform Template", ["Shopify", "Etsy"])
uploaded_file = st.sidebar.file_uploader(f"Upload raw {platform} export", type=["csv", "xlsx"])

# Feedback and status display for Beta Users
st.sidebar.markdown("---")
st.sidebar.info("""
👋 **Beta Feedback Option:**
This tool is 100% free while we test features. If it saves you time, please help us improve!
""")

# ----------------------------------------------------
# 4. MAIN USER DASHBOARD RUNTIME
# ----------------------------------------------------
if uploaded_file is not None:
    try:
        # Load file structures
        if uploaded_file.name.endswith('.csv'):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
            
        with st.spinner("Analyzing spreadsheet composition..."):
            cleaned_data, audit_log = validate_and_clean(raw_df, platform)
            
        st.success("✨ Processing Complete!")
        tab1, tab2 = st.tabs(["📋 Diagnostic Audit Log", "💾 Download Repaired File"])
        
        with tab1:
            st.subheader("Spreadsheet Audit Summary")
            if not audit_log.empty:
                st.warning("⚠️ Formatting discrepancies discovered and isolated below:")
                st.dataframe(audit_log, use_container_width=True, hide_index=True)
                st.info("💡 Review the errors above, then jump to the 'Download Repaired File' tab to grab your document.")
            else:
                st.success("🎉 Outstanding Structure! No critical formatting discrepancies detected.")
                st.dataframe(raw_df.head(5), use_container_width=True)

        with tab2:
            st.subheader("🛠️ Cleaned Dataset Preview (Top 10 Records)")
            st.dataframe(cleaned_data.head(10), use_container_width=True)
            
            # Instantly generate downloading bytes stream without paywall boundaries
            excel_bytes = convert_df_to_excel(cleaned_data)
            st.download_button(
                label="💾 Download Fully Repaired Excel Sheet",
                data=excel_bytes,
                file_name=f"REPAIRED_{platform}_{uploaded_file.name.split('.')[0]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
                    
    except Exception as e:
        st.error(f"Failed to cleanly process file structure: {e}. Check if you selected the right platform toggle.")
else:
    st.info("💡 Welcome! Please upload an e-commerce data spreadsheet in the sidebar to activate the validation engine.")
