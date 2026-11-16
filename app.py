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


def info_box(title, amount, note):
    """Shows a box with a title, a big amount and a small note."""
    with st.container(border=True):
        st.metric(title, f"CHF {amount:,}")
        st.caption(note)

col1, col2 = st.columns(2)
with col1:
    info_box("Monthly estimate", monthly_estimate, "Based on your city, housing and lifestyle")
with col2:
    info_box("Total stay estimate", total_estimate, f"Includes CHF {one_time_costs} one-time costs")