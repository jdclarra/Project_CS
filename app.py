import streamlit as st  #load Streamlit, st is the short name
import plotly.express as px   # library for nicer charts

st.title("Exchange Cost Planner")  #App Title
st.write("Estimate the cost of your exchange semester")

st.sidebar.header("Your details") #Sidebar

city=st.sidebar.selectbox ("City", ["Madrid", "Copenhagen"])
months=st.sidebar.slider("Number of months", 3, 12, 4)
lifestyle=st.sidebar.radio("Lifestyle", ["Budget", "Balanced", "Comfortable"])
monthly_budget=st.sidebar.number_input("Your monthly Budget (CHF)", min_value=0, value=1000, step=100)
total_budget = monthly_budget * months

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

    left, right = st.columns([3, 2])   # left column wider than right

# ---------- Cost breakdown (donut chart) ----------
with left:
    with st.container(border=True):
        st.subheader("Cost breakdown (per month)")

        chart_col, legend_col = st.columns(2)   # chart left, list right

        with chart_col:
            fig = px.pie(names=list(costs.keys()), values=list(costs.values()), hole=0.6)
            fig.update_traces(textinfo="none")   # hide percentages on the chart
            fig.update_layout(
                showlegend=False,                # we build our own list next to it
                height=250,
                margin=dict(t=0, b=0, l=0, r=0),
                annotations=[dict(text=f"CHF {monthly_estimate:,}<br>per month",
                                  showarrow=False, font_size=18)],   # text in the middle
            )
            st.plotly_chart(fig, use_container_width=True)

        with legend_col:
            for category, amount in costs.items():   # one line per category
                st.write(f"**{category}**: CHF {amount}")

# ---------- Budget comparison ----------
with right:
    with st.container(border=True):
        st.subheader("Your budget")

        st.write(f"Budget: CHF {monthly_budget:,}")
        st.progress(1.0)                          # full bar = budget

        st.write(f"Estimate: CHF {monthly_estimate:,}")
        if monthly_budget > 0:                    # avoid dividing by 0
            st.progress(min(monthly_estimate / monthly_budget, 1.0))

        remaining = monthly_budget - monthly_estimate
        if remaining >= 0:
            st.success(f"CHF {remaining:,} remaining per month")
        else:
            st.warning(f"CHF {abs(remaining):,} over budget per month")