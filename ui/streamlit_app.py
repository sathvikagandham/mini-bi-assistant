"""
Streamlit frontend for the Mini AI BI Assistant.

Talks to the FastAPI backend over HTTP.
Run the backend first:
    uvicorn app.main:app --reload

Then run this UI:
    streamlit run ui/streamlit_app.py
"""
import requests
import streamlit as st
import pandas as pd

API_URL = "http://127.0.0.1:8000"
TIMEOUT = 20


st.set_page_config(page_title="Mini AI BI Assistant", page_icon="📊", layout="wide")

st.title("📊 Mini AI BI Assistant")
st.caption("Ask natural-language questions about the sales data.")

# --- Sidebar ---
with st.sidebar:
    st.header("Status")
    try:
        health = requests.get(f"{API_URL}/health", timeout=3, proxies={"http": None, "https": None}).json()
        st.success(f"✅ API online — {health['rows_in_db']} rows in DB")
    except Exception as e:
        st.error(f"❌ API offline")
        st.caption(f"Start the backend with: `uvicorn app.main:app --reload`")
        st.caption(f"Error: {e}")
        st.stop()

    st.divider()
    st.markdown("**Example questions**")
    examples = [
        "What is the total revenue?",
        "Which product generated the highest revenue?",
        "What is the monthly revenue trend?",
        "Which region generated the highest sales?",
        "How did revenue change between January and June?",
        "Which was better, February or April?",
    ]
    for q in examples:
        if st.button(q, use_container_width=True, key=f"ex_{q}"):
            st.session_state["question"] = q

# --- Main ---
question = st.text_input(
    "Your question",
    value=st.session_state.get("question", ""),
    placeholder="e.g. What is the total revenue?",
)

if st.button("Ask", type="primary"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question},
                    timeout=TIMEOUT,
                    proxies={"http": None, "https": None},
                )
                
                    
                
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach the API. Is uvicorn running?")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("The API took too long to respond.")
                st.stop()

        if resp.status_code == 200:
            payload = resp.json()
            st.markdown("### Answer")
            st.success(payload["answer"])
            st.caption(f"Classified as: `{payload['intent']}`")

            if payload.get("supporting_table"):
                st.markdown("### Supporting data")
                df = pd.DataFrame(payload["supporting_table"])
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Bar chart for ranking intents
                if payload["intent"] in ("top_product", "top_region", "monthly_trend"):
                    label_col = df.columns[0]
                    chart_df = df.set_index(label_col)[["total_revenue"]]
                    st.bar_chart(chart_df)
        else:
            detail = resp.json().get("detail", resp.text)
            st.warning(f"⚠️ {detail}")