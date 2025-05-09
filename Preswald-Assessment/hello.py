import numpy as np
from preswald import Workflow, text, table, plotly, sidebar, alert, connect, get_df, query, separator, slider
import pandas as pd
import plotly.express as px

# Create a workflow instance
workflow = Workflow()

# Load Data Atom
@workflow.atom()
def load_data():
    connect()
    try:
        df = get_df('sample_csv')

        # Type corrections
        df['carbo'] = pd.to_numeric(df['carbo'], errors='coerce')
        df['sugars'] = pd.to_numeric(df['sugars'], errors='coerce')
        df['potass'] = pd.to_numeric(df['potass'], errors='coerce')
        df = df.dropna(subset=['carbo', 'sugars', 'potass'])

        # Manufacturer full names
        mfr_map = {
            'A': 'American Home Food Products',
            'G': 'General Mills',
            'K': 'Kelloggs',
            'N': 'Nabisco',
            'P': 'Post',
            'Q': 'Quaker Oats',
            'R': 'Ralston Purina'
        }
        df['manufacturer_full'] = df['mfr'].map(mfr_map)

        # Type (hot/cold) mapping
        type_map = {
            'C': 'Cold',
            'H': 'Hot'
        }
        df['type_full'] = df['type'].map(type_map)

        return df
    except Exception as e:
        alert(f"Error loading data: {str(e)}", level="error")
        return pd.DataFrame()

# Analyze Data Atom
@workflow.atom(dependencies=["load_data"])
def analyze_data(load_data):
    df = load_data.copy()

    # Clean up - remove negative or invalid values
    df = df[df['calories'] > 0]
    df = df[df['rating'] > 0]
    df.replace(-1, pd.NA, inplace=True)

    text('# An Understanding and Insightful Analysis of the Cereal Industry')

    # 1. Column Types Table
    text("## Column Types")
    try:
        if not df.empty:
            col_types = {"Column": df.columns, "Data Type": [str(dtype) for dtype in df.dtypes]}
            dtypes_df = pd.DataFrame(col_types)
            table(dtypes_df, title="Column Data Types")
        else:
            text("No data loaded, column types unavailable.")
    except Exception as e:
        alert(f"Error displaying column types: {str(e)}", level="error")
    
    separator()

    # 2. Full Dataset Preview
    text("## Cereal Analytics & Insights Data")
    table(df, title="Sample Data")

    separator()

    # 3. Summary Stats (numeric only)
    text("## Key Metrics Summary (Numerical Only)")
    stats = df.describe().transpose().round(2)
    table(stats.reset_index(), title="Numerical Summary")

    separator()

    # 4. Categorical Value Counts
    text("## Cereal Category Value Counts")
    categorical_cols = df.select_dtypes(include='object').columns
    for col in categorical_cols:
        counts_df = df[col].value_counts().reset_index()
        counts_df.columns = [col, "Count"]
        table(counts_df, title=f"Top 10 '{col}' Values")

    separator()

    # 5. Missing Values
    text('## Missing Value Counts')
    missing = df.isnull().sum()
    if missing.sum() > 0:
        missing_df = missing[missing > 0].reset_index()
        missing_df.columns = ["Column", "Missing Count"]
        table(missing_df, title="Missing Values Summary")
    else:
        text("## Missing Values Count: None")

    separator()

    # 6. Interactive Filter by Rating
    text("## 🔍 Explore Cereals by Rating Threshold")
    rating_cutoff = slider(
        label="Minimum Rating",
        min_val=0,
        max_val=100,
        step=5,
        default=40
    )

    query_text = (
        f"SELECT name, manufacturer_full, rating "
        f"FROM sample_csv "
        f"WHERE rating >= {rating_cutoff} "
        f"ORDER BY rating DESC"
    )

    top_rated_df = query(query_text, "sample_csv")

    if not top_rated_df.empty:
        table(top_rated_df, title=f"Cereals Rated {rating_cutoff}+")
        alert(f"🍽️ There are {len(top_rated_df)} cereals rated above {rating_cutoff}.", level="success")
    else:
        alert("😕 No cereals found above that rating.", level="warning")

    return df

# Visualize Data Atom
@workflow.atom(dependencies=["analyze_data"])
def visualize_data(analyze_data):
    df = analyze_data.copy()

    text("## Key Visualizations")

    fig1 = px.histogram(df, x='calories', title='Distribution of Calories')
    plotly(fig1)
    separator()

    fig2 = px.scatter(df, x='protein', y='calories', title='Protein vs. Calories')
    plotly(fig2)
    separator()

    fig3 = px.box(df, x='manufacturer_full', y='rating', title='Rating Distribution by Manufacturer')
    plotly(fig3)
    separator()

    avg_df = df.dropna().groupby('type_full')[['calories', 'protein', 'fat']].mean().reset_index()
    fig4 = px.bar(avg_df, x='type_full', y='calories', title='Average Calories by Type')
    plotly(fig4)
    separator()

    text("## Key Observations")
    alert("🧮 Most cereals have calorie values clustered between 100 and 120.", level="info")
    alert("💪 There's a modest positive correlation between protein and calories.", level="info")
    alert("🏆 Nabisco and Quaker Oats cereals tend to have higher ratings.", level="success")

# Execute the workflow
workflow.execute()