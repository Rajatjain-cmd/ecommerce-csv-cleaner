import streamlit as st
import pandas as pd
from io import BytesIO

# ----------------------------------------------------
# 1. INITIAL SYSTEM SETUP & STYLING
# ----------------------------------------------------
st.set_page_config(
    page_title="E-Com Validation Engine", 
    page_icon="🛍️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize persistent session states
if 'premium_unlocked' not in st.session_state:
    st.session_state.premium_unlocked = False

st.title("🛍️ Smart E-Commerce Data Validator & Cleaner")
st.markdown("""
Easily repair messy **Etsy** and **Shopify** spreadsheet exports. 
Upload files for a free diagnostics audit, and upgrade to premium to download your polished documents.
""")

# ----------------------------------------------------
# 2. CORE ENGINES: VALIDATOR & FILE CONVERTER
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
    
    # Check 1: Duplicate Row Purge
    duplicate_count = cleaned_df.duplicated().sum()
    if duplicate_count > 0:
        errors_found.append({
            "Issue Category": "Duplicate Records",
            "Details": f"Detected {duplicate_count} identical duplicate rows. These will be automatically purged."
        })
        cleaned_df = cleaned_df.drop_duplicates()

    # Check 2: Core Identifier Validation
    if id_col in cleaned_df.columns:
        missing_ids = cleaned_df[id_col].isna().sum()
        if missing_ids > 0:
            errors_found.append({
                "Issue Category": "Missing Transaction IDs",
                "Details": f"Found {missing_ids} rows missing order names/identifiers. These invalid records will be dropped."
            })
            cleaned_df = cleaned_df.dropna(subset=[id_col])

    # Check 3: Zip Code Truncation Fix (Restoring leading zeros destroyed by Excel)
    if zip_col in cleaned_df.columns:
        corrupted_zips = 0
        fixed_zips = []
        for val in cleaned_df[zip_col]:
            if pd.isna(val):
                fixed_zips.append(val)
                continue
            # Strip decimal points if converted to floats (e.g., '90210.0' -> '90210')
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

    # Check 4: Invisible Whitespace Trimming (FIXED LOGIC)
    str_cols = cleaned_df.select_dtypes(include=['object']).columns
    space_errors = 0
    for col in str_cols:
        # Direct string equality assessment avoids the .str.map attribute crash
        has_spaces = cleaned_df[col].astype(str) != cleaned_df[col].astype(str).str.strip()
        space_errors += has_spaces.sum()
        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
        
    if space_errors > 0:
        errors_found.append({
            "Issue Category": "Hidden Whitespace Errors",
            "Details": f"Trimmed {space_errors} fields containing accidental leading or trailing blank spaces."
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

# ----------------------------------------------------
# 4. MAIN INTERACTIVE DASHBOARD RUNTIME
# ----------------------------------------------------
if uploaded_file is not None:
    try:
        # File Loader Context
        if uploaded_file.name.endswith('.csv'):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
            
        # Execute processing pipeline
        with st.spinner("Analyzing spreadsheet composition..."):
            cleaned_data, audit_log = validate_and_clean(raw_df, platform)
            
        st.success("✨ Processing Complete!")
        
        # UI Tab Layout
        tab1, tab2 = st.tabs(["📋 Free Diagnostic Audit", "🔓 Premium Download Access"])
        
        with tab1:
            st.subheader("Diagnostic Audit Log")
            if not audit_log.empty:
                st.warning(f"⚠️ We isolated structural data issues in your current file:")
                st.dataframe(audit_log, use_container_width=True, hide_index=True)
                st.info("💡 Switch to the 'Premium Download Access' tab to unlock the completely repaired file.")
            else:
                st.success("🎉 Outstanding Structure! No critical formatting discrepancies detected.")
                st.dataframe(raw_df.head(5), use_container_width=True)

        with tab2:
            # Check gate access state
            if not st.session_state.premium_unlocked:
                st.subheader("🔒 This Export Feature is Locked")
                st.write("Join our premium members to download unlimited error-free spreadsheets.")
                
                # Global payment gateway action anchor
                checkout_url = "https://lemonsqueezy.com"
                
                st.markdown(f'''
                    <a href="{checkout_url}" target="_blank">
                        <button style="background-color:#28a745; color:white; border:none; 
                        padding:14px 28px; border-radius:6px; font-size:16px; font-weight:bold; 
                        cursor:pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            💳 Get Unlimited Access Safely via Lemon Squeezy ($9/mo)
                        </button>
                    </a>
                ''', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # License Key Submission Form Component
                st.write("🔑 **Already Subscribed? Activate Session Below:**")
                user_key = st.text_input("Enter your premium software license key:", type="password")
                
                # Verify master key
                if user_key:
                    if user_key.strip() == "LAUNCH_PREMIUM_2026":
                        st.session_state.premium_unlocked = True
                        st.success("🔑 Key Authenticated Successfully! Unlocking software assets...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid License Key pattern. Please double check your invoice details.")
            
            else:
                # Premium Screen state (Displays once st.session_state.premium_unlocked turns True)
                st.success("🎟️ Premium Access Verified! You have full processing permissions.")
                
                st.subheader("🛠️ Cleaned Dataset Preview (Top 10 Records)")
                st.dataframe(cleaned_data.head(10), use_container_width=True)
                
                # Generate download media stream asset
                excel_bytes = convert_df_to_excel(cleaned_data)
                
                st.download_button(
                    label="💾 Download Fully Repaired Excel Sheet",
                    data=excel_bytes,
                    file_name=f"REPAIRED_{platform}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Reset access button for demo/testing flexibility
                if st.button("🔄 Lock App (Test Gateway Again)"):
                    st.session_state.premium_unlocked = False
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Failed to cleanly process file structure: {e}. Check your platform selection toggle.")
else:
    # Landing configuration state
    st.info("💡 Welcome! Please upload an e-commerce data spreadsheet in the left sidebar configuration panel to run the file diagnostics tool.")
