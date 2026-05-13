import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from langchain_groq import ChatGroq

# ------------------- PAGE CONFIG -------------------
st.set_page_config(
    page_title="AI SQL Data Analyst",
    page_icon="🤖",
    layout="wide"
)

# ------------------- CUSTOM CSS -------------------
st.markdown("""
<style>

.main {
    background-color: #0f172a;
}

h1, h2, h3, h4 {
    color: white;
}

.stApp {
    background-color: #0f172a;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-size: 16px;
    border: none;
}

.stButton>button:hover {
    background-color: #1d4ed8;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# ------------------- HERO SECTION -------------------
st.markdown("""
<h1 style='text-align:center;'>🤖 AI SQL Data Analyst Agent</h1>
<h4 style='text-align:center;color:lightgray;'>
Upload CSV → Ask Questions → Generate SQL → Visualize Data Instantly
</h4>
""", unsafe_allow_html=True)

st.markdown("---")

# ------------------- SIDEBAR -------------------
st.sidebar.header("⚙️ Settings")

groq_api_key = st.sidebar.text_input(
    "Enter Groq API Key",
    type="password"
)

model_option = st.sidebar.selectbox(
    "Select AI Model",
    [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant"
    ]
)

# ------------------- FILE UPLOAD -------------------
uploaded_file = st.file_uploader(
    "📂 Upload your CSV file",
    type=["csv"]
)

# ------------------- MAIN APP -------------------
if uploaded_file:

    # ------------------- LOAD DATA -------------------
    df = pd.read_csv(uploaded_file)

    # ------------------- PREVIEW -------------------
    st.subheader("📊 Dataset Preview")
    st.dataframe(df.head(), use_container_width=True)

    # ------------------- DATASET METRICS -------------------
    st.subheader("📌 Dataset Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Rows", df.shape[0])

    with col2:
        st.metric("Columns", df.shape[1])

    with col3:
        st.metric(
            "Numeric Columns",
            len(df.select_dtypes(include='number').columns)
        )

    with col4:
        st.metric(
            "Missing Values",
            int(df.isnull().sum().sum())
        )

    # ------------------- SCHEMA -------------------
    st.subheader("🧠 Table Schema")
    st.dataframe(df.dtypes.astype(str))

    # ------------------- SQLITE DATABASE -------------------
    conn = sqlite3.connect("data.db")

    df.to_sql(
        "data_table",
        conn,
        if_exists="replace",
        index=False
    )

    st.success("✅ Data loaded into SQL database successfully!")

    # ------------------- QUESTION INPUT -------------------
    question = st.text_area(
        "💬 Ask Questions About Your Data",
        placeholder="""
Examples:
- Total sales by country
- Average profit
- Top 5 products by sales
- Number of orders in United States
- Highest revenue category
""",
        height=120
    )

    # ------------------- AI QUERY SECTION -------------------
    if question and groq_api_key:

        try:

            # ------------------- LOAD LLM -------------------
            llm = ChatGroq(
                groq_api_key=groq_api_key,
                model_name=model_option
            )

            # ------------------- PROMPT -------------------
            prompt = f"""
You are an expert SQLite SQL query generator and data analyst.

Database Information:
- Database Type: SQLite
- Table Name: data_table

Available Columns:
{', '.join(df.columns)}

Important Rules:
1. If user asks for TOTAL/sum/revenue → use SUM()
2. If user asks for COUNT/how many/number → use COUNT(*)
3. If user asks for average → use AVG()
4. Use exact column names
5. Generate ONLY valid SQLite SQL
6. No explanations
7. Use LIMIT when needed

User Question:
{question}

STRICT FORMAT:

SQL:
<query>

Answer:
<short answer>
"""

            # ------------------- GET RESPONSE -------------------
            response = llm.invoke(prompt).content.strip()

            # ------------------- PARSE RESPONSE -------------------
            sql_query = ""
            final_answer = ""

            if "SQL:" in response and "Answer:" in response:

                sql_query = response.split("SQL:")[1].split("Answer:")[0].strip()

                final_answer = response.split("Answer:")[1].strip()

            else:
                final_answer = response

            # ------------------- DISPLAY SQL -------------------
            st.subheader("🧠 Generated SQL Query")

            st.code(sql_query, language="sql")

            # ------------------- EXECUTE SQL -------------------
            try:

                if sql_query.lower().startswith("select"):

                    result_df = pd.read_sql_query(
                        sql_query,
                        conn
                    )

                    # ------------------- RESULT TABLE -------------------
                    st.subheader("📄 Query Results")

                    st.dataframe(
                        result_df,
                        use_container_width=True
                    )

                    # ------------------- DOWNLOAD BUTTON -------------------
                    csv = result_df.to_csv(index=False).encode("utf-8")

                    st.download_button(
                        "⬇ Download Results",
                        csv,
                        "query_results.csv",
                        "text/csv"
                    )

                    # ------------------- FINAL ANSWER -------------------
                    if not result_df.empty:

                        st.subheader("✅ Final Answer")

                        st.success(str(result_df.iloc[0, 0]))

                    else:
                        st.warning("No results found.")

            except Exception as sql_error:

                st.error(f"SQL Execution Error: {sql_error}")

        except Exception as e:

            st.error(f"❌ Error: {e}")

    elif question and not groq_api_key:

        st.warning("⚠️ Please enter your Groq API key")

    # ------------------- ADVANCED VISUALIZATION -------------------
    st.subheader("📈 Advanced Data Visualization")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if len(numeric_cols) > 0:

        col1, col2 = st.columns(2)

        with col1:
            x_axis = st.selectbox(
                "Select X-axis",
                df.columns
            )

        with col2:
            y_axis = st.selectbox(
                "Select Y-axis",
                numeric_cols
            )

        chart_type = st.selectbox(
            "📊 Select Chart Type",
            [
                "Bar Chart",
                "Line Chart",
                "Scatter Plot",
                "Pie Chart",
                "Histogram",
                "Box Plot",
                "Area Chart",
                "Violin Plot"
            ]
        )

        if st.button("🚀 Generate Visualization"):

            fig = None

            if chart_type == "Bar Chart":
                fig = px.bar(df, x=x_axis, y=y_axis)

            elif chart_type == "Line Chart":
                fig = px.line(df, x=x_axis, y=y_axis)

            elif chart_type == "Scatter Plot":
                fig = px.scatter(df, x=x_axis, y=y_axis)

            elif chart_type == "Pie Chart":
                fig = px.pie(df, names=x_axis, values=y_axis)

            elif chart_type == "Histogram":
                fig = px.histogram(df, x=x_axis, y=y_axis)

            elif chart_type == "Box Plot":
                fig = px.box(df, x=x_axis, y=y_axis)

            elif chart_type == "Area Chart":
                fig = px.area(df, x=x_axis, y=y_axis)

            elif chart_type == "Violin Plot":
                fig = px.violin(df, x=x_axis, y=y_axis)

            fig.update_layout(
                template="plotly_dark",
                height=600
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:
        st.warning("No numeric columns available for charts")

    # ------------------- AUTO INSIGHTS -------------------
    st.subheader("🧠 Automatic Dataset Insights")

    try:

        numeric_df = df.select_dtypes(include='number')

        if not numeric_df.empty:

            st.write("### 📌 Statistical Summary")

            st.dataframe(
                numeric_df.describe(),
                use_container_width=True
            )

            st.write("### 🔥 Correlation Heatmap")

            corr = numeric_df.corr()

            fig_corr = px.imshow(
                corr,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Blues"
            )

            st.plotly_chart(
                fig_corr,
                use_container_width=True
            )

    except Exception as e:

        st.warning("Could not generate insights")

# ------------------- NO FILE -------------------
else:

    st.info("👆 Upload a CSV file to get started")

# ------------------- FOOTER -------------------
st.markdown("---")

st.markdown(
    """
    <center>
    <h5>🚀 Developed by Soujanya | AI SQL Data Analyst Project</h5>
    </center>
    """,
    unsafe_allow_html=True
)
