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
    page_title="Enhanced Inventory Analysis",
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
        """Load sample inventory data"""
        inventory_sample = [
            ["AC0303020106", "FLAT ALUMINIUM PROFILE", "5.230", "4.000", "496"],
            ["AC0303020105", "RAIN GUTTER PROFILE", "8.360", "6.000", "1984"],
            ["AA0106010001", "HYDRAULIC POWER STEERING OIL", "12.500", "10.000", "2356"],
            ["AC0203020077", "Bulb beading LV battery flap", "3.500", "3.000", "248"],
            ["AC0303020104", "L- PROFILE JAM PILLAR", "15.940", "20.000", "992"],
            ["AA0112014000", "Conduit Pipe Filter to Compressor", "25", "30", "1248"],
            ["AA0115120001", "HVPDU ms", "18", "12", "1888"],
            ["AA0119020017", "REAR TURN INDICATOR", "35", "40", "1512"],
            ["AA0119020019", "REVERSING LAMP", "28", "20", "1152"],
            ["AA0822010800", "SIDE DISPLAY BOARD", "42", "50", "2496"],
            ["BB0101010001", "ENGINE OIL FILTER", "65", "45", "1300"],
            ["BB0202020002", "BRAKE PAD SET", "22", "25", "880"],
            ["CC0303030003", "CLUTCH DISC", "8", "12", "640"],
            ["DD0404040004", "SPARK PLUG", "45", "35", "450"],
            ["EE0505050005", "AIR FILTER", "30", "28", "600"],
            ["FF0606060006", "FUEL FILTER", "55", "50", "1100"],
            ["GG0707070007", "TRANSMISSION OIL", "40", "35", "800"],
            ["HH0808080008", "COOLANT", "22", "30", "660"],
            ["II0909090009", "BRAKE FLUID", "15", "12", "300"],
            ["JJ1010101010", "WINDSHIELD WASHER", "33", "25", "495"]
        ]
        
        inventory_data = []
        for row in inventory_sample:
            inventory_data.append({
                'Material': row[0],
                'Description': row[1],
                'QTY': self.safe_float_convert(row[2]),
                'RM IN QTY': self.safe_float_convert(row[3]),
                'Stock_Value': self.safe_int_convert(row[4])
            })
        
        return inventory_data
    
    def standardize_inventory_data(self, df):
        """Standardize inventory data and extract QTY and RM columns"""
        if df is None or df.empty:
            return []
        
        # Find required columns (case insensitive)
        qty_columns = ['qty', 'quantity', 'current_qty', 'stock_qty']
        rm_columns = ['rm', 'rm_qty', 'required_qty', 'norm_qty', 'target_qty', 'rm_in_qty', 'ri_in_qty']
        material_columns = ['material', 'material_code', 'part_number', 'item_code', 'code', 'part_no']
        desc_columns = ['description', 'item_description', 'part_description', 'desc']
        value_columns = ['stock_value', 'value', 'amount', 'cost']
        
        # Get column names (case insensitive)
        available_columns = {k.lower().replace(' ', '_'): k for k in df.columns}
        
        # Find the best matching columns
        qty_col = None
        rm_col = None
        material_col = None
        desc_col = None
        value_col = None
        
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
                
                if material and material.lower() != 'nan' and qty >= 0 and rm >= 0:
                    item = {
                        'Material': material,
                        'Description': str(record.get(desc_col, '')).strip() if desc_col else '',
                        'QTY': qty,
                        'RM IN QTY': rm,
                        'Stock_Value': self.safe_int_convert(record.get(value_col, 0)) if value_col else 0
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
                'Stock_Value': stock_value
            }
            processed_data.append(processed_item)
            
            # Update summary
            summary_data[status]['count'] += 1
            summary_data[status]['value'] += stock_value
        
        return processed_data, summary_data

def main():
    # Initialize analyzer
    analyzer = InventoryAnalyzer()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Enhanced Inventory Analysis</h1>', unsafe_allow_html=True)
    
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
        help="Upload a CSV or Excel file with QTY and RM IN QTY columns"
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
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Graphical Analysis", "📋 Detailed Data", "📤 Export"])
    
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
            show_stock_impact = st.checkbox("Stock Impact Analysis", value=False)
        
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
                hover_data=['Material', 'Variance_%']
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
        
        if show_stock_impact:
            st.subheader("📊 Stock Value Impact by Status")
            
            status_values = {status: data['value'] for status, data in summary_data.items()}
            
            fig_impact = px.bar(
                x=list(status_values.keys()),
                y=list(status_values.values()),
                color=list(status_values.keys()),
                color_discrete_map=analyzer.status_colors,
                title="Stock Value Impact by Status"
            )
            fig_impact.update_layout(xaxis_title="Status", yaxis_title="Stock Value (₹)")
            
            st.plotly_chart(fig_impact, use_container_width=True)
    
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
        
        # Status filter
        status_filter = st.multiselect(
            "Filter by Status:",
            options=['Within Norms', 'Excess Inventory', 'Short Inventory'],
            default=['Within Norms', 'Excess Inventory', 'Short Inventory']
        )
        
        # Apply filter
        filtered_df = df_display[df_display['Status'].isin(status_filter)]
        
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
        st.header("📤 Export Options")
        
        # Prepare export data
        df_export = pd.DataFrame(processed_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Download Detailed Report")
            
            # Convert to CSV
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Report",
                data=csv_data,
                file_name=f"inventory_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Convert to Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Summary sheet
                summary_df = pd.DataFrame([
                    {'Status': status, 'Count': data['count'], 'Stock_Value': data['value']}
                    for status, data in summary_data.items()
                ])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed data
                df_export.to_excel(writer, sheet_name='Detailed_Analysis', index=False)
                
                # Status-wise sheets
                for status in ['Excess Inventory', 'Short Inventory', 'Within Norms']:
                    status_data = df_export[df_export['Status'] == status]
                    if not status_data.empty:
                        status_data.to_excel(writer, sheet_name=status.replace(' ', '_'), index=False)
            
            excel_data = excel_buffer.getvalue()
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_data,
                file_name=f"inventory_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            st.subheader("📊 Export Summary")
            
            total_parts = len(processed_data)
            total_value = sum(item['Stock_Value'] for item in processed_data)
            
            st.write(f"**Total Parts Analyzed:** {total_parts}")
            st.write(f"**Total Stock Value:** ₹{total_value:,}")
            st.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Tolerance Used:** ±{tolerance}%")
            
            for status, data in summary_data.items():
                percentage = (data['count'] / total_parts * 100) if total_parts > 0 else 0
                st.write(f"**{status}:** {data['count']} parts ({percentage:.1f}%)")

def create_top_parts_chart(processed_data, status_filter, color):
    """Create bar chart for top parts by stock value for specific status"""
    filtered_data = [item for item in processed_data if item['Status'] == status_filter]
    
    if not filtered_data:
        st.info(f"No {status_filter} items found")
        return
    
    # Sort by stock value and get top 10
    sorted_data = sorted(filtered_data, key=lambda x: x['Stock_Value'], reverse=True)[:10]
    
    materials = [item['Material'] for item in sorted_data]
    values = [item['Stock_Value'] for item in sorted_data]
    
    fig = px.bar(
        x=materials,
        y=values,
        title=f"Top 10 {status_filter} Parts by Stock Value",
        labels={'x': 'Material Code', 'y': 'Stock Value (₹)'},
        color_discrete_sequence=[color]
    )
    
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
