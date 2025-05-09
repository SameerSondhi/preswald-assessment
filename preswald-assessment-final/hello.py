import pandas as pd
import plotly.express as px
import preswald

# Create a workflow instance
workflow = preswald.Workflow()


# Load Data Atom
@workflow.atom()
def load_data():
    preswald.connect()
    df = preswald.get_df("sample_csv")

    # Coerce all relevant columns to numeric
    numeric_cols = [
        "calories", "protein", "fat", "sodium", "fiber",
        "carbo", "sugars", "potass", "vitamins", "shelf",
        "weight", "cups", "rating"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # Drop rows with any missing critical numeric fields
    df = df.dropna(subset=numeric_cols)

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
    df["manufacturer_full"] = df["mfr"].map(mfr_map)

    # Type (hot/cold) mapping
    type_map = {
        'C': 'Cold',
        'H': 'Hot'
    }
    df["type_full"] = df["type"].map(type_map)

    return df


# Analyze Data Atom
@workflow.atom(dependencies=["load_data"])
def analyze_data(load_data):
    df = load_data.copy()

    # Remove non‑positive calories and ratings
    df = df[(df["calories"] > 0) & (df["rating"] > 0)]
    df.replace(-1, pd.NA, inplace=True)

    preswald.sidebar(defaultopen=True, logo='images/cereal_logo.png')

    # 0. Analysis Title
    preswald.text('# The Cereal Industry: An Interactive Overview With Analytics & Insights')

    # Introductory stats
    preswald.text("## Getting Started: Looking at Cereal a Different Way")

    # 1. Total cereals
    total_df = preswald.query("""
        SELECT COUNT(*) AS total_cereals
        FROM sample_csv
    """, "sample_csv")
    if total_df is not None and not total_df.empty:
        total = total_df["total_cereals"].iloc[0]
        preswald.alert(f"We chose to look at {total} cereals out there and found a robust dataset to help us out.", level='info')

    # 2. Average calories (cast to DOUBLE)
    avg_cal_df = preswald.query("""
        SELECT ROUND(AVG(CAST(calories AS DOUBLE)), 2) AS avg_calories
        FROM sample_csv
    """, "sample_csv")
    if avg_cal_df is not None and not avg_cal_df.empty:
        avg_cal = avg_cal_df["avg_calories"].iloc[0]
        preswald.alert(f"Thought that cereal is a high calorie treat? Actually the average calories per modest serving are actually more like {avg_cal} calories!")

    # 3. Top 3 highest‑sugar cereals (cast sugars too)
    sugar_df = preswald.query("""
        SELECT name,
               CAST(sugars AS DOUBLE) AS sugars
        FROM sample_csv
        ORDER BY sugars DESC
        LIMIT 3
    """, "sample_csv")
    if sugar_df is not None and not sugar_df.empty:
        top3 = sugar_df["name"].tolist()
        names_str = ", ".join(top3)
        preswald.alert(f"Cereals can pack a sugary punch though! Here's a little insider info on the 3 most sugary cereals to watch out for: {names_str}", level='warning')

    preswald.separator()

    # 1. Column Types Table
    preswald.text("## Understanding the Data: Column Types")
    if not df.empty:
        dtype_df = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str)
        })
        preswald.table(dtype_df, title="Column Data Types")
    else:
        preswald.text("No data loaded, column types unavailable.")
    preswald.separator()

    # 2. First 10 Rows
    preswald.text("## Cereal Analytics & Insights: The Dataset")
    preswald.table(df, title="Sample Data")
    preswald.separator()

    # 3. Summary Stats (numeric only)
    preswald.text("## Key Metrics Summary (Numerical Only)")
    stats = df.describe().transpose().round(2).reset_index()
    preswald.table(stats, title="Numerical Summary")
    preswald.separator()

    # 4. Categorical Value Counts (Top 10 per column)
    preswald.text("## The Cereal Dichotomy: Hot vs. Cold Value Counts")
    categorical_cols = df.select_dtypes(include="object").columns
    for col in categorical_cols:
        counts = df[col].value_counts().reset_index()
        counts.columns = [col, "Count"]
        preswald.table(counts.head(10), title=f"Top 10 '{col}' Values")
    preswald.separator()

    # 5. Missing Values
    preswald.text("## Full Transparency: Missing Value Counts")
    missing = df.isna().sum()
    if missing.sum() > 0:
        missing_df = missing[missing > 0].reset_index()
        missing_df.columns = ["Column", "Missing Count"]
        preswald.table(missing_df, title="Missing Values Summary")
    else:
        preswald.text("No missing values detected.")

    preswald.separator()

    # 6. Interactive Filter by Rating
    preswald.text("## An Interactive Insight: Explore Cereals by Rating Threshold")
    rating_cutoff = preswald.slider(
        label="Minimum Rating",
        min_val=0,
        max_val=100,
        step=5,
        default=85
    )

    # Query and filter the DataFrame based on slider
    filtered = df[df["rating"] >= rating_cutoff][["name", "manufacturer_full", "rating"]]

    # Display results
    if len(filtered) == 1:
        preswald.alert(f"🥣 There is {len(filtered)} cereal rated above {rating_cutoff}.", level="success")
    else:
        preswald.alert(f"🥣 There are {len(filtered)} cereals rated above {rating_cutoff}.", level="success")
    preswald.table(filtered, title=f"Cereals Rated {rating_cutoff}+")

    preswald.separator()

    return df


# Visualize Data Atom
@workflow.atom(dependencies=["analyze_data"])
def visualize_data(analyze_data):
    df = analyze_data.copy()

    preswald.text("# The Big Picture: Visualizing the Data")

    # 1. Calories Distribution
    fig1 = px.histogram(df, x="calories", title="Distribution of Calories")
    preswald.plotly(fig1)
    preswald.separator()

    # 2. Protein vs. Calories
    fig2 = px.scatter(df, x="protein", y="calories", title="Protein vs. Calories")
    preswald.plotly(fig2)
    preswald.separator()

    # 3. Ratings by Manufacturer
    fig3 = px.box(
        df,
        x="manufacturer_full",
        y="rating",
        title="Rating Distribution by Manufacturer"
    )
    preswald.plotly(fig3)
    preswald.separator()

    # 4. Average Calories by Type
    avg_df = (
        df
        .groupby("type_full")[["calories", "protein", "fat"]]
        .mean()
        .round(2)
        .reset_index()
    )
    fig4 = px.bar(avg_df, x="type_full", y="calories", title="Average Calories by Type")
    preswald.plotly(fig4)
    preswald.separator()

    # Key Observations
    preswald.text("## Key Observations: What We Know Based on the Data ")
    preswald.alert(
        "🧮 Most cereals have calorie values clustered between 100 and 120 — a common threshold for 'low-calorie' labeling."
    , level='info')
    preswald.alert(
        "💪 A modest positive correlation exists between protein content and calorie count — higher protein usually means more calories."
    ,level='info')
    preswald.alert(
        "🏆 Cereals from Nabisco and Quaker Oats tend to score higher in consumer ratings than others."
    ,level='success')


# Execute the workflow
workflow.execute()