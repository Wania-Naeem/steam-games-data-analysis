import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page config ---
st.set_page_config(page_title="Steam Games Dashboard", layout="wide", page_icon="🎮")

# --- Load data ---
@st.cache_data
def load_data():
    df = pd.read_csv('steam_clean.csv')
    return df

df = load_data()

st.title("🎮 Steam Games Analytics Dashboard")
st.markdown("Explore pricing, ratings, genres, and player engagement across 27,000+ Steam games.")

# --- Sidebar filters ---
st.sidebar.header("Filters")

genres = sorted(df['primary_genre'].dropna().unique().tolist())
selected_genres = st.sidebar.multiselect("Genre", genres, default=[])

price_range = st.sidebar.slider(
    "Price Range ($)",
    float(df['price'].min()), float(df['price'].max()),
    (0.0, 60.0)
)

year_min, year_max = int(df['release_year'].min()), int(df['release_year'].max())
year_range = st.sidebar.slider("Release Year", year_min, year_max, (year_min, year_max))

free_only = st.sidebar.checkbox("Free games only", value=False)

# --- Apply filters ---
filtered = df.copy()
if selected_genres:
    filtered = filtered[filtered['primary_genre'].isin(selected_genres)]
filtered = filtered[
    (filtered['price'] >= price_range[0]) & (filtered['price'] <= price_range[1]) &
    (filtered['release_year'] >= year_range[0]) & (filtered['release_year'] <= year_range[1])
]
if free_only:
    filtered = filtered[filtered['is_free'] == True]

st.sidebar.markdown(f"**{len(filtered):,} games** match your filters")

# --- KPI row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Games", f"{len(filtered):,}")
col2.metric("Free Games", f"{(filtered['is_free'].sum() / len(filtered) * 100):.1f}%" if len(filtered) else "N/A")
reliable = filtered[filtered['total_ratings'] >= 50]
col3.metric("Avg Satisfaction", f"{reliable['satisfaction_pct'].mean():.1f}%" if len(reliable) else "N/A")
col4.metric("Avg Price", f"${filtered['price'].mean():.2f}" if len(filtered) else "N/A")

st.divider()

# --- Row 1: Genre count + Games per year ---
c1, c2 = st.columns(2)

