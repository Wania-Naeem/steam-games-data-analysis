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
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
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