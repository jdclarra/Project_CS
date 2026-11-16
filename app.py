import streamlit as st  #load Streamlit, st is the short name

st.title("Exchange Cost Planner")  #App Title
st.write("Estimate the cost of your exchange semester")

st.sidebar.header("Your details") #Sidebar

city=st.sidebar.selectbox ("City", ["Madrid", "Copenhagen"])
months=st.sidebar.slider("Number of months", 3, 12, 4)
lifestyle=st.sidebar.radio("Lifestyle", ["Budget", "Balanced", "Comfortable"])
monthly_budget=st.sidebar.number_input("Your monthly Budget (CHF)", min_value=0, value=1000, step=100)
total_budget=monthly_budget * months