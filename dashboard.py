import streamlit as st
import pandas as pd
import plotly.express as px 
import io
import random 
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import os
import matplotlib
# import smtplib
# from email.mime.text import MIMEText
#  from email.mime.multipart import MIMEMultipart

st.set_page_config(
    page_title='E-commerce Analytics Dashboard',
    layout='wide'
)

st_autorefresh(interval=30*1000,key='Auto_refresh')

st.title('📊💰🛒E-commerce Analytics Dashboard')
st.caption('Revenue, orders, customer behavior & performance insights')

if 'merged_df' not in st.session_state:
    if os.path.exists('merged_df.csv'):
        st.session_state.merged_df = pd.read_csv('merged_df.csv')
    else:
        st.session_state.merged_df = pd.DataFrame(columns=[
            'Customer ID', 'Purchase Amount (USD)', 'Category', 'Segment', 'Time stamp'
        ])

merged_df = st.session_state.merged_df

def new_fake_orders(n=5):
    new_orders = []
    for _ in range(n):
        new_orders.append({
            'Customer ID': random.randint(
                merged_df['Customer ID'].min(),
                merged_df['Customer ID'].max()
            ),
            'Purchase Amount (USD)': random.randint(20, 500),
            'Category': random.choice(
                merged_df['Category'].dropna().unique()
            ),
            'Time stamp': datetime.now()
        })
    return pd.DataFrame(new_orders)

st.sidebar.subheader('🧪 Simulate Live Data')
if st.sidebar.button('Generate New Orders'):
    new_data=new_fake_orders(5)
    merged_df = pd.concat([merged_df, new_data], ignore_index=True)
    st.session_state.merged_df = merged_df 
    merged_df.to_csv('merged_df.csv', index=False)
    st.success('New orders added and saved!')


merged_df['Time stamp'] = pd.to_datetime(merged_df['Time stamp'], errors='coerce')
total_revenue = merged_df['Purchase Amount (USD)'].sum()
total_orders = merged_df.shape[0]
aov = total_revenue / total_orders

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
col2.metric("📦 Total Orders", total_orders)
col3.metric("🧾 Avg Order Value", f"${aov:,.2f}")

revenue_threshold = 100000  
if 'alert_log' not in st.session_state:
    st.session_state.alert_log = []

if total_revenue > revenue_threshold:
    
    # def send_email_alert(subject, message, to_email):
    #     sender_email = 'my_email@gmail.com'
    #     password = 'APP_PASSWORD'
    #     msg = MIMEMultipart()
    #     msg['From'] = sender_email
    #     msg['To'] = to_email
    #     msg['Subject'] = subject
    #     msg.attach(MIMEText(message, 'plain'))
    #     server = smtplib.SMTP('smtp.gmail.com', 587)
    #     server.starttls()
    #     server.login(sender_email, password)
    #     server.sendmail(sender_email, to_email, msg.as_string())
    #     server.quit()
    #
    # send_email_alert('Revenue Alert', f"Revenue crossed ${total_revenue:,.0f}", 'receiver@gmail.com')   

    st.warning(f"⚡ Revenue Alert: Total revenue has crossed ${revenue_threshold:,.0f}!")
    alert_msg = f"Revenue crossed ${total_revenue:,.0f} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if alert_msg not in st.session_state.alert_log:
        st.session_state.alert_log.append(alert_msg)

    else:
        st.info(f"Total revenue is below the threshold (${revenue_threshold:,.0f})")

if st.session_state.alert_log:
    st.subheader("📢 Alert Log (Simulated)")
    for alert in st.session_state.alert_log[::-1]:
        st.info(alert)

st.sidebar.header('Filters')
merged_df['Time stamp']=pd.to_datetime(merged_df['Time stamp'])
min_date=merged_df['Time stamp'].min()
max_date=merged_df['Time stamp'].max()
date_range=st.sidebar.date_input('Select Date Range',[min_date,max_date])

categories = merged_df['Category'].unique()
selected_category = st.sidebar.multiselect("Select Category", categories, default=categories)

segments = merged_df['Segment'].unique()
selected_segment = st.sidebar.multiselect("Select Customer Segment", segments, default=segments)

filtered_df = merged_df[
    (merged_df['Time stamp'].dt.date.between(date_range[0], date_range[1])) &
    (merged_df['Category'].isin(selected_category)) &
    (merged_df['Segment'].isin(selected_segment))
]

st.subheader('📊 Category-wise Revenue')
category_data=filtered_df.groupby('Category')['Purchase Amount (USD)'].sum().reset_index()
category_chart=px.bar(
    category_data,
    x='Category',
    y='Purchase Amount (USD)',
    text_auto=True,
    title='Revenue by Category',
    color='Category'
)
st.plotly_chart(category_chart, use_container_width=True)