with c1:
    genre_counts = filtered['primary_genre'].value_counts().head(10)
    fig = px.bar(
        x=genre_counts.values, y=genre_counts.index, orientation='h',
        labels={'x': 'Number of Games', 'y': 'Genre'},
        title="Top 10 Genres by Game Count", color=genre_counts.values,
        color_continuous_scale='viridis'
    )
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        yaxis={"categoryorder": "array", "categoryarray": genre_counts.index[::-1]},
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    games_per_year = filtered['release_year'].value_counts().sort_index()
    fig = px.line(
        x=games_per_year.index, y=games_per_year.values,
        labels={'x': 'Year', 'y': 'Games Released'},
        title="Games Released Per Year", markers=True
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Row 2: Price vs Satisfaction + Playtime by genre ---
c3, c4 = st.columns(2)

with c3:
    sample = filtered[filtered['total_ratings'] >= 20].sample(min(2000, len(filtered[filtered['total_ratings'] >= 20]))) if len(filtered) else filtered
    fig = px.scatter(
        sample, x='price', y='satisfaction_pct', color='primary_genre',
        hover_data=['name'], title="Price vs Satisfaction",
        labels={'price': 'Price ($)', 'satisfaction_pct': 'Satisfaction %'}
    )
    st.plotly_chart(fig, use_container_width=True)

with c4:
    genre_playtime = filtered.groupby('primary_genre').filter(lambda x: len(x) >= 10)
    if len(genre_playtime) > 0:
        top_playtime = genre_playtime.groupby('primary_genre')['average_playtime'].mean().sort_values(ascending=False).head(10)
        fig = px.bar(
            x=top_playtime.values, y=top_playtime.index, orientation='h',
            labels={'x': 'Avg Playtime (minutes)', 'y': 'Genre'},
            title="Top 10 Genres by Average Playtime", color=top_playtime.values,
            color_continuous_scale='teal'
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough games in the current filter (each genre needs at least 10 games) to show this chart. Try selecting fewer/broader filters.")

st.divider()

# --- Additional analysis (ported from the notebook) ---
st.subheader("📊 Deeper Analysis")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["💰 Pricing", "🎯 Genres", "🏢 Developers & Publishers", "📈 Trends Over Time", "🖥️ Platforms & Language"]
)

with tab1:
    p1, p2 = st.columns(2)
    with p1:
        free_paid = filtered['is_free'].value_counts()
        fig = px.pie(
            names=['Free' if v else 'Paid' for v in free_paid.index],
            values=free_paid.values,
            title="Proportion of Free vs. Paid Games",
            color_discrete_sequence=['#66b3ff', '#ff9999']
        )
        st.plotly_chart(fig, use_container_width=True)
    with p2:
        cat_order = ['Free', 'Budget', 'Mid-range', 'Premium', 'AAA']
        cat_counts = filtered['price_category'].value_counts().reindex(cat_order).fillna(0)
        fig = px.bar(
            x=cat_counts.index, y=cat_counts.values,
            labels={'x': 'Price Category', 'y': 'Number of Games'},
            title="Count of Games by Price Category", color=cat_counts.index,
            category_orders={'x': cat_order}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    p3, p4 = st.columns(2)
    with p3:
        fig = px.box(
            filtered, x='price_category', y='satisfaction_pct',
            category_orders={'price_category': cat_order},
            title="Satisfaction % by Price Category", points=False
        )
        st.plotly_chart(fig, use_container_width=True)
    with p4:
        fig = px.scatter(
            filtered, x='price', y='owners_midpoint', log_y=True,
            opacity=0.5, title="Price vs. Estimated Owners (Log Scale)",
            labels={'price': 'Price ($)', 'owners_midpoint': 'Estimated Owners'}
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    g1, g2 = st.columns(2)
    valid_genres = filtered['primary_genre'].value_counts()
    valid_genres = valid_genres[valid_genres >= 20].index
    genre_df = filtered[filtered['primary_genre'].isin(valid_genres)]
    with g1:
        if len(genre_df):
            avg_sat_genre = genre_df.groupby('primary_genre')['satisfaction_pct'].mean().nlargest(10)
            fig = px.bar(
                x=avg_sat_genre.index, y=avg_sat_genre.values,
                labels={'x': 'Genre', 'y': 'Avg Satisfaction %'},
                title="Top 10 Genres by Avg Satisfaction (≥20 games)", color=avg_sat_genre.values,
                color_continuous_scale='reds'
            )
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough games in the current filter to show this chart.")
    with g2:
        fig = px.histogram(
            filtered[filtered['total_ratings'] >= 50], x='satisfaction_pct', nbins=30,
            title="Distribution of Satisfaction % (games with ≥50 ratings)",
            labels={'satisfaction_pct': 'Satisfaction %'}
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    d1, d2 = st.columns(2)
    with d1:
        dev_counts = filtered['developer'].value_counts().head(15)
        fig = px.bar(
            x=dev_counts.index, y=dev_counts.values,
            labels={'x': 'Developer', 'y': 'Number of Games'},
            title="Top 15 Most Prolific Developers", color=dev_counts.values,
            color_continuous_scale='viridis'
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_tickangle=-60)
        st.plotly_chart(fig, use_container_width=True)
    with d2:
        pub_reach = filtered.groupby('publisher')['owners_midpoint'].sum().nlargest(10)
        fig = px.bar(
            x=pub_reach.index, y=pub_reach.values,
            labels={'x': 'Publisher', 'y': 'Total Estimated Owners'},
            title="Top 10 Publishers by Total Reach", color=pub_reach.values,
            color_continuous_scale='magma'
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_tickangle=-60)
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    trend_df = filtered[filtered['release_year'] <= 2018]
    t1, t2 = st.columns(2)
    with t1:
        avg_price_yr = trend_df.groupby('release_year')['price'].mean()
        fig = px.line(
            x=avg_price_yr.index, y=avg_price_yr.values, markers=True,
            labels={'x': 'Release Year', 'y': 'Avg Price ($)'},
            title="Average Price of Games Per Year (up to 2018)"
        )
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        top_5_genres = filtered['primary_genre'].value_counts().nlargest(5).index
        gt = trend_df[trend_df['primary_genre'].isin(top_5_genres)]
        yearly = gt.groupby(['release_year', 'primary_genre']).size().unstack(fill_value=0)
        if len(yearly):
            proportions = yearly.divide(yearly.sum(axis=1), axis=0).reset_index()
            fig = px.area(
                proportions, x='release_year', y=[c for c in proportions.columns if c != 'release_year'],
                title="Share of Top 5 Genres Over Release Years",
                labels={'release_year': 'Release Year', 'value': 'Proportion', 'variable': 'Genre'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough games in the current filter to show this chart.")

with tab5:
    pl1, pl2, pl3 = st.columns(3)
    with pl1:
        plat_counts = filtered['platform_count'].value_counts().sort_index()
        fig = px.bar(
            x=plat_counts.index.astype(str), y=plat_counts.values,
            labels={'x': 'Platforms Supported', 'y': 'Number of Games'},
            title="Games by Platform Count"
        )
        st.plotly_chart(fig, use_container_width=True)
    with pl2:
        avg_owners_plat = filtered.groupby('multi_platform')['owners_midpoint'].mean().reset_index()
        fig = px.bar(
            avg_owners_plat, x='multi_platform', y='owners_midpoint',
            labels={'multi_platform': 'Platform Type', 'owners_midpoint': 'Avg Estimated Owners'},
            title="Avg Owners: Single vs Multi-Platform"
        )
        st.plotly_chart(fig, use_container_width=True)
    with pl3:
        avg_sat_lang = filtered.groupby('english')['satisfaction_pct'].mean().reset_index()
        avg_sat_lang['english'] = avg_sat_lang['english'].map({0: 'Non-English', 1: 'English'})
        fig = px.bar(
            avg_sat_lang, x='english', y='satisfaction_pct',
            labels={'english': 'Language Support', 'satisfaction_pct': 'Avg Satisfaction %'},
            title="Avg Satisfaction: English vs Non-English"
        )
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Hidden Gems Table ---
st.subheader("💎 Hidden Gems")
st.caption("High satisfaction, moderate review count, smaller player base — great games you may have missed.")

median_owners = df['owners_midpoint'].median()
hidden_gems = filtered[
    (filtered['satisfaction_pct'] >= 90) &
    (filtered['total_ratings'] >= 100) &
    (filtered['total_ratings'] <= 2000) &
    (filtered['owners_midpoint'] <= median_owners)
].sort_values('satisfaction_pct', ascending=False)

st.dataframe(
    hidden_gems[['name', 'primary_genre', 'satisfaction_pct', 'total_ratings', 'price']].head(20),
    use_container_width=True,
    hide_index=True
)

# --- Top games table ---
st.subheader("🏆 Top Rated Games (in current filter)")
top_rated = filtered[filtered['total_ratings'] >= 1000].sort_values('satisfaction_pct', ascending=False)
st.dataframe(
    top_rated[['name', 'primary_genre', 'satisfaction_pct', 'total_ratings', 'price']].head(15),
    use_container_width=True,
    hide_index=True
)
