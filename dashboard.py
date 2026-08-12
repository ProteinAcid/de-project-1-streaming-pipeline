import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Order Analytics Dashboard", layout="wide")
st.title("📦 E-Commerce Order Analytics")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "de_project")
POSTGRES_USER = os.getenv("POSTGRES_USER", "vedant")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "localdev")

engine = create_engine(
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

@st.cache_data(ttl=60)
def load_data():
    orders = pd.read_sql("SELECT * FROM dbt_vedadnt.fct_orders", engine)
    customers = pd.read_sql("SELECT * FROM dbt_vedadnt.dim_customers", engine)
    return orders, customers

orders_df, customers_df = load_data()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Revenue", f"${orders_df['order_amount'].sum():,.2f}")

with col2:
    st.metric("Total Orders", len(orders_df))

with col3:
    st.metric("Unique Customers", len(customers_df))

import plotly.express as px

st.subheader("Top Customers by Lifetime Value")
top_customers = customers_df.sort_values("lifetime_value", ascending=False).head(10)

fig = px.bar(
    top_customers,
    x="customer_name",
    y="lifetime_value",
    color="lifetime_value",
    color_continuous_scale="Blues",
    labels={"customer_name": "Customer", "lifetime_value": "Lifetime Value ($)"},
)
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
)
st.plotly_chart(fig, width='stretch')

st.divider()
st.subheader("Recent Orders")

st.dataframe(orders_df.sort_values("event_timestamp", ascending=False).head(20))