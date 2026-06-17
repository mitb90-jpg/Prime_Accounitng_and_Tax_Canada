import streamlit as st
import pandas as pd
import io
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Transaction Categorizer",
    page_icon="📊",
    layout="wide"
)

# ---------------- FORMAT FUNCTION ----------------
def format_amount(x):
    try:
        if pd.isna(x):
            return ""
        if isinstance(x, (int, float)):
            return f"{x:,.2f}"
        return x
    except:
        return x

# ---------------- CSS ----------------
st.markdown("""
<style>
div.stDownloadButton > button {
    width: 100%;
    background-color: #1f4e79;
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding: 12px;
    border-radius: 10px;
}
div.stDownloadButton > button:hover {
    background-color: #163a5c;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
col1, col2 = st.columns([1, 6])

with col1:
    st.image("Logo.jpeg", width=100)

with col2:
    st.markdown("<h1 style='color:#1f4e79;'>Prime Accounting and Tax</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:20px; color:gray;'>World Eyewear</p>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
company = st.sidebar.selectbox(
    "Select Account",
    ["Scotia Bank", "Triangle Master Card", "Visa - 6023", "Visa - 7866"]
)

uploaded_excel = st.sidebar.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

uploaded_pdf = st.sidebar.file_uploader(
    "Upload PDF File",
    type=["pdf"]
)

# ================= MAIN =================

if uploaded_excel is not None:

    df = pd.read_excel(uploaded_excel)

    # remove blank Excel columns
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]


elif uploaded_pdf is not None:

    import pdfplumber

    st.success("PDF uploaded successfully")

    transactions = []

    with pdfplumber.open(uploaded_pdf) as pdf:

        current = None
        started = False

        for page in pdf.pages:

            words = page.extract_words()

            rows = {}

            for w in words:
                y = round(float(w["top"]), 1)

                if y not in rows:
                    rows[y] = []

                rows[y].append(w)


            for y in sorted(rows):

                line_words = sorted(
                    rows[y],
                    key=lambda x: float(x["x0"])
                )

                text = " ".join(
                    w["text"] for w in line_words
                )


                header_text = text.upper()


                # start transaction table
                if (
                    "DATE" in header_text
                    and "DESCRIPTION" in header_text
                    and (
                        "DEBIT" in header_text
                        or "WITHDRAW" in header_text
                    )
                ):
                    started = True
                    continue


                if not started:
                    continue


                # ignore bottom summary
                if (
                    "NO. OF DEBITS" in header_text
                    or "NO. OF CREDITS" in header_text
                    or "TOTAL AMOUNT" in header_text
                    or "PAGE -" in header_text
                ):
                    continue


                # ignore repeated headers
                if (
                    "DATE" in header_text
                    and "DESCRIPTION" in header_text
                ):
                    continue


                first = line_words[0]["text"]


                # transaction row
                if (
                    "/" in first
                    or "-" in first
                    or "." in first
                ):

                    if current:
                        transactions.append(current)


                    current = {
                        "Date": first,
                        "Description": "",
                        "Debit": "",
                        "Credit": "",
                        "Balance": ""
                    }


                    for w in line_words[1:]:

                        x = float(w["x0"])
                        value = w["text"]


                        # amount columns based on PDF layout

                        if x < 260:
                            current["Description"] += " " + value


                        elif x >= 260 and x < 420:
                            current["Debit"] += " " + value


                        elif x >= 420 and x < 560:
                            current["Credit"] += " " + value


                        else:
                            current["Balance"] += " " + value



                else:

                    # continuation description
                    if current:

                        current["Description"] += " " + text



        if current:
            transactions.append(current)



    df = pd.DataFrame(transactions)


    df = df.apply(
        lambda x: x.str.strip()
        if x.dtype == "object"
        else x
    )


    st.write("PDF Converted Table")

    st.dataframe(
        df,
        use_container_width=True
    )


    st.write("Column check")

    st.dataframe(
        df[
            [
                "Date",
                "Description",
                "Debit",
                "Credit",
                "Balance"
            ]
        ].head(30),
        use_container_width=True
    )

# ---------------- CLEAN DATA ----------------

if uploaded_excel is not None or uploaded_pdf is not None:

    df.columns = df.columns.astype(str).str.strip()


    # PDF column normalization
    if uploaded_pdf is not None:

        df.columns = (
            df.columns
            .astype(str)
            .str.replace("\n", " ", regex=False)
            .str.strip()
        )


        for col in df.columns:

            if "Deposit" in col or "Credit" in col:
                df.rename(columns={col: "Credit"}, inplace=True)

            if "Withdraw" in col or "Debit" in col:
                df.rename(columns={col: "Debit"}, inplace=True)


    # ---------------- CLEAN AMOUNTS ----------------

    for col in ["Debit", "Credit"]:

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)


    # ---------------- RULES ----------------

    df.loc[
        df["Credit"].notna() &
        df["Description"].astype(str).str.contains(
            "MISC PAYMENT|TRANSFER FROM|DEPOSIT|DEP. FROM ANOTHER PARTY",
            case=False
        ),
        "Category"
    ] = "Revenue"


    df.loc[
        df["Credit"].notna() &
        df["Description"].astype(str).str.contains(
            "Insurance|HEALTH/DENTAL CLAIM",
            case=False
        ),
        "Category"
    ] = "Other Income"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.strip().str.lower().eq("misc payment"),
        "Category"
    ] = "Misc Expenses"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("INSURANCE", case=False),
        "Category"
    ] = "Insurance"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("LOANS", case=False),
        "Category"
    ] = "Car Loan"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("PC Bill Payment", case=False),
        "Category"
    ] = "Purchases"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("GOODLIFE FITNESS", case=False),
        "Category"
    ] = "Personal Expenses"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("HIGHWAY", case=False),
        "Category"
    ] = "Parking and Toll"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("TSCC", case=False),
        "Category"
    ] = "Vehicle Expense"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("Debit Memo", case=False),
        "Category"
    ] = "Ask from Customer"


    df.loc[
        df["Debit"].notna() &
        df["Description"].astype(str).str.contains("SERVICE CHARGE|FEE", case=False),
        "Category"
    ] = "Interest and Bank charges"


else:

    st.markdown("Your beautiful opening screen")

if uploaded_excel is not None or uploaded_pdf is not None:

    # ---------------- Sr No ----------------
    df = df.reset_index(drop=True)

    df.insert(
        0,
        "Sr. No",
        range(1, len(df) + 1)
    )

    # ---------------- DISPLAY TABLE ----------------
    display_df = df.copy()

    for col in ["Credit", "Debit"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_amount)

    st.subheader("📊 Categorized Transactions")


    # ---------------- TOTAL ROW ----------------

    debit_total = (
        pd.to_numeric(
            df["Debit"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False),
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )


    credit_total = (
        pd.to_numeric(
            df["Credit"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False),
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )


    total_row = pd.DataFrame([{
        "Sr. No": "",
        "Date": "",
        "Description": "TOTAL",
        "Debit": debit_total,
        "Credit": credit_total,
        "Balance": ""
    }])


    display_df = pd.concat(
        [
            display_df,
            total_row
        ],
        ignore_index=True
    )


    for col in ["Credit", "Debit"]:

        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_amount)


    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # ---------------- CATEGORY STATUS COUNT ----------------
    total_entries = len(df)
    categorized_entries = (
    df["Category"]
    .fillna("")
    .astype(str)
    .str.strip()
    .ne("")
    .sum()
)
    uncategorized_entries = total_entries - categorized_entries

    st.markdown("### 📌 Categorization Summary")
    st.markdown(f"""
    - ✅ **Total Transactions:** {total_entries:,}
    - 🟢 **Categorized Transactions:** {categorized_entries:,}
    - ⚪ **Uncategorized Transactions:** {uncategorized_entries:,}
    """)

    # ---------------- DOWNLOAD TRANSACTIONS ----------------
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    output.seek(0)

    st.download_button(
        "⬇️ Export Categorized Data",
        data=output,
        file_name="Auto_Categorized_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------------- PROFIT & LOSS ----------------
    st.subheader("📊 Profit & Loss Statement")

    revenue = df.loc[df["Category"] == "Revenue", "Credit"].fillna(0).sum()
    expense_df = df[df["Category"] != "Revenue"]
    expense_summary = expense_df.groupby("Category")["Debit"].sum().reset_index()

    total_expenses = expense_summary["Debit"].sum()
    net_profit = revenue - total_expenses

    pl_rows = [["Revenue", revenue], ["Less: Expenses", ""]]

    for _, r in expense_summary.iterrows():
        pl_rows.append([r["Category"], r["Debit"]])

    pl_rows += [["Total Expenses", total_expenses],
                ["Net Profit", net_profit]]

    pl_df = pd.DataFrame(pl_rows, columns=["Description", "Amount"])
    pl_df["Amount"] = pl_df["Amount"].apply(format_amount)

    st.dataframe(pl_df, use_container_width=True, hide_index=True)

    # ---------------- P&L DOWNLOAD ----------------
    pl_output = io.BytesIO()
    with pd.ExcelWriter(pl_output, engine="openpyxl") as writer:
        pl_df.to_excel(writer, index=False, sheet_name="Profit & Loss")
    pl_output.seek(0)

    st.download_button(
        "📊 Export Profit & Loss Statement",
        data=pl_output,
        file_name="Profit_and_Loss.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------------- CATEGORY SUMMARY ----------------

    df["Amount"] = (
        df["Credit"].fillna(0) +
        df["Debit"].fillna(0)
    )


    summary = (
        df.groupby("Category")["Amount"]
        .sum()
        .reset_index()
    )


    display_summary = summary.copy()


    display_summary["Amount"] = (
        display_summary["Amount"]
        .apply(format_amount)
    )


    st.subheader("📋 Category Summary")


    st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True
    )


    # ---------------- SUMMARY DOWNLOAD ----------------

    summary_output = io.BytesIO()


    with pd.ExcelWriter(summary_output, engine="openpyxl") as writer:

        summary.to_excel(
            writer,
            index=False,
            sheet_name="Category Summary"
        )


    summary_output.seek(0)


    st.download_button(
        "⬇️ Export Summary Data",
        data=summary_output,
        file_name="Category_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if uploaded_excel is not None:

    pass

else:

    st.markdown("""
    <div style="
        background: linear-gradient(135deg,#eaf3ff,#ffffff);
        padding:60px 40px;
        border-radius:30px;
        border:1px solid #cbdced;
        text-align:center;
        box-shadow:0 12px 35px rgba(0,0,0,0.10);
    ">

    <div style="
        display:inline-block;
        background:#dff3e6;
        color:#176b35;
        padding:8px 18px;
        border-radius:20px;
        font-size:15px;
        font-weight:bold;
        margin-bottom:20px;
    ">
    🟢 System Ready
    </div>


    <h1 style="
        color:#1f4e79;
        font-size:50px;
        margin-bottom:10px;
    ">
    📊 Prime Automated
    <br>
    Categorization System
    </h1>


    <h2 style="
        color:#555;
        font-weight:400;
    ">
    Prime Accounting and Tax
    </h2>


    <p style="
        font-size:22px;
        color:#333;
        margin-top:25px;
    ">
    Smart transaction processing for modern accounting workflows
    </p>


    </div>
    """, unsafe_allow_html=True)



    st.write("")


    col1, col2, col3 = st.columns(3)


    with col1:

        st.markdown("""
        <div style="
            padding:30px;
            height:180px;
            border-radius:22px;
            background:white;
            border:1px solid #d6e4f0;
            box-shadow:0 6px 18px rgba(0,0,0,0.08);
            text-align:center;
        ">

        <div style="font-size:45px;">
        📂
        </div>

        <h2 style="color:#1f4e79;">
        Upload
        </h2>

        <p>
        Bank statements<br>
        Excel or PDF
        </p>

        </div>
        """, unsafe_allow_html=True)



    with col2:

        st.markdown("""
        <div style="
            padding:30px;
            height:180px;
            border-radius:22px;
            background:white;
            border:1px solid #d6e4f0;
            box-shadow:0 6px 18px rgba(0,0,0,0.08);
            text-align:center;
        ">

        <div style="font-size:45px;">
        🤖
        </div>

        <h2 style="color:#1f4e79;">
        Automate
        </h2>

        <p>
        Smart categorization<br>
        Transaction analysis
        </p>

        </div>
        """, unsafe_allow_html=True)



    with col3:

        st.markdown("""
        <div style="
            padding:30px;
            height:180px;
            border-radius:22px;
            background:white;
            border:1px solid #d6e4f0;
            box-shadow:0 6px 18px rgba(0,0,0,0.08);
            text-align:center;
        ">

        <div style="font-size:45px;">
        📈
        </div>

        <h2 style="color:#1f4e79;">
        Reports
        </h2>

        <p>
        Summary<br>
        Profit & Loss
        </p>

        </div>
        """, unsafe_allow_html=True)



    st.write("")


    st.markdown("""
    <div style="
        background:linear-gradient(90deg,#1f4e79,#2e75b6);
        color:white;
        padding:25px;
        border-radius:20px;
        text-align:center;
        box-shadow:0 8px 20px rgba(0,0,0,0.15);
        margin-top:40px;
    ">

    <h2>
    👈 Ready when you are
    </h2>

    <p style="font-size:18px;">
    Upload your statement from the sidebar and let Prime handle the rest.
    </p>

    </div>
    """, unsafe_allow_html=True)
