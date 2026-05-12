import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nassau Candy Shipping Analysis",
    page_icon="🍬",
    layout="wide"
)

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df            = pd.read_csv("nassau_candy_clean.csv")
    route_stats   = pd.read_csv("route_stats.csv")
    region_stats  = pd.read_csv("region_stats.csv")
    shipmode_stats = pd.read_csv("shipmode_stats.csv")
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"])
    return df, route_stats, region_stats, shipmode_stats

df, route_stats, region_stats, shipmode_stats = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/candy.png", width=80)
st.sidebar.title("🍬 Nassau Candy")
st.sidebar.markdown("---")

st.sidebar.header("Filters")

# Date range filter
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Region filter
all_regions = ["All"] + sorted(df["Region"].unique().tolist())
selected_region = st.sidebar.selectbox("Region", all_regions)

# Ship Mode filter
all_modes = ["All"] + sorted(df["Ship Mode"].unique().tolist())
selected_mode = st.sidebar.selectbox("Ship Mode", all_modes)

# Lead time threshold slider
threshold = st.sidebar.slider(
    "Delay Threshold (days)",
    min_value=1, max_value=11, value=7,
    help="Shipments above this are considered delayed"
)

# ── Apply Filters ─────────────────────────────────────────────────────────────
filtered = df.copy()
if len(date_range) == 2:
    filtered = filtered[
        (filtered["Order Date"].dt.date >= date_range[0]) &
        (filtered["Order Date"].dt.date <= date_range[1])
    ]
if selected_region != "All":
    filtered = filtered[filtered["Region"] == selected_region]
if selected_mode != "All":
    filtered = filtered[filtered["Ship Mode"] == selected_mode]

filtered["Is_Delayed"] = (filtered["Lead Time (Days)"] > threshold).astype(int)

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🍬 Nassau Candy — Factory-to-Customer Shipping Route Efficiency")
st.markdown("Interactive dashboard analyzing shipping performance across all routes, regions, and ship modes.")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Shipments",    f"{len(filtered):,}")
k2.metric("Avg Lead Time",      f"{filtered['Lead Time (Days)'].mean():.2f} days")
k3.metric("Delay Rate",         f"{filtered['Is_Delayed'].mean()*100:.1f}%")
k4.metric("Unique Routes",      f"{filtered['Route'].nunique()}")
k5.metric("Fastest Ship Mode",  shipmode_stats.loc[shipmode_stats['Avg_Lead_Time'].idxmin(), 'Ship Mode'])

st.markdown("---")

