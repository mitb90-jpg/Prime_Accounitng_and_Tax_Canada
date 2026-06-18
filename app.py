import streamlit as st
import pandas as pd
import io
import re
import sqlite3

# ---------------- DATABASE ----------------

conn = sqlite3.connect(
    "prime_accounting.db",
    check_same_thread=False
)

cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS clients
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT UNIQUE
)
""")



cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    account_name TEXT,
    account_type TEXT,
    FOREIGN KEY(client_id) REFERENCES clients(id)
)
""")


conn.commit()



# ---------------- DATABASE FUNCTIONS ----------------


def add_client(name):

    cursor.execute(
        """
        INSERT INTO clients(client_name)
        VALUES (?)
        """,
        (name,)
    )

    conn.commit()



def get_clients():

    cursor.execute(
        """
        SELECT client_name
        FROM clients
        ORDER BY client_name
        """
    )

    return [
        row[0]
        for row in cursor.fetchall()
    ]



def delete_client(name):

    cursor.execute(
        """
        DELETE FROM clients
        WHERE client_name = ?
        """,
        (name,)
    )

    conn.commit()



# ---------------- ACCOUNT FUNCTIONS ----------------


def add_account(
    client_name,
    account_name,
    account_type
):

    cursor.execute(
        """
        SELECT id
        FROM clients
        WHERE client_name = ?
        """,
        (client_name,)
    )


    client_id = cursor.fetchone()[0]


    cursor.execute(
        """
        INSERT INTO accounts
        (
            client_id,
            account_name,
            account_type
        )
        VALUES (?, ?, ?)
        """,
        (
            client_id,
            account_name,
            account_type
        )
    )


    conn.commit()



def get_accounts(client_name):

    cursor.execute(
        """
        SELECT 
            account_name,
            account_type

        FROM accounts

        WHERE client_id =
        (
            SELECT id
            FROM clients
            WHERE client_name = ?
        )
        """,
        (client_name,)
    )


    return cursor.fetchall()



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
    st.markdown("<p style='font-size:25px; color:gray;'>Turning Transactions Into Insights</p>", unsafe_allow_html=True)

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


# ---------------- CLIENT MANAGEMENT ----------------

st.sidebar.markdown("## 👥 Clients")


new_client = st.sidebar.text_input(
    "Add New Client"
)


if st.sidebar.button("➕ Add Client"):

    if new_client.strip():

        add_client(new_client)

        st.sidebar.success(
            "Client Added"
        )


clients = get_clients()


selected_client = st.sidebar.selectbox(
    "Select Client",
    ["Select Client"] + clients
)

# ================= WORK AREA =================

if page == "📂 Work Area":

    st.title("📂 Work Area")


    clients = get_clients()


    if not clients:

        st.warning(
            "Please add a client first"
        )

    else:

        selected_work_client = st.selectbox(
            "Select Client",
            ["Select Client"] + clients,
            key="work_client"
        )


        if selected_work_client != "Select Client":

            st.success(
                f"Active Client: {selected_work_client}"
            )


            st.divider()


            st.subheader(
                "Upload Statement"
            )


            uploaded_file = st.file_uploader(
                "Choose PDF or Excel File",
                type=["pdf", "xlsx"]
            )


            st.divider()


            st.subheader(
                "Generate"
            )


            report_type = st.radio(
                "Select Report Type",
                [
                    "Categorized Transactions Only",
                    "Category Summary Only",
                    "Profit & Loss Only",
                    "Complete Package"
                ]
            )


            st.button(
                "🚀 Generate Report",
                use_container_width=True
            )

# ---------------- APP MENU ----------------

st.sidebar.markdown("---")


page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "👥 Clients",
        "📂 Work Area",
        "📂 Statements",
        "📊 Reports"
    ]
)

# ================= CLIENT PAGE =================

if page == "👥 Clients":

    st.title("👥 Client Management")


    st.subheader("Add New Client")

    client_name = st.text_input(
        "Client Name"
    )


    if st.button("➕ Add Client"):

        if client_name.strip():

            add_client(client_name)

            st.success(
                "Client Added Successfully"
            )

            st.rerun()



    st.divider()


    st.subheader("Existing Clients")


    clients = get_clients()


    if clients:

        client_df = pd.DataFrame(
            clients,
            columns=["Client Name"]
        )

        st.dataframe(
            client_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No clients added yet"
        )


    st.divider()


    st.subheader("Delete Client")


    if clients:

        delete_client_name = st.selectbox(
            "Select Client",
            options=["Select Client"] + clients,
            index=0,
            key="delete_client_dropdown"
        )


        # DELETE CONFIRMATION

        if "confirm_delete" not in st.session_state:

            st.session_state.confirm_delete = False



        if st.button("🗑️ Delete Client"):


            if delete_client_name != "Select Client":

                st.session_state.confirm_delete = True


            else:

                st.warning(
                    "Please select a client first"
                )



        if st.session_state.confirm_delete:


            st.warning(
                f"⚠️ Are you sure you want to delete '{delete_client_name}'?"
            )


            c1, c2 = st.columns(2)


            with c1:

                if st.button("✅ Yes, Delete"):


                    delete_client(delete_client_name)


                    st.session_state.confirm_delete = False


                    st.success(
                        "Client Deleted"
                    )


                    st.rerun()



            with c2:

                if st.button("❌ Cancel"):


                    st.session_state.confirm_delete = False


                    st.rerun()



    else:

        st.info(
            "No clients available to delete"
        )

