import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

# Function to load default data
@st.cache_data
def load_default_data():
    return pd.read_csv(
        r'C:\Users\Extreme\OneDrive\Desktop\streamlit  dashboards\pharmacy\salesdaily.csv'
    )

# Function to load uploaded files (supports Excel and CSV)
def load_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(uploaded_file, engine='openpyxl')
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        else:
            st.sidebar.error("Unsupported file type! Please upload an Excel or CSV file.")
            st.stop()
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
        st.stop()

# Sidebar for file upload or default dataset
st.sidebar.title("Upload or Load Dataset")

data_source = st.sidebar.radio(
    "Choose Data Source:",
    ("Default Dataset", "Upload Your Own Dataset")
)

# Load dataset based on user input
if data_source == "Default Dataset":
    pharmacy_data = load_default_data()
    st.sidebar.success("Default dataset loaded successfully!")
else:
    uploaded_file = st.sidebar.file_uploader("Upload an Excel or CSV file", type=['xlsx', 'csv'])
    if uploaded_file is not None:
        pharmacy_data = load_uploaded_file(uploaded_file)
        st.sidebar.success("Dataset uploaded successfully!")
    else:
        st.sidebar.warning("Please upload a dataset to proceed.")
        st.stop()

# Main dashboard options
st.sidebar.title("Pharmacy Data Dashboard")
main_option = st.sidebar.radio(
    "Select Analysis Type",
    ["Sales Trends", "Category-Specific Analysis", "Peak Hours or Days", "Correlation Analysis"]
)
# Convert date column to datetime
pharmacy_data['datum'] = pd.to_datetime(pharmacy_data['datum'], errors='coerce')

# Sidebar filters
start_date = st.sidebar.date_input("Start Date", pharmacy_data['datum'].min().date())
end_date = st.sidebar.date_input("End Date", pharmacy_data['datum'].max().date())
filtered_data = pharmacy_data[
    (pharmacy_data['datum'] >= pd.Timestamp(start_date)) & (pharmacy_data['datum'] <= pd.Timestamp(end_date))
]

# Apply additional filters dynamically based on columns
for column in pharmacy_data.columns:
    if pharmacy_data[column].dtype in ['int64', 'float64']:
        selected_range = st.sidebar.slider(
            f"{column} Range",
            float(filtered_data[column].min()),
            float(filtered_data[column].max()),
            (float(filtered_data[column].min()), float(filtered_data[column].max()))
        )
        filtered_data = filtered_data[filtered_data[column].between(*selected_range)]

# Refresh Button
if st.button("Refresh Dashboard"):
    st.experimental_set_query_params()

# Tooltip Message
tooltip_message = (
    "The dataset is a working process. You cannot open the Excel file directly, "
    "and no modifications can be made. You can only add data to existing columns, "
    "and you cannot change the column names."
)
st.markdown(
    f'<span style="color: grey; font-size: 12px; text-decoration: underline;">{tooltip_message}</span>',
    unsafe_allow_html=True
)
# Main content based on the selected option
st.title(main_option)

if main_option == "Sales Trends":
    st.subheader("Sales Trends Over Time")
    # Ensure we only sum numeric columns
    numeric_data = filtered_data.select_dtypes(include=['number'])

    # Chart 1: Total Sales per Category
    category_totals = numeric_data.iloc[:, :8].sum()  # Adjust indexing based on your dataset
    fig1 = px.bar(
        x=category_totals.index,
        y=category_totals.values,
        color=category_totals.index,
        labels={"x": "Category", "y": "Total Sales"},
        title="Total Sales by Category"
    )
    st.plotly_chart(fig1)

    numeric_columns = filtered_data.select_dtypes(include=['number']).columns

    # Create Year-Month column
    filtered_data['Year'] = filtered_data['datum'].dt.year
    filtered_data['Month'] = filtered_data['datum'].dt.month
    filtered_data['Year-Month'] = pd.to_datetime(
        filtered_data[['Year', 'Month']].assign(Day=1), errors='coerce'
    )

    # Group by Year-Month
    monthly_sales = (
        filtered_data.groupby('Year-Month')[numeric_columns].sum().reset_index()
    )

    # Melt for multi-category plotting
    melted_monthly_sales = monthly_sales.melt(
        id_vars=["Year-Month"],
        value_vars=numeric_columns,
        var_name="Category",
        value_name="Sales"
    )

    # Plot the line chart
    fig1 = px.line(
        melted_monthly_sales,
        x="Year-Month",
        y="Sales",
        color="Category",
        title="Monthly Sales Trend",
        labels={"Year-Month": "Month", "Sales": "Total Sales"}
    )
    st.plotly_chart(fig1)