# ── TAB LAYOUT ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Route Efficiency",
    "🗺️ Geographic Map",
    "🚚 Ship Mode Analysis",
    "🔍 Route Drill-Down"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Route Efficiency
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Route Performance Leaderboard")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏆 Top 10 Most Efficient Routes")
        top10 = route_stats.nlargest(10, "Efficiency_Score")[
            ["Route", "Avg_Lead_Time", "Total_Shipments", "Efficiency_Score"]
        ]
        fig1 = px.bar(
            top10.sort_values("Avg_Lead_Time"),
            x="Avg_Lead_Time", y="Route",
            orientation="h",
            color="Efficiency_Score",
            color_continuous_scale="Greens",
            text="Avg_Lead_Time",
            labels={"Avg_Lead_Time": "Avg Lead Time (Days)", "Route": ""}
        )
        fig1.update_traces(texttemplate="%{text:.1f}d", textposition="outside")
        fig1.update_layout(height=420, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("#### 🔴 Bottom 10 Least Efficient Routes")
        bottom10 = route_stats.nsmallest(10, "Efficiency_Score")[
            ["Route", "Avg_Lead_Time", "Total_Shipments", "Efficiency_Score"]
        ]
        fig2 = px.bar(
            bottom10.sort_values("Avg_Lead_Time", ascending=False),
            x="Avg_Lead_Time", y="Route",
            orientation="h",
            color="Avg_Lead_Time",
            color_continuous_scale="Reds",
            text="Avg_Lead_Time",
            labels={"Avg_Lead_Time": "Avg Lead Time (Days)", "Route": ""}
        )
        fig2.update_traces(texttemplate="%{text:.1f}d", textposition="outside")
        fig2.update_layout(height=420, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 📋 Full Route Stats Table")
    st.dataframe(
        route_stats.sort_values("Efficiency_Score", ascending=False).reset_index(drop=True),
        use_container_width=True, height=350
    )

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Geographic Map
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("US Shipping Efficiency Heatmap by State")

    state_stats = filtered.groupby("State/Province").agg(
        Avg_Lead_Time   = ("Lead Time (Days)", "mean"),
        Total_Shipments = ("Lead Time (Days)", "count"),
        Delay_Rate      = ("Is_Delayed", "mean")
    ).reset_index().round(2)
    state_stats["Delay_Rate"] = (state_stats["Delay_Rate"] * 100).round(1)

    us_state_abbrev = {
        'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
        'Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA',
        'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA',
        'Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD',
        'Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS',
        'Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH',
        'New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC',
        'North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA',
        'Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD','Tennessee':'TN',
        'Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA',
        'West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'
    }
    state_stats["State_Code"] = state_stats["State/Province"].map(us_state_abbrev)

    fig_map = px.choropleth(
        state_stats,
        locations="State_Code",
        locationmode="USA-states",
        color="Avg_Lead_Time",
        scope="usa",
        color_continuous_scale="RdYlGn_r",
        hover_name="State/Province",
        hover_data={"Total_Shipments": True, "Delay_Rate": True, "State_Code": False},
        labels={"Avg_Lead_Time": "Avg Lead Time (Days)"},
        title="Average Shipping Lead Time by State (Red = Slow, Green = Fast)"
    )
    fig_map.update_layout(height=520)
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("#### 📍 Regional Performance Summary")
    fig_reg = px.bar(
        region_stats.sort_values("Avg_Lead_Time"),
        x="Region", y="Avg_Lead_Time",
        color="Avg_Lead_Time",
        color_continuous_scale="RdYlGn_r",
        text="Avg_Lead_Time",
        labels={"Avg_Lead_Time": "Avg Lead Time (Days)"}
    )
    fig_reg.update_traces(texttemplate="%{text:.2f}d", textposition="outside")
    fig_reg.update_layout(height=380, showlegend=False)
    st.plotly_chart(fig_reg, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Ship Mode Analysis
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Ship Mode Performance Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Average Lead Time by Ship Mode")
        order = ["Same Day", "First Class", "Second Class", "Standard Class"]
        fig_sm = px.bar(
            shipmode_stats.sort_values("Avg_Lead_Time"),
            x="Ship Mode", y="Avg_Lead_Time",
            color="Ship Mode",
            text="Avg_Lead_Time",
            category_orders={"Ship Mode": order},
            labels={"Avg_Lead_Time": "Avg Lead Time (Days)"},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_sm.update_traces(texttemplate="%{text:.2f}d", textposition="outside")
        fig_sm.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_sm, use_container_width=True)

    with col2:
        st.markdown("#### Lead Time Distribution (Box Plot)")
        fig_box = px.box(
            filtered,
            x="Ship Mode", y="Lead Time (Days)",
            color="Ship Mode",
            category_orders={"Ship Mode": order},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_box.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("#### 📦 Shipment Volume by Ship Mode")
    fig_vol = px.pie(
        shipmode_stats,
        names="Ship Mode",
        values="Total_Shipments",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4
    )
    fig_vol.update_layout(height=380)
    st.plotly_chart(fig_vol, use_container_width=True)

    st.markdown("#### 📋 Ship Mode Summary Table")
    st.dataframe(shipmode_stats, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Route Drill-Down
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Route Drill-Down — State Level")

    col1, col2 = st.columns(2)
    with col1:
        selected_factory = st.selectbox("Select Factory", sorted(df["Factory"].unique()))
    with col2:
        states_for_factory = sorted(
            df[df["Factory"] == selected_factory]["State/Province"].unique()
        )
        selected_state = st.selectbox("Select State", states_for_factory)

    route_data = filtered[
        (filtered["Factory"] == selected_factory) &
        (filtered["State/Province"] == selected_state)
    ].copy()

    if len(route_data) == 0:
        st.warning("No data for this combination with current filters. Try removing filters.")
    else:
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total Orders",    len(route_data))
        r2.metric("Avg Lead Time",   f"{route_data['Lead Time (Days)'].mean():.2f} days")
        r3.metric("Delayed Orders",  f"{route_data['Is_Delayed'].sum()}")
        r4.metric("Delay Rate",      f"{route_data['Is_Delayed'].mean()*100:.1f}%")

        st.markdown(f"#### Order Timeline — {selected_factory} → {selected_state}")
        fig_time = px.scatter(
            route_data.sort_values("Order Date"),
            x="Order Date", y="Lead Time (Days)",
            color="Ship Mode",
            size="Sales",
            hover_data=["Product Name", "Sales", "Units"],
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig_time.add_hline(
            y=threshold, line_dash="dash", line_color="red",
            annotation_text=f"Delay threshold ({threshold} days)"
        )
        fig_time.update_layout(height=420)
        st.plotly_chart(fig_time, use_container_width=True)

        st.markdown("#### 📋 Order-Level Detail")
        st.dataframe(
            route_data[[
                "Order Date", "Ship Date", "Lead Time (Days)",
                "Product Name", "Ship Mode", "Sales", "Units", "Is_Delayed"
            ]].sort_values("Order Date", ascending=False).reset_index(drop=True),
            use_container_width=True, height=350
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray; font-size:13px;'>"
    "Nassau Candy Distributor — Shipping Route Efficiency Dashboard | Built with Streamlit"
    "</p>",
    unsafe_allow_html=True
)
