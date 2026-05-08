import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

from langchain_groq import ChatGroq

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="AI SQL Data Analyst", layout="wide")

st.title("🤖 AI SQL Data Analyst Agent")
st.markdown("Upload CSV → Ask Questions → Get SQL + Answer + Charts")

# ------------------- SIDEBAR -------------------
st.sidebar.header("⚙️ Settings")

groq_api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

model_option = st.sidebar.selectbox(
    "Select Model",
    ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
)

# ------------------- FILE UPLOAD -------------------
uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

if uploaded_file:

    # ------------------- LOAD DATA -------------------
    df = pd.read_csv(uploaded_file)

    st.subheader("📊 Data Preview")
    st.dataframe(df.head())

    # ------------------- SCHEMA -------------------
    st.subheader("🧠 Table Schema")
    st.write(df.dtypes)

    # ------------------- CREATE SQLITE -------------------
    conn = sqlite3.connect("data.db")
    df.to_sql("data_table", conn, if_exists="replace", index=False)

    st.success("✅ Data loaded into SQL database (table: data_table)")

    # ------------------- USER QUESTION -------------------
    question = st.text_input("💬 Ask a question about your data")

    if question and groq_api_key:

        try:
            # ------------------- LLM -------------------
            llm = ChatGroq(
                groq_api_key=groq_api_key,
                model_name=model_option
            )

            # ------------------- PROMPT -------------------
            prompt = f"""
You are a SQL expert.

Database: SQLite
Table name: data_table

Columns:
{', '.join(df.columns)}

User Question:
{question}

Instructions:
1. Generate a valid SQL query
2. Then give the final answer

STRICT FORMAT:

SQL:
<query>

Answer:
<answer>
"""

            # ------------------- LLM RESPONSE -------------------
            response = llm.invoke(prompt).content.strip()

            # ------------------- PARSE OUTPUT -------------------
            sql_query = ""
            final_answer = ""

            if "SQL:" in response and "Answer:" in response:
                sql_query = response.split("SQL:")[1].split("Answer:")[0].strip()
                final_answer = response.split("Answer:")[1].strip()
            else:
                final_answer = response

            # ------------------- DISPLAY -------------------
            st.subheader("🧠 Generated SQL Query")
            st.code(sql_query, language="sql")

            st.subheader("✅ Answer")
            st.write(final_answer)

            # ------------------- EXECUTE SQL -------------------
            try:
                if sql_query.lower().startswith("select"):
                    result_df = pd.read_sql_query(sql_query, conn)

                    st.subheader("📄 Query Result Table")
                    st.dataframe(result_df)

            except Exception as e:
                st.warning("⚠️ SQL execution failed. Try a clearer question.")

        except Exception as e:
            st.error("❌ Error: Try a more specific question using column names")

    elif question and not groq_api_key:
        st.warning("⚠️ Please enter your Groq API key")

    # ------------------- VISUALIZATION -------------------
    st.subheader("📈 Quick Visualization")

    numeric_cols = df.select_dtypes(include=['number']).columns

    if len(numeric_cols) > 0:

        col1 = st.selectbox("Select X-axis", df.columns)
        col2 = st.selectbox("Select Y-axis", numeric_cols)

        chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Scatter"])

        if st.button("Generate Chart"):

            if chart_type == "Line":
                fig = px.line(df, x=col1, y=col2)

            elif chart_type == "Bar":
                fig = px.bar(df, x=col1, y=col2)

            else:
                fig = px.scatter(df, x=col1, y=col2)

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No numeric columns available for visualization")

else:
    st.info("👆 Upload a CSV file to get started")