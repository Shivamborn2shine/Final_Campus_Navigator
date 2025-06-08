import streamlit as st
import base64
import pandas as pd
import os
from utils.data_manager import DataManager
from utils.visualization import create_campus_map
from components.search import search_interface
from components.navigator import navigator_interface
from components.details import details_view

# Page configuration
st.set_page_config(
    page_title="Smart Campus Navigator",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)




# ===== ENHANCED HEADING WITH LOGO =====
# Premium header with logo inside gradient box
import streamlit as st
import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

img_base64 = get_base64_image("assets/geu_logo.png")

# Premium header with logo inside gradient box
header = st.container()
with header:
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%); 
                    padding: 20px; 
                    border-radius: 15px;
                    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;'>
            <div>
                <h1 style='color: white; margin: 0; padding: 0; font-size: 2.5rem;'>
                    GEU Campus Navigator <span style='font-size: 1.5rem;'>PRO</span>
                </h1>
                <p style='color: rgba(255,255,255,0.9); font-size: 1.1rem; margin-top: 5px;'>
                    The Ultimate Campus Exploration Platform | Powered
                </p>
            </div>
            <div style='margin-left: 20px;'>
                <img src='data:image/png;base64,{img_base64}' 
                     style='height: 80px; width: auto; border-radius: 5px;' />
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ===== END OF ENHANCED HEADING =====





# Initialize session state variables if they don't exist
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
if 'selected_item' not in st.session_state:
    st.session_state.selected_item = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = "departments"  # Start at the top level
if 'nav_history' not in st.session_state:
    st.session_state.nav_history = []
if 'parent_item' not in st.session_state:
    st.session_state.parent_item = None

# Application title
st.title("Now Don't get Lost just be focused and on time")

# Main content layout with columns
col1, col2 = st.columns([1, 2])

# Sidebar for data management
with st.sidebar:
    st.header("Data Management")
    
    upload_tab, export_tab = st.tabs(["Import Data", "Export Data"])
    
    with upload_tab:
        uploaded_file = st.file_uploader("Upload Campus Data CSV", type=['csv'])
        if uploaded_file is not None:
            try:
                if st.button("Import Data"):
                    st.session_state.data_manager.import_from_csv(uploaded_file)
                    st.success("Data imported successfully!")
                    # Reset navigation state
                    st.session_state.current_view = "departments"
                    st.session_state.nav_history = []
                    st.session_state.selected_item = None
                    st.session_state.parent_item = None
                    st.rerun()
            except Exception as e:
                st.error(f"Error importing data: {str(e)}")
    
    with export_tab:
        if st.button("Export Current Data"):
            # Add export format options
            export_format = st.selectbox(
                "Export format",
                options=["Standard format", "Simple format"],
                index=0
            )
            
            format_type = "standard" if export_format == "Standard format" else "simple"
            csv_data = st.session_state.data_manager.export_to_csv(format_type)
            
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="campus_data_export.csv",
                mime="text/csv"
            )
    
    # Sample data options
    sample_format = st.selectbox(
        "Sample data format",
        options=["Standard format", "Simple format"],
        index=0,
        key="sample_format"
    )
    
    # Load sample data button
    if st.button("Load Sample Data"):
        try:
            # Select the appropriate sample file based on format
            if sample_format == "Standard format":
                sample_path = "data/sample_campus_data.csv"
            else:  # Simple format
                sample_path = "data/simple_campus_data.csv"
                
            if os.path.exists(sample_path):
                st.session_state.data_manager.import_from_file(sample_path)
                st.success(f"Sample data ({sample_format}) loaded successfully!")
                # Reset navigation state
                st.session_state.current_view = "departments"
                st.session_state.nav_history = []
                st.session_state.selected_item = None
                st.session_state.parent_item = None
                st.rerun()
            else:
                st.warning(f"Sample data file {sample_path} not found.")
        except Exception as e:
            st.error(f"Error loading sample data: {str(e)}")

# Column 1: Navigation and Search
with col1:
    st.subheader("Search & Navigation")
    
    # Search interface
    search_interface()
    
    st.divider()
    
    # Navigator interface
    navigator_interface()

# Column 2: Map Visualization and Details
with col2:
    tab1, tab2 = st.tabs(["Campus Map", "Details"])
    
    with tab1:
        st.subheader("Campus Visualization")
        
        if st.session_state.data_manager.has_data():
            # Create the visualization based on the current view and selection
            fig = create_campus_map(
                st.session_state.data_manager, 
                st.session_state.current_view,
                st.session_state.selected_item,
                st.session_state.parent_item
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available. Please import campus data using the sidebar.")
            # Display some campus building images
            st.image("assets/graphiceraimage.jpg", 
            caption="GEU Campus", 
            use_column_width=True)

    
    with tab2:
        # Details view
        details_view()

# Footer
st.markdown("---")
st.caption("Smart Campus Navigator - Navigate your campus efficiently")