elif main_option == "Category-Specific Analysis":


    st.subheader(f"Category-Specific Analysis Products")

    # Convert 'datum' to datetime
    filtered_data['datum'] = pd.to_datetime(filtered_data['datum'], format='%d/%m/%Y')

    # Summing sales for each pharmaceutical code
    pharma_codes = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']
    sales_by_code = filtered_data[pharma_codes].sum().reset_index()
    sales_by_code.columns = ['Pharmaceutical Code', 'Sales']

    # Sort to get the top and low-performing products
    top_products = sales_by_code.nlargest(10, 'Sales')
    low_products = sales_by_code.nsmallest(10, 'Sales')

    # Add a radio button to select between 'Top' and 'Low'
    category = st.radio(
        "Select Category:",
        ("Top 10 Pharmaceutical Products by Sales", "Low 10 Pharmaceutical Products by Sales")
    )

    # Display the appropriate chart based on the radio button selection
    if category == "Top 10 Pharmaceutical Products by Sales":
        fig_top = px.bar(
            top_products,
            x='Pharmaceutical Code',
            y='Sales',
            title="Top 10 Pharmaceutical Products by Sales",
            color='Pharmaceutical Code',
            labels={'Sales': 'Total Sales', 'Pharmaceutical Code': 'Product Code'}
        )
        st.plotly_chart(fig_top)

    elif category == "Low 10 Pharmaceutical Products by Sales":
        fig_low = px.bar(
            low_products,
            x='Pharmaceutical Code',
            y='Sales',
            title="Low 10 Pharmaceutical Products by Sales",
            color='Pharmaceutical Code',
            labels={'Sales': 'Total Sales', 'Pharmaceutical Code': 'Product Code'}
        )
        st.plotly_chart(fig_low)
    # Pie chart showing the sales contribution of each pharmaceutical code
    fig_pie = px.pie(
        sales_by_code,
        names='Pharmaceutical Code',
        values='Sales',
        title="Sales Contribution by Pharmaceutical Codes",
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    st.plotly_chart(fig_pie)
    # Ensure numeric columns for grouping
    numeric_columns = filtered_data.select_dtypes(include=['number']).columns

    # Convert Year and Month to numeric and filter invalid rows
    filtered_data['Year'] = pd.to_numeric(filtered_data['Year'], errors='coerce')
    filtered_data['Month'] = pd.to_numeric(filtered_data['Month'], errors='coerce')
    filtered_data = filtered_data.dropna(subset=['Year', 'Month'])

    # Create Year-Month column
    filtered_data['Year-Month'] = pd.to_datetime(
        filtered_data[['Year', 'Month']].assign(Day=1), errors='coerce'
    )

    # Group by Year-Month
    monthly_sales = (
        filtered_data.groupby('Year-Month')[numeric_columns].sum().reset_index()
    )

    # Melt for multi-category plotting
    melted_monthly_sales = monthly_sales.melt(
        id_vars=["Year-Month"],
        value_vars=numeric_columns[:8],  # Adjust to include relevant columns
        var_name="Category",
        value_name="Sales"
    )

    # Plot the line chart
    fig2 = px.line(
        melted_monthly_sales,
        x="Year-Month",
        y="Sales",
        color="Category",
        title="Monthly Sales Trend",
        labels={"Year-Month": "Month", "Sales": "Total Sales"},
        facet_col="Category",  # Create facets for each category
        facet_col_wrap=4  # Adjust layout
    )
    st.plotly_chart(fig2)



elif main_option == "Peak Hours or Days":
    st.subheader("Peak Hours or Days Analysis")

    # Convert 'datum' to datetime and extract Hour and Weekday information
    filtered_data['datum'] = pd.to_datetime(filtered_data['datum'], format='%d/%m/%Y')
    filtered_data['Hour'] = filtered_data['datum'].dt.hour
    filtered_data['Weekday'] = filtered_data['datum'].dt.day_name()

    # Define pharmaceutical codes (make sure it's defined correctly)
    pharma_codes = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']

    # Summing sales for each hour of the day
    sales_by_hour = filtered_data.groupby('Hour')[pharma_codes].sum().reset_index()

    # Summing sales for each weekday
    sales_by_weekday = filtered_data.groupby('Weekday')[pharma_codes].sum().reset_index()

    # Sort weekdays in the correct order
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    sales_by_weekday['Weekday'] = pd.Categorical(sales_by_weekday['Weekday'], categories=weekday_order, ordered=True)
    sales_by_weekday = sales_by_weekday.sort_values('Weekday')

    # Peak Hours Visualization - Line Chart for all Pharma Codes
    fig_hour_all = px.line(
        sales_by_hour,
        x='Hour',
        y=pharma_codes,
        title="Sales by Hour of the Day for All Products",
        labels={'Hour': 'Hour of the Day', 'value': 'Total Sales'},
        markers=True,
        line_group='variable'
    )
    st.plotly_chart(fig_hour_all)

    # Peak Days Visualization - Line Chart for All Pharma Codes
    fig_day_all = px.line(
        sales_by_weekday,
        x='Weekday',
        y=pharma_codes,
        title="Sales by Weekday for All Products",
        labels={'Weekday': 'Day of the Week', 'value': 'Total Sales'},
        markers=True,
        line_group='variable'
    )
    st.plotly_chart(fig_day_all)




elif main_option == "Correlation Analysis":
    st.subheader("Correlation Analysis Between Categories")
    # Define pharmaceutical codes
    pharma_codes = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']

    # -------------------- 1. Correlation Matrix (Using Plotly) --------------------
    # Calculate the correlation between the pharmaceutical codes
    corr = filtered_data[pharma_codes].corr()

    # Convert correlation matrix to a format Plotly can work with
    corr_df = corr.reset_index().melt(id_vars='index')
    corr_df.columns = ['Product1', 'Product2', 'Correlation']

    # Generate the Plotly Scatter Plot for Correlation (use color instead of size)
    fig_corr = px.scatter(
        corr_df,
        x='Product1',
        y='Product2',
        color='Correlation',  # Using color to represent correlation strength
        title="Correlation Between Product Categories",
        labels={'Correlation': 'Correlation Coefficient', 'Product1': 'Product', 'Product2': 'Product'},
        hover_data={'Correlation': True}  # Show correlation values in hover
    )
    st.plotly_chart(fig_corr)

    # -------------------- 2. Scatter Plot Between Two Products --------------------
    # Select two products (e.g., M01AB and M01AE)
    fig_pairwise = px.scatter(
        filtered_data,
        x='M01AB',  # Example product 1
        y='M01AE',  # Example product 2
        title="Scatter Plot: M01AB vs M01AE",
        labels={'M01AB': 'M01AB Sales', 'M01AE': 'M01AE Sales'},
        opacity=0.7
    )
    st.plotly_chart(fig_pairwise)

    # -------------------- 3. Bar Chart for Total Sales by Product --------------------
    # Summing sales for each pharmaceutical code
    sales_by_code = filtered_data[pharma_codes].sum().reset_index()
    sales_by_code.columns = ['Pharmaceutical Code', 'Sales']

    # Bar Chart for Top 5 Products
    fig_bar = px.bar(
        sales_by_code,
        x='Pharmaceutical Code',
        y='Sales',
        title="Total Sales by Pharmaceutical Code",
        color='Sales',
        labels={'Sales': 'Total Sales', 'Pharmaceutical Code': 'Product Code'},
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig_bar)

# Sidebar message
st.sidebar.markdown("---")
st.sidebar.text("Use filters to customize the data!")