# ================= ACCOUNT PAGE =================

if page == "🏦 Accounts":

    st.title("🏦 Account Management")


    clients = get_clients()


    if not clients:

        st.info(
            "Please add a client first"
        )

    else:


        selected_client_account = st.selectbox(
            "Select Client",
            ["Select Client"] + clients,
            key="account_client_select"
        )


        if selected_client_account != "Select Client":


            st.success(
                f"Active Client: {selected_client_account}"
            )


            st.divider()


            st.subheader("Add New Account")


            account_name = st.text_input(
                "Account Name",
                placeholder="Example: Scotia Bank"
            )


            account_type = st.selectbox(
                "Account Type",
                [
                    "Bank Account",
                    "Credit Card"
                ]
            )



            if st.button(
                "➕ Add Account"
            ):


                if account_name.strip():


                    add_account(
                        selected_client_account,
                        account_name,
                        account_type
                    )


                    st.success(
                        "Account Added Successfully"
                    )


                    st.rerun()



            st.divider()


            st.subheader("Existing Accounts")


            accounts = get_accounts(
                selected_client_account
            )


            if accounts:


                account_df = pd.DataFrame(
                    accounts,
                    columns=[
                        "Account Name",
                        "Account Type"
                    ]
                )


                st.dataframe(
                    account_df,
                    use_container_width=True,
                    hide_index=True
                )


            else:

                st.info(
                    "No accounts added for this client"
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

        for page in pdf.pages:
            started = False

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
                        }


                    for w in line_words[1:]:

                        x = float(w["x0"])
                        value = w["text"]


                        # amount columns based on PDF layout

                        if x < 260:
                            current["Description"] += " " + value


                        elif x >= 260 and x < 400:
                            current["Debit"] += " " + value


                        elif x >= 400 and x < 540:
                            current["Credit"] += " " + value

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

    st.markdown("""
    <div style="
        background:#f5f9ff;
        padding:25px;
        border-radius:20px;
        text-align:center;
        border:1px solid #d6e4f0;
    ">

    <h2 style="color:#1f4e79;">
    👋 Welcome to Prime Accounting Dashboard
    </h2>

    <p style="font-size:18px;color:#555;">
    Upload a bank statement or credit card statement
    to start automated categorization and reporting
    </p>

    </div>
    """, unsafe_allow_html=True)

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
        "Credit": credit_total
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


    # ---------------- BOLD TOTAL ROW ----------------

    def bold_transaction_total(row):

        if row["Description"] == "TOTAL":
            return ["font-weight: bold"] * len(row)

        return [""] * len(row)


    styled_transactions = display_df.style.apply(
        bold_transaction_total,
        axis=1
    )


    st.dataframe(
        styled_transactions,
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


    # ---------------- TOTAL ROW ----------------

    summary_total = summary["Amount"].sum()


    total_summary_row = pd.DataFrame([{
        "Category": "TOTAL",
        "Amount": format_amount(summary_total)
    }])


    display_summary = pd.concat(
        [
            display_summary,
            total_summary_row
        ],
        ignore_index=True
    )


    st.subheader("📋 Category Summary")


    # ---------------- BOLD TOTAL ROW ----------------

    def bold_total(row):

        if row["Category"] == "TOTAL":
            return ["font-weight: bold"] * len(row)

        return [""] * len(row)


    styled_summary = display_summary.style.apply(
        bold_total,
        axis=1
    )


    st.dataframe(
        styled_summary,
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

    st.markdown(
        """
        <h1 style="color:#1f4e79;">
        📊 Prime Accounting System
        </h1>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <p style="font-size:22px;color:#555;">
        Automated accounting workflow management
        </p>
        """,
        unsafe_allow_html=True
    )


    if selected_client != "Select Client":

        st.success(
            f"Active Client: {selected_client}"
        )

    else:

        st.info(
            "Please select a client"
        )


    col1, col2, col3, col4 = st.columns(4)


    col1, col2, col3, col4 = st.columns(4)


    with col1:
        st.metric("👥 Clients", "0")

    with col2:
        st.metric("📄 Statements", "0")

    with col3:
        st.metric("💰 Revenue", "$0")

    with col4:
        st.metric("💸 Expenses", "$0")


    st.divider()


    st.subheader("Quick Actions")


    c1, c2, c3 = st.columns(3)


    with c1:
        st.button(
            "➕ Add Client",
            use_container_width=True
        )


    with c2:
        st.button(
            "📂 Upload Statement",
            use_container_width=True
        )


    with c3:
        st.button(
            "📊 Reports",
            use_container_width=True
        )


    st.divider()


    st.subheader("Recent Activity")


    empty_df = pd.DataFrame(
        columns=[
            "Client",
            "Statement",
            "Date",
            "Status"
        ]
    )


    st.dataframe(
        empty_df,
        use_container_width=True,
        hide_index=True
    )


