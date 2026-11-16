import streamlit as st  #load Streamlit, st is the short name

st.title("Exchange Cost Planner")  #App Title
st.write("Estimate the cost of your exchange semester")

st.sidebar.header("Your details") #Sidebar

city=st.sidebar.selectbox ("City", ["Madrid", "Copenhagen"])
months=st.sidebar.slider("Number of months", 3, 12, 4)
lifestyle=st.sidebar.radio("Lifestyle", ["Budget", "Balanced", "Comfortable"])
monthly_budget=st.sidebar.number_input("Your monthly Budget (CHF)", min_value=0, value=1000, step=100)

costs={"Housing":600, "Groceries":250, "Transport":50, "Leisure":120, "Other":80}
one_time_costs=300 #e.g. tuition, flights, visa-->to be coded differently once we have the data

monthly_estimate=sum(costs.values())
total_estimate=monthly_estimate * months + one_time_costs

col1, col2 = st.columns(2)
col1.metric("Monthly estimate", f" CHF {monthly_estimate:}", border=True) #Border gibt eine Umrandung
col2.metric("Total stay estimate", f"CHF {total_estimate:}", f"Includes CHF {one_time_costs} one-time costs", border=True)
st.caption(f"Total includes CHF {one_time_costs} one-time costs")