st.subheader('📈 Monthly Revenue Trend')
monthly_data = filtered_df.groupby(filtered_df['Time stamp'].dt.to_period('M'))['Purchase Amount (USD)'].sum().reset_index()
monthly_data['Time stamp'] = monthly_data['Time stamp'].dt.to_timestamp()
monthly_chart = px.line(
    monthly_data,
    x='Time stamp',               
    y='Purchase Amount (USD)',   
    markers=True,                 
    title='Monthly Revenue Trend'
)
monthly_chart.update_xaxes(tickformat="%b %Y") 
st.plotly_chart(monthly_chart, use_container_width=True)

st.subheader('🥇 Revenue by Customer Segment')
segment_data = filtered_df.groupby('Segment')['Purchase Amount (USD)'].sum().reset_index()
segment_chart = px.pie(
    segment_data,
    names='Segment',              
    values='Purchase Amount (USD)', 
    title='Revenue by Customer Segment',
    color='Segment'  
)
st.plotly_chart(segment_chart, use_container_width=True)

st.subheader('🏆 Top Customers')
top_cust_table = filtered_df.groupby('Customer ID')['Purchase Amount (USD)'].sum().sort_values(ascending=False).reset_index()
st.dataframe(top_cust_table.head(10))

st.sidebar.header('📥 Export Data')
csv=filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label='Download Filetered Data as CSV',
    data=csv,
    file_name='filtered_data.csv',
    mime='text/csv'
)
output=io.BytesIO()
with pd.ExcelWriter(output,engine='xlsxwriter') as writer:
    filtered_df.to_excel(writer,index=False,sheet_name='FilteredData')
   
    processed_data=output.getvalue()
st.sidebar.download_button(
    label="Download Filtered Data as Excel",
    data=processed_data,
    file_name='filtered_data.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
kpi_data={
    'Metric': ['Total Revenue', 'Total Orders', 'Average Order Value'],
    'Value': [total_revenue, total_orders, round(aov,2)]
}
kpi_df=pd.DataFrame(kpi_data)
kpi_csv=kpi_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="Download KPI Snapshot",
    data=kpi_csv,
    file_name='kpi_snapshot.csv',
    mime='text/csv'
)

st.subheader("🔍 Top Customers by Category")
if not filtered_df.empty:
    selected_category_for_drill = st.selectbox(
        "Select Category to see Top Customers",
        filtered_df['Category'].unique()
    )
    drill_df = filtered_df[filtered_df['Category'] == selected_category_for_drill]
    top_customers_drill = drill_df.groupby('Customer ID')['Purchase Amount (USD)'].sum().sort_values(ascending=False).reset_index()
    st.dataframe(top_customers_drill.head(10))

st.subheader("📈 Revenue Trend")
time_agg = st.radio("Select Time Aggregation", ['Daily', 'Weekly', 'Monthly'])

if not filtered_df.empty:
    if time_agg == 'Daily':
        trend_df = filtered_df.groupby(filtered_df['Time stamp'].dt.date)['Purchase Amount (USD)'].sum().reset_index()
        trend_df.rename(columns={'Time stamp':'Date'}, inplace=True)
        x_col = 'Date'
    elif time_agg == 'Weekly':
        trend_df = filtered_df.groupby(filtered_df['Time stamp'].dt.to_period('W'))['Purchase Amount (USD)'].sum().reset_index()
        trend_df['Time stamp'] = trend_df['Time stamp'].dt.start_time
        x_col = 'Time stamp'
    else:  
        trend_df = filtered_df.groupby(filtered_df['Time stamp'].dt.to_period('M'))['Purchase Amount (USD)'].sum().reset_index()
        trend_df['Time stamp'] = trend_df['Time stamp'].dt.to_timestamp()
        x_col = 'Time stamp'

    trend_chart = px.line(trend_df, x=x_col, y='Purchase Amount (USD)', markers=True, title=f'{time_agg} Revenue Trend')
    st.plotly_chart(trend_chart, use_container_width=True)

st.subheader("🏆 Top Customers Highlighted")
if not filtered_df.empty:
    top_customers_table = filtered_df.groupby('Customer ID')['Purchase Amount (USD)'].sum().reset_index()
    top_customers_table = top_customers_table.sort_values('Purchase Amount (USD)', ascending=False).head(20)
    st.dataframe(
        top_customers_table.style.background_gradient(subset=['Purchase Amount (USD)'], cmap='Greens')
    )
