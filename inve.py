import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import io
import base64
from matplotlib.figure import Figure
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(
    page_title="Enhanced Inventory Analysis with Vendor Filter",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .status-excess {
        border-left-color: #007bff !important;
    }
    .status-short {
        border-left-color: #dc3545 !important;
    }
    .status-normal {
        border-left-color: #28a745 !important;
    }
    .vendor-filter {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class InventoryAnalyzer:
    def __init__(self):
        self.status_colors = {
            'Within Norms': '#28a745',      # Green
            'Excess Inventory': '#007bff',   # Blue
            'Short Inventory': '#dc3545'     # Red
        }
        
    def safe_float_convert(self, value):
        """Safely convert string to float, handling commas and other formatting"""
        if pd.isna(value) or value == '' or value is None:
            return 0.0
        
        str_value = str(value).strip()
        str_value = str_value.replace(',', '').replace(' ', '')
        
        if str_value.endswith('%'):
            str_value = str_value[:-1]
        
        try:
            return float(str_value)
        except (ValueError, TypeError):
            return 0.0
    
    def safe_int_convert(self, value):
        """Safely convert string to int, handling commas and other formatting"""
        if pd.isna(value) or value == '' or value is None:
            return 0
        
        str_value = str(value).strip()
        str_value = str_value.replace(',', '').replace(' ', '')
        
        try:
            return int(float(str_value))
        except (ValueError, TypeError):
            return 0
    
    def load_sample_data(self):
        """Load sample inventory data with vendor information"""
        inventory_sample = [
            ["AC0303020106", "FLAT ALUMINIUM PROFILE", "5.230", "4.000", "496", "Vendor_A"],
            ["AC0303020105", "RAIN GUTTER PROFILE", "8.360", "6.000", "1984", "Vendor_B"],
            ["AA0106010001", "HYDRAULIC POWER STEERING OIL", "12.500", "10.000", "2356", "Vendor_A"],
            ["AC0203020077", "Bulb beading LV battery flap", "3.500", "3.000", "248", "Vendor_C"],
            ["AC0303020104", "L- PROFILE JAM PILLAR", "15.940", "20.000", "992", "Vendor_A"],
            ["AA0112014000", "Conduit Pipe Filter to Compressor", "25", "30", "1248", "Vendor_B"],
            ["AA0115120001", "HVPDU ms", "18", "12", "1888", "Vendor_D"],
            ["AA0119020017", "REAR TURN INDICATOR", "35", "40", "1512", "Vendor_C"],
            ["AA0119020019", "REVERSING LAMP", "28", "20", "1152", "Vendor_A"],
            ["AA0822010800", "SIDE DISPLAY BOARD", "42", "50", "2496", "Vendor_B"],
            ["BB0101010001", "ENGINE OIL FILTER", "65", "45", "1300", "Vendor_E"],
            ["BB0202020002", "BRAKE PAD SET", "22", "25", "880", "Vendor_C"],
            ["CC0303030003", "CLUTCH DISC", "8", "12", "640", "Vendor_D"],
            ["DD0404040004", "SPARK PLUG", "45", "35", "450", "Vendor_A"],
            ["EE0505050005", "AIR FILTER", "30", "28", "600", "Vendor_B"],
            ["FF0606060006", "FUEL FILTER", "55", "50", "1100", "Vendor_E"],
            ["GG0707070007", "TRANSMISSION OIL", "40", "35", "800", "Vendor_C"],
            ["HH0808080008", "COOLANT", "22", "30", "660", "Vendor_D"],
            ["II0909090009", "BRAKE FLUID", "15", "12", "300", "Vendor_A"],
            ["JJ1010101010", "WINDSHIELD WASHER", "33", "25", "495", "Vendor_B"]
        ]
        
        inventory_data = []
        for row in inventory_sample:
            inventory_data.append({
                'Material': row[0],
                'Description': row[1],
                'QTY': self.safe_float_convert(row[2]),
                'RM IN QTY': self.safe_float_convert(row[3]),
                'Stock_Value': self.safe_int_convert(row[4]),
                'Vendor': row[5]
            })
        
        return inventory_data
    
    def standardize_inventory_data(self, df):
        """Standardize inventory data and extract QTY, RM, and Vendor columns"""
        if df is None or df.empty:
            return []
        
        # Find required columns (case insensitive)
        qty_columns = ['qty', 'quantity', 'current_qty', 'stock_qty']
        rm_columns = ['rm', 'rm_qty', 'required_qty', 'norm_qty', 'target_qty', 'rm_in_qty', 'ri_in_qty']
        material_columns = ['material', 'material_code', 'part_number', 'item_code', 'code', 'part_no']
        desc_columns = ['description', 'item_description', 'part_description', 'desc']
        value_columns = ['stock_value', 'value', 'amount', 'cost']
        vendor_columns = ['vendor', 'vendor_name', 'supplier', 'supplier_name']
        
        # Get column names (case insensitive)
        available_columns = {k.lower().replace(' ', '_'): k for k in df.columns}
        
        # Find the best matching columns
        qty_col = None
        rm_col = None
        material_col = None
        desc_col = None
        value_col = None
        vendor_col = None
        
        for col_name in qty_columns:
            if col_name in available_columns:
                qty_col = available_columns[col_name]
                break
        
        for col_name in rm_columns:
            if col_name in available_columns:
                rm_col = available_columns[col_name]
                break
        
        for col_name in material_columns:
            if col_name in available_columns:
                material_col = available_columns[col_name]
                break
        
        for col_name in desc_columns:
            if col_name in available_columns:
                desc_col = available_columns[col_name]
                break
        
        for col_name in value_columns:
            if col_name in available_columns:
                value_col = available_columns[col_name]
                break
        
        for col_name in vendor_columns:
            if col_name in available_columns:
                vendor_col = available_columns[col_name]
                break
        
        if not qty_col:
            st.error("QTY/Quantity column not found in inventory file")
            return []
        
        if not rm_col:
            st.error("RM/RM IN QTY column not found in inventory file")
            return []
        
        if not material_col:
            st.error("Material/Part Number column not found in inventory file")
            return []
        
        # Process each record
        standardized_data = []
        for _, record in df.iterrows():
            try:
                material = str(record.get(material_col, '')).strip()
                qty = self.safe_float_convert(record.get(qty_col, 0))
                rm = self.safe_float_convert(record.get(rm_col, 0))
                vendor = str(record.get(vendor_col, 'Unknown')).strip() if vendor_col else 'Unknown'
                
                if material and material.lower() != 'nan' and qty >= 0 and rm >= 0:
                    item = {
                        'Material': material,
                        'Description': str(record.get(desc_col, '')).strip() if desc_col else '',
                        'QTY': qty,
                        'RM IN QTY': rm,
                        'Stock_Value': self.safe_int_convert(record.get(value_col, 0)) if value_col else 0,
                        'Vendor': vendor
                    }
                    standardized_data.append(item)
                    
            except Exception as e:
                continue
        
        return standardized_data
    
    def calculate_variance(self, qty, rm):
        """Calculate variance percentage and absolute value"""
        if rm == 0:
            return 0, 0
        
        variance_percent = ((qty - rm) / rm) * 100
        variance_value = qty - rm
        return variance_percent, variance_value
    
    def determine_status(self, variance_percent, tolerance):
        """Determine inventory status based on variance and tolerance"""
        if abs(variance_percent) <= tolerance:
            return 'Within Norms'
        elif variance_percent > tolerance:
            return 'Excess Inventory'
        else:
            return 'Short Inventory'
    
    def process_data(self, inventory_data, tolerance):
        """Process inventory data and calculate analysis"""
        processed_data = []
        summary_data = {
            'Within Norms': {'count': 0, 'value': 0},
            'Excess Inventory': {'count': 0, 'value': 0},
            'Short Inventory': {'count': 0, 'value': 0}
        }
        
        for item in inventory_data:
            qty = item['QTY']
            rm = item['RM IN QTY']
            stock_value = item['Stock_Value']
            vendor = item['Vendor']
            
            # Calculate variance
            variance_percent, variance_value = self.calculate_variance(qty, rm)
            
            # Determine status
            status = self.determine_status(variance_percent, tolerance)
            
            # Store processed data
            processed_item = {
                'Material': item['Material'],
                'Description': item['Description'],
                'QTY': qty,
                'RM IN QTY': rm,
                'Variance_%': variance_percent,
                'Variance_Value': variance_value,
                'Status': status,
                'Stock_Value': stock_value,
                'Vendor': vendor
            }
            processed_data.append(processed_item)
            
            # Update summary
            summary_data[status]['count'] += 1
            summary_data[status]['value'] += stock_value
        
        return processed_data, summary_data
    
    def get_vendor_summary(self, processed_data):
        """Get summary data by vendor"""
        vendor_summary = {}
        
        for item in processed_data:
            vendor = item['Vendor']
            if vendor not in vendor_summary:
                vendor_summary[vendor] = {
                    'total_parts': 0,
                    'total_qty': 0,
                    'total_rm': 0,
                    'total_value': 0,
                    'short_parts': 0,
                    'excess_parts': 0,
                    'normal_parts': 0
                }
            
            vendor_summary[vendor]['total_parts'] += 1
            vendor_summary[vendor]['total_qty'] += item['QTY']
            vendor_summary[vendor]['total_rm'] += item['RM IN QTY']
            vendor_summary[vendor]['total_value'] += item['Stock_Value']
            
            if item['Status'] == 'Short Inventory':
                vendor_summary[vendor]['short_parts'] += 1
            elif item['Status'] == 'Excess Inventory':
                vendor_summary[vendor]['excess_parts'] += 1
            else:
                vendor_summary[vendor]['normal_parts'] += 1
        
        return vendor_summary

def main():
    # Initialize analyzer
    analyzer = InventoryAnalyzer()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Enhanced Inventory Analysis with Vendor Filter</h1>', unsafe_allow_html=True)
    
    # Sidebar for controls
    st.sidebar.header("⚙️ Control Panel")
    
    # Tolerance setting
    tolerance = st.sidebar.selectbox(
        "Tolerance Zone (+/-)",
        options=[10, 20, 30, 40, 50],
        index=2,  # Default to 30%
        format_func=lambda x: f"{x}%"
    )
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload Inventory File",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a CSV or Excel file with QTY, RM IN QTY, and Vendor columns"
    )
    
    # Load data
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            inventory_data = analyzer.standardize_inventory_data(df)
            
            if inventory_data:
                st.sidebar.success(f"✅ Loaded {len(inventory_data)} inventory items")
            else:
                st.sidebar.error("❌ No valid data found in uploaded file")
                inventory_data = analyzer.load_sample_data()
                st.sidebar.info("Using sample data instead")
        
        except Exception as e:
            st.sidebar.error(f"❌ Error loading file: {str(e)}")
            inventory_data = analyzer.load_sample_data()
            st.sidebar.info("Using sample data instead")
    else:
        inventory_data = analyzer.load_sample_data()
        st.sidebar.info("📋 Using sample data for demonstration")
    
    # Process data
    processed_data, summary_data = analyzer.process_data(inventory_data, tolerance)
    
    # Get vendor list for filtering
    vendors = sorted(list(set(item['Vendor'] for item in processed_data)))
    
    # Vendor filter
    st.sidebar.header("🏢 Vendor Filter")
    selected_vendor = st.sidebar.selectbox(
        "Select Vendor (for Short Inventory focus)",
        options=['All Vendors'] + vendors,
        help="Select a specific vendor to focus on their short inventory items"
    )
    
    # Apply vendor filter for short inventory focus
    if selected_vendor != 'All Vendors':
        st.markdown(f'<div class="vendor-filter">🏢 <strong>Vendor Focus:</strong> {selected_vendor} - Showing Short Inventory Analysis</div>', unsafe_allow_html=True)
        
        # Filter data for selected vendor and short inventory
        vendor_short_items = [item for item in processed_data if item['Vendor'] == selected_vendor and item['Status'] == 'Short Inventory']
        
        if vendor_short_items:
            st.info(f"Found {len(vendor_short_items)} short inventory items for {selected_vendor}")
        else:
            st.success(f"No short inventory items found for {selected_vendor}")
    
    # Display status criteria
    st.info(f"""
    **Status Criteria (Tolerance: ±{tolerance}%)**
    - 🟢 **Within Norms**: QTY = RM IN QTY ± {tolerance}%
    - 🔵 **Excess Inventory**: QTY > RM IN QTY + {tolerance}%
    - 🔴 **Short Inventory**: QTY < RM IN QTY - {tolerance}%
    """)
    
    # Summary Dashboard
    st.header("📈 Summary Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card status-normal">', unsafe_allow_html=True)
        st.metric(
            label="🟢 Within Norms",
            value=f"{summary_data['Within Norms']['count']} parts",
            delta=f"₹{summary_data['Within Norms']['value']:,}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card status-excess">', unsafe_allow_html=True)
        st.metric(
            label="🔵 Excess Inventory",
            value=f"{summary_data['Excess Inventory']['count']} parts",
            delta=f"₹{summary_data['Excess Inventory']['value']:,}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card status-short">', unsafe_allow_html=True)
        st.metric(
            label="🔴 Short Inventory",
            value=f"{summary_data['Short Inventory']['count']} parts",
            delta=f"₹{summary_data['Short Inventory']['value']:,}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Vendor Summary
    vendor_summary = analyzer.get_vendor_summary(processed_data)
    
    st.header("🏢 Vendor Summary")
    vendor_df = pd.DataFrame([
        {
            'Vendor': vendor,
            'Total Parts': data['total_parts'],
            'Total QTY': round(data['total_qty'], 2),
            'Total RM': round(data['total_rm'], 2),
            'Short Items': data['short_parts'],
            'Excess Items': data['excess_parts'],
            'Normal Items': data['normal_parts'],
            'Total Value': f"₹{data['total_value']:,}"
        }
        for vendor, data in vendor_summary.items()
    ])
    
    st.dataframe(vendor_df, use_container_width=True, hide_index=True)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Graphical Analysis", "📋 Detailed Data", "🏢 Vendor Analysis", "📤 Export"])
    
    with tab1:
        st.header("📊 Graphical Analysis")
        
        # Graph selection
        st.subheader("Select Graphs to Display")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_pie = st.checkbox("Status Distribution (Pie)", value=True)
            show_comparison = st.checkbox("QTY vs RM Comparison", value=True)
            show_variance_hist = st.checkbox("Variance Distribution", value=False)
        
        with col2:
            show_excess = st.checkbox("Top Excess Parts", value=True)
            show_short = st.checkbox("Top Short Parts", value=True)
            show_scatter = st.checkbox("QTY vs RM Scatter", value=False)
        
        with col3:
            show_normal = st.checkbox("Top Normal Parts", value=False)
            show_variance_top = st.checkbox("Top Variance Parts", value=True)
            show_vendor_qty = st.checkbox("Top 10 Vendors by QTY", value=True)
        
        # Create graphs
        if show_pie:
            st.subheader("📊 Status Distribution")
            
            # Prepare data for pie chart
            status_counts = {status: data['count'] for status, data in summary_data.items() if data['count'] > 0}
            
            if status_counts:
                fig_pie = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    color=list(status_counts.keys()),
                    color_discrete_map=analyzer.status_colors,
                    title="Inventory Status Distribution"
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
        
        if show_comparison:
            st.subheader("📊 QTY vs RM Comparison")
            
            # Get top 10 by stock value
            sorted_data = sorted(processed_data, key=lambda x: x['Stock_Value'], reverse=True)[:10]
            
            materials = [item['Material'] for item in sorted_data]
            qty_values = [item['QTY'] for item in sorted_data]
            rm_values = [item['RM IN QTY'] for item in sorted_data]
            
            fig_comparison = go.Figure()
            fig_comparison.add_trace(go.Bar(name='Current QTY', x=materials, y=qty_values, marker_color='#1f77b4'))
            fig_comparison.add_trace(go.Bar(name='RM IN QTY', x=materials, y=rm_values, marker_color='#ff7f0e'))
            
            fig_comparison.update_layout(
                title="QTY vs RM IN QTY Comparison (Top 10 by Stock Value)",
                xaxis_title="Material Code",
                yaxis_title="Quantity",
                barmode='group'
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        if show_vendor_qty:
            st.subheader("🏢 Top 10 Vendors by Total QTY")
            
            # Sort vendors by total QTY
            sorted_vendors = sorted(vendor_summary.items(), key=lambda x: x[1]['total_qty'], reverse=True)[:10]
            
            vendor_names = [vendor for vendor, _ in sorted_vendors]
            total_qtys = [data['total_qty'] for _, data in sorted_vendors]
            
            fig_vendor = go.Figure()
            fig_vendor.add_trace(go.Bar(name='Total QTY', x=vendor_names, y=total_qtys, marker_color='#1f77b4'))
            
            fig_vendor.update_layout(
                title="Top 10 Vendors by Total QTY",
                xaxis_title="Vendor",
                yaxis_title="Quantity",
                showlegend=False  # Hide legend since there's only one series
            )
            
            st.plotly_chart(fig_vendor, use_container_width=True)
        
        if show_excess:
            st.subheader("🔵 Top 10 Excess Inventory Parts")
            create_top_parts_chart(processed_data, 'Excess Inventory', analyzer.status_colors['Excess Inventory'])
        
        if show_short:
            st.subheader("🔴 Top 10 Short Inventory Parts")
            create_top_parts_chart(processed_data, 'Short Inventory', analyzer.status_colors['Short Inventory'])
        
        if show_normal:
            st.subheader("🟢 Top 10 Within Norms Parts")
            create_top_parts_chart(processed_data, 'Within Norms', analyzer.status_colors['Within Norms'])
        
        if show_variance_top:
            st.subheader("📊 Top 10 Materials by Variance")
            
            # Sort by absolute variance
            sorted_variance = sorted(processed_data, key=lambda x: abs(x['Variance_%']), reverse=True)[:10]
            
            materials = [item['Material'] for item in sorted_variance]
            variances = [item['Variance_%'] for item in sorted_variance]
            colors = [analyzer.status_colors[item['Status']] for item in sorted_variance]
            
            fig_variance = go.Figure(data=[
                go.Bar(x=materials, y=variances, marker_color=colors)
            ])
            
            fig_variance.update_layout(
                title="Top 10 Materials by Variance %",
                xaxis_title="Material Code",
                yaxis_title="Variance %"
            )
            fig_variance.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            
            st.plotly_chart(fig_variance, use_container_width=True)
        
        if show_scatter:
            st.subheader("📊 QTY vs RM Scatter Plot")
            
            df_processed = pd.DataFrame(processed_data)
            fig_scatter = px.scatter(
                df_processed,
                x='RM IN QTY',
                y='QTY',
                color='Status',
                color_discrete_map=analyzer.status_colors,
                title="QTY vs RM IN QTY Scatter Plot",
                hover_data=['Material', 'Variance_%', 'Vendor']
            )
            
            # Add diagonal line
            max_val = max(df_processed['QTY'].max(), df_processed['RM IN QTY'].max())
            fig_scatter.add_trace(go.Scatter(
                x=[0, max_val],
                y=[0, max_val],
                mode='lines',
                name='Perfect Match',
                line=dict(dash='dash', color='black')
            ))
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        if show_variance_hist:
            st.subheader("📊 Variance Distribution")
            
            variances = [item['Variance_%'] for item in processed_data]
            
            fig_hist = px.histogram(
                x=variances,
                nbins=20,
                title="Variance Distribution",
                labels={'x': 'Variance %', 'y': 'Frequency'}
            )
            
            # Add tolerance lines
            fig_hist.add_vline(x=tolerance, line_dash="dash", line_color="red", annotation_text=f"+{tolerance}%")
            fig_hist.add_vline(x=-tolerance, line_dash="dash", line_color="red", annotation_text=f"-{tolerance}%")
            
            st.plotly_chart(fig_hist, use_container_width=True)
    
    with tab2:
        st.header("📋 Detailed Analysis")
        
        # Convert to DataFrame for display
        df_display = pd.DataFrame(processed_data)
        
        # Format the DataFrame
        df_display['QTY'] = df_display['QTY'].round(2)
        df_display['RM IN QTY'] = df_display['RM IN QTY'].round(2)
        df_display['Variance_%'] = df_display['Variance_%'].round(1)
        df_display['Variance_Value'] = df_display['Variance_Value'].round(2)
        df_display['Stock_Value'] = df_display['Stock_Value'].apply(lambda x: f"₹{x:,}")
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.multiselect(
                "Filter by Status:",
                options=['Within Norms', 'Excess Inventory', 'Short Inventory'],
                default=['Within Norms', 'Excess Inventory', 'Short Inventory']
            )
        
        with col2:
            vendor_filter = st.multiselect(
                "Filter by Vendor:",
                options=vendors,
                default=vendors
            )
        
        # Apply filters
        filtered_df = df_display[
            (df_display['Status'].isin(status_filter)) & 
            (df_display['Vendor'].isin(vendor_filter))
        ]
        
        # Display filtered data
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Show summary stats
        st.subheader("📊 Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Parts", len(filtered_df))
        with col2:
            st.metric("Avg Variance %", f"{filtered_df['Variance_%'].mean():.1f}%")
        with col3:
            st.metric("Max Variance %", f"{filtered_df['Variance_%'].max():.1f}%")
        with col4:
            st.metric("Min Variance %", f"{filtered_df['Variance_%'].min():.1f}%")
    
    with tab3:
        st.header("🏢 Vendor-Specific Analysis")
        
        if selected_vendor != 'All Vendors':
            st.subheader(f"Short Inventory Analysis for {selected_vendor}")
            
            vendor_short_items = [item for item in processed_data if item['Vendor'] == selected_vendor and item['Status'] == 'Short Inventory']
            
            if vendor_short_items:
                # Create DataFrame for vendor short items
                vendor_short_df = pd.DataFrame(vendor_short_items)
                vendor_short_df['QTY'] = vendor_short_df['QTY'].round(2)
                vendor_short_df['RM IN QTY'] = vendor_short_df['RM IN QTY'].round(2)
                vendor_short_df['Variance_%'] = vendor_short_df['Variance_%'].round(1)
                vendor_short_df['Variance_Value'] = vendor_short_df['Variance_Value'].round(2)
                vendor_short_df['Stock_Value'] = vendor_short_df['Stock_Value'].apply(lambda x: f"₹{x:,}")
                
                st.dataframe(
                    vendor_short_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Chart for vendor short items
                if len(vendor_short_items) > 0:
                    materials = [item['Material'] for item in vendor_short_items[:10]]
                    shortages = [abs(item['Variance_Value']) for item in vendor_short_items[:10]]
                    
                    fig_shortage = go.Figure(data=[
                        go.Bar(x=materials, y=shortages, marker_color='#dc3545')
                    ])
                    
                    fig_shortage.update_layout(
                        title=f"Top 10 Short Items - {selected_vendor}",
                        xaxis_title="Material Code",
                        yaxis_title="Shortage Quantity"
                    )
                    st.plotly_chart(fig_shortage, use_container_width=True)
                
                # Summary metrics for vendor
                total_short_value = sum(item['Stock_Value'] for item in vendor_short_items if isinstance(item['Stock_Value'], (int, float)))
                avg_shortage = sum(abs(item['Variance_Value']) for item in vendor_short_items) / len(vendor_short_items)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Short Items Count", len(vendor_short_items))
                with col2:
                    st.metric("Total Short Value", f"₹{total_short_value:,}")
                with col3:
                    st.metric("Avg Shortage Qty", f"{avg_shortage:.2f}")
            
            else:
                st.success(f"✅ {selected_vendor} has no short inventory items!")
        
        else:
            st.subheader("All Vendors Analysis")
            
            # Vendor performance chart
            vendor_performance = []
            for vendor, data in vendor_summary.items():
                short_percentage = (data['short_parts'] / data['total_parts']) * 100 if data['total_parts'] > 0 else 0
                excess_percentage = (data['excess_parts'] / data['total_parts']) * 100 if data['total_parts'] > 0 else 0
                normal_percentage = (data['normal_parts'] / data['total_parts']) * 100 if data['total_parts'] > 0 else 0
                
                vendor_performance.append({
                    'Vendor': vendor,
                    'Short %': short_percentage,
                    'Excess %': excess_percentage,
                    'Normal %': normal_percentage,
                    'Total Parts': data['total_parts']
                })
            
            # Create stacked bar chart for vendor performance
            df_performance = pd.DataFrame(vendor_performance)
            
            fig_performance = go.Figure()
            
            fig_performance.add_trace(go.Bar(
                name='Short %',
                x=df_performance['Vendor'],
                y=df_performance['Short %'],
                marker_color='#dc3545'
            ))
            
            fig_performance.add_trace(go.Bar(
                name='Excess %',
                x=df_performance['Vendor'],
                y=df_performance['Excess %'],
                marker_color='#007bff'
            ))
            
            fig_performance.add_trace(go.Bar(
                name='Normal %',
                x=df_performance['Vendor'],
                y=df_performance['Normal %'],
                marker_color='#28a745'
            ))
            
            fig_performance.update_layout(
                title="Vendor Performance - Inventory Status Distribution",
                xaxis_title="Vendor",
                yaxis_title="Percentage",
                barmode='stack'
            )
            
            st.plotly_chart(fig_performance, use_container_width=True)
            
            # Vendor ranking table
            st.subheader("📊 Vendor Performance Ranking")
            
            # Sort by performance (least short items percentage is best)
            df_performance_sorted = df_performance.sort_values('Short %')
            
            # Add ranking
            df_performance_sorted['Rank'] = range(1, len(df_performance_sorted) + 1)
            
            # Reorder columns
            df_performance_display = df_performance_sorted[['Rank', 'Vendor', 'Total Parts', 'Normal %', 'Short %', 'Excess %']]
            
            # Format percentages
            for col in ['Normal %', 'Short %', 'Excess %']:
                df_performance_display[col] = df_performance_display[col].round(1).astype(str) + '%'
            
            st.dataframe(df_performance_display, use_container_width=True, hide_index=True)
    
    with tab4:
        st.header("📤 Export Options")
        
        # Prepare export data
        export_df = pd.DataFrame(processed_data)
        
        # Format for export
        export_df['QTY'] = export_df['QTY'].round(2)
        export_df['RM IN QTY'] = export_df['RM IN QTY'].round(2)
        export_df['Variance_%'] = export_df['Variance_%'].round(2)
        export_df['Variance_Value'] = export_df['Variance_Value'].round(2)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Export Full Analysis")
            
            # Convert DataFrame to CSV
            csv_data = export_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Full Analysis (CSV)",
                data=csv_data,
                file_name=f"inventory_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.subheader("🔴 Export Short Inventory Only")
            
            # Filter short inventory items
            short_items_df = export_df[export_df['Status'] == 'Short Inventory']
            
            if not short_items_df.empty:
                csv_short = short_items_df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download Short Inventory (CSV)",
                    data=csv_short,
                    file_name=f"short_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No short inventory items to export")
        
        # Export vendor summary
        st.subheader("🏢 Export Vendor Summary")
        
        vendor_summary_df = pd.DataFrame([
            {
                'Vendor': vendor,
                'Total_Parts': data['total_parts'],
                'Total_QTY': round(data['total_qty'], 2),
                'Total_RM': round(data['total_rm'], 2),
                'Short_Items': data['short_parts'],
                'Excess_Items': data['excess_parts'],
                'Normal_Items': data['normal_parts'],
                'Total_Value': data['total_value'],
                'Short_Percentage': round((data['short_parts'] / data['total_parts']) * 100, 2) if data['total_parts'] > 0 else 0,
                'Performance_Score': round(100 - ((data['short_parts'] / data['total_parts']) * 100), 2) if data['total_parts'] > 0 else 100
            }
            for vendor, data in vendor_summary.items()
        ])
        
        csv_vendor = vendor_summary_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Vendor Summary (CSV)",
            data=csv_vendor,
            file_name=f"vendor_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Export statistics
        st.subheader("📈 Analysis Summary")
        
        total_parts = len(processed_data)
        total_value = sum(item['Stock_Value'] for item in processed_data if isinstance(item['Stock_Value'], (int, float)))
        
        summary_stats = {
            'Analysis Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Tolerance Used': f"{tolerance}%",
            'Total Parts Analyzed': total_parts,
            'Total Stock Value': f"₹{total_value:,}",
            'Within Norms': f"{summary_data['Within Norms']['count']} ({(summary_data['Within Norms']['count']/total_parts)*100:.1f}%)",
            'Excess Inventory': f"{summary_data['Excess Inventory']['count']} ({(summary_data['Excess Inventory']['count']/total_parts)*100:.1f}%)",
            'Short Inventory': f"{summary_data['Short Inventory']['count']} ({(summary_data['Short Inventory']['count']/total_parts)*100:.1f}%)",
            'Total Vendors': len(vendor_summary),
            'Average Parts per Vendor': round(total_parts / len(vendor_summary), 1)
        }
        
        for key, value in summary_stats.items():
            st.write(f"**{key}:** {value}")

def create_top_parts_chart(processed_data, status_filter, color):
    """Helper function to create top parts charts"""
    # Filter and sort data
    filtered_data = [item for item in processed_data if item['Status'] == status_filter]
    
    if not filtered_data:
        st.info(f"No {status_filter.lower()} items found")
        return
    
    # Sort by absolute variance value for better insights
    sorted_data = sorted(filtered_data, key=lambda x: abs(x['Variance_Value']), reverse=True)[:10]
    
    materials = [item['Material'] for item in sorted_data]
    variances = [abs(item['Variance_Value']) for item in sorted_data]
    
    fig = go.Figure(data=[
        go.Bar(x=materials, y=variances, marker_color=color)
    ])
    
    fig.update_layout(
        title=f"Top 10 {status_filter} Parts by Variance",
        xaxis_title="Material Code",
        yaxis_title="Absolute Variance Value"
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
