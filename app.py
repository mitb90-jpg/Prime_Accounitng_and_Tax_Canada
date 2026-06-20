import streamlit as st
import pandas as pd
import io
import re
import json
import os
import datetime

from supabase import create_client, Client


# ReportLab PDF
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# ---------------- DATABASE ----------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ---------------- DATABASE FUNCTIONS ----------------

def add_client(name, address, contact_number):

    response = supabase.table("clients").insert(
        {
            "client_name": name,
            "address": address,
            "contact_number": contact_number
        }
    ).execute()

    return response.data[0]["id"]



def update_client(old_name, new_name, address, contact_number):

    supabase.table("clients") \
        .update(
            {
                "client_name": new_name,
                "address": address,
                "contact_number": contact_number
            }
        ) \
        .eq("client_name", old_name) \
        .execute()



def get_clients():

    response = (
        supabase
        .table("clients")
        .select("client_name")
        .order("client_name")
        .execute()
    )

    return [
        row["client_name"]
        for row in response.data
    ]


def get_client_details(client_name):

    response = (
        supabase
        .table("clients")
        .select("*")
        .eq("client_name", client_name)
        .execute()
    )

    return response.data[0] if response.data else None


# ---------------- INVOICE FUNCTIONS ----------------

import datetime


def generate_invoice_number():

    today = datetime.date.today()

    prefix = f"INV-{today.strftime('%Y%m%d')}"

    response = (
        supabase
        .table("invoices")
        .select("invoice_number")
        .like(
            "invoice_number",
            f"{prefix}%"
        )
        .execute()
    )

    count = len(response.data) + 1

    return f"{prefix}-{count:04d}"


def add_invoice(
    invoice_number,
    client_name,
    invoice_date,
    due_date,
    description,
    quantity,
    rate,
    amount,
    tax,
    total,
    payment_status,
    received_date
):

    existing = (
        supabase
        .table("invoices")
        .select("invoice_number")
        .eq(
            "invoice_number",
            invoice_number
        )
        .execute()
    )

    if existing.data:
        return

    supabase.table("invoices").insert(
        {
            "invoice_number": invoice_number,
            "client_name": client_name,
            "invoice_date": str(invoice_date),
            "due_date": str(due_date),
            "description": description,
            "quantity": quantity,
            "rate": rate,
            "amount": amount,
            "tax": tax,
            "total": total,
            "payment_status": payment_status,
            "received_date":
                str(received_date)
                if received_date
                else None
        }
    ).execute()


def add_invoice_items(invoice_number, items):

    for item in items:

        supabase.table("invoice_items").insert(
            {
                "invoice_number": invoice_number,
                "description": item["Description"],
                "quantity": item["Quantity"],
                "rate": item["Rate"],
                "amount": item["Amount"]
            }
        ).execute()
def generate_invoice_pdf(invoice_number):

    invoice = (
        supabase
        .table("invoices")
        .select("*")
        .eq("invoice_number", invoice_number)
        .execute()
    ).data[0]

    items = (
        supabase
        .table("invoice_items")
        .select("*")
        .eq("invoice_number", invoice_number)
        .execute()
    ).data

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, title="Prime Accounting Invoice")
    styles = getSampleStyleSheet()
    content = []

    logo = Image("Logo.jpeg", width=80, height=80)

    header_data = [[
        Paragraph(
            "<b><font size=20 color='white'>Prime Accounting & Tax</font></b>"
            "<br/>"
            "<font size=11 color='white'>Toronto, Ontario</font>",
            styles["Normal"]
        ),
        logo
    ]]

    header_table = Table(header_data, colWidths=[350, 100])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1f4e79")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    content.append(header_table)
    content.append(Spacer(1, 20))

    invoice_info = [
        ["Invoice Sent To", invoice["client_name"]],
        ["Invoice Number", invoice["invoice_number"]],
        ["Invoice Date", invoice["invoice_date"]],
        ["Due Date", invoice["due_date"]],
        ["Payment Status", invoice["payment_status"]],
    ]

    invoice_table = Table(invoice_info, colWidths=[150, 280])
    invoice_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)
    ]))

    content.append(invoice_table)
    content.append(Spacer(1, 20))

    item_data = [["Description", "Qty", "Rate", "Amount"]]

    for item in items:
        item_data.append([
            item["description"],
            str(item["quantity"]),
            f"${item['rate']:,.2f}",
            f"${item['amount']:,.2f}"
        ])

    item_table = Table(item_data, colWidths=[220, 60, 80, 80])
    item_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f7189")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ]))

    content.append(item_table)
    content.append(Spacer(1, 20))

    total_table = Table([
        ["Tax", f"${invoice['tax']:,.2f}"],
        ["TOTAL", f"${invoice['total']:,.2f}"]
    ], colWidths=[300, 120])

    total_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)
    ]))

    content.append(total_table)
    content.append(Spacer(1, 30))
    content.append(Paragraph("Thank you for your business.", styles["Normal"]))

    doc.build(content)
    buffer.seek(0)

    return buffer

def get_invoices():

    response = (
        supabase
        .table("invoices")
        .select("*")
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    return response.data


def delete_client(name):

    supabase.table("clients") \
        .delete() \
        .eq(
            "client_name",
            name
        ) \
        .execute()


def delete_invoice(invoice_number):

    supabase.table("invoices") \
        .delete() \
        .eq(
            "invoice_number",
            invoice_number
        ) \
        .execute()



# ---------------- ACCOUNT FUNCTIONS ----------------


def add_account(
    client_id,
    client_name,
    account_name,
    account_type
):

    supabase.table("accounts").insert(
        {
            "client_id": client_id,
            "client_name": client_name,
            "account_name": account_name,
            "account_type": account_type
        }
    ).execute()



def get_accounts(client_id):

    response = (
        supabase
        .table("accounts")
        .select(
            "account_name, account_type"
        )
        .eq(
            "client_id",
            client_id
        )
        .execute()
    )


    return [
        (
            row["account_name"],
            row["account_type"]
        )
        for row in response.data
    ]



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
div.stButton > button {
    width: 100%;
    background-color: #1f4e79;
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding: 12px;
    border-radius: 10px;
}
div.stButton > button:hover {
    background-color: #163a5c;
}
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}
section[data-testid="stSidebar"] * {
    color: #333333;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 16px;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 4px;
    display: block;
}
section[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
    background-color: #eaf1fb;
}
section[data-testid="stSidebar"] .stRadio label[data-checked="true"] p {
    color: #1f4e79 !important;
    font-weight: bold;
}
section[data-testid="stSidebar"] div.stButton > button {
    color: white !important;
    font-weight: bold;
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


st.sidebar.image("Logo.jpeg", width=70)

st.sidebar.markdown(
    "<h2 style='color:#1f4e79; margin-top:0px;'>Prime Accounting & Tax</h2>",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")


# ---------------- APP MENU ----------------
st.sidebar.markdown("---")
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

nav_items = [
    "🏠 Dashboard",
    "👥 Clients",
    "🧾 Sales",
    "📄 Invoice History",
    "📊 Reports"
]

for item in nav_items:
    if st.sidebar.button(item, key=f"nav_{item}", use_container_width=True):
        st.session_state.page = item

page = st.session_state.page

st.sidebar.markdown("---")

total_clients = len(get_clients())

all_invoices = get_invoices()

unpaid_count = len([
    inv for inv in all_invoices
    if inv["payment_status"] == "Unpaid"
])

st.sidebar.markdown(
    f"""
    <div style="font-size:14px; line-height:1.8;">
    👥 <b>Total Clients:</b> {total_clients}<br>
    📌 <b>Unpaid Invoices:</b> {unpaid_count}
    </div>
    """,
    unsafe_allow_html=True
)

# ================= CLIENT PAGE =================

if page == "👥 Clients":

    st.title("👥 Client Management")

    tab1, tab2, tab3 = st.tabs(
        ["📋 All Clients", "➕ Add Client", "👤 Client Profile"]
    )


    with tab2:

        st.subheader("Add New Client")

        client_name = st.text_input(
            "Client Name"
        )

        client_address = st.text_input(
            "Address"
        )

        client_contact = st.text_input(
            "Contact Number"
        )

        st.markdown("**Account Details (optional)**")

        new_account_name = st.text_input(
            "Account Name",
            placeholder="Example: Scotia Bank",
            key="new_client_account_name"
        )

        new_account_type = st.selectbox(
            "Account Type",
            ["Bank Account", "Credit Card"],
            key="new_client_account_type"
        )


        if st.button("➕ Add Client"):

            if client_name.strip():

                new_client_id = add_client(client_name, client_address, client_contact)

                if new_account_name.strip():

                    add_account(new_client_id, client_name, new_account_name, new_account_type)

                st.success(
                    "Client Added Successfully"
                )

                st.rerun()



    st.divider()


    with tab1:

        st.subheader("Existing Clients")

        clients = get_clients()

        if clients:

            all_clients_data = (
                supabase
                .table("clients")
                .select("*")
                .order("client_name")
                .execute()
            ).data

            client_df = pd.DataFrame(all_clients_data)

            client_df = client_df.drop(columns=["id"])

            client_df.insert(0, "Sr. No", range(1, len(client_df) + 1))

            st.dataframe(
                client_df,
                use_container_width=True,
                hide_index=True
            )

            client_excel = io.BytesIO()

            with pd.ExcelWriter(client_excel, engine="openpyxl") as writer:
                client_df.to_excel(writer, index=False, sheet_name="Clients")

            client_excel.seek(0)

            st.download_button(
                "⬇️ Export Clients Database",
                data=client_excel,
                file_name="Clients_Database.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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

            if "confirm_delete" not in st.session_state:
                st.session_state.confirm_delete = False

            if st.button("🗑️ Delete Client"):

                if delete_client_name != "Select Client":
                    st.session_state.confirm_delete = True
                else:
                    st.warning("Please select a client first")

            if st.session_state.confirm_delete:

                st.warning(
                    f"⚠️ Are you sure you want to delete '{delete_client_name}'?"
                )

                c1, c2 = st.columns(2)

                with c1:
                    if st.button("✅ Yes, Delete"):
                        delete_client(delete_client_name)
                        st.session_state.confirm_delete = False
                        st.success("Client Deleted")
                        st.rerun()

                with c2:
                    if st.button("❌ Cancel"):
                        st.session_state.confirm_delete = False
                        st.rerun()

        else:

            st.info(
                "No clients available to delete"
            )

    with tab3:

        st.subheader("👤 Client Profile")

        if clients:

            profile_client = st.selectbox(
                "Select Client to View Profile",
                ["Select Client"] + clients,
                key="profile_client_select"
            )

            if profile_client != "Select Client":

                details = get_client_details(profile_client)

                st.write(f"**Name:** {details['client_name']}")
                st.write(f"**Address:** {details.get('address', '')}")
                st.write(f"**Contact Number:** {details.get('contact_number', '')}")

                with st.expander("✏️ Edit Client Details"):

                    edit_name = st.text_input(
                        "Client Name",
                        value=details['client_name'],
                        key=f"edit_client_name_{details['id']}"
                    )

                    edit_address = st.text_input(
                        "Address",
                        value=details.get('address', ''),
                        key=f"edit_client_address_{details['id']}"
                    )

                    edit_contact = st.text_input(
                        "Contact Number",
                        value=details.get('contact_number', ''),
                        key=f"edit_client_contact_{details['id']}"
                    )

                    if st.button("💾 Save Changes", key="save_client_edit"):

                        update_client(
                            profile_client,
                            edit_name,
                            edit_address,
                            edit_contact
                        )

                        st.success("Client Updated Successfully")

                        st.rerun()

                st.divider()

                st.subheader("🏦 Accounts")

                account_name = st.text_input(
                    "Account Name",
                    placeholder="Example: Scotia Bank",
                    key="profile_account_name"
                )

                account_type = st.selectbox(
                    "Account Type",
                    ["Bank Account", "Credit Card"],
                    key="profile_account_type"
                )

                if st.button("➕ Add Account", key="profile_add_account"):

                    if account_name.strip():
                        add_account(details["id"], profile_client, account_name, account_type)
                        st.success("Account Added Successfully")
                        st.rerun()

                accounts = get_accounts(details["id"])

                if accounts:

                    account_df = pd.DataFrame(
                        accounts,
                        columns=["Account Name", "Account Type"]
                    )

                    st.dataframe(
                        account_df,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info("No accounts added for this client")


# ================= SALES PAGE =================

if page == "🧾 Sales":

    st.title("🧾 Sales & Invoice Management")


    # -------- MULTIPLE INVOICE ITEMS --------

    if "invoice_items" not in st.session_state:

        st.session_state.invoice_items = []


    st.subheader("Invoice Items")


    col1, col2, col3 = st.columns(3)


    with col1:

        item_description = st.text_input(
            "Description",
            key="item_description"
        )


    with col2:

        quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=1,
            key="invoice_quantity"
        )


    with col3:

        rate = st.number_input(
            "Rate",
            min_value=0.0,
            key="invoice_rate"
        )


    item_total = quantity * rate


    st.info(
        f"Item Total: ${item_total:,.2f}"
    )


    if st.button(
        "➕ Add Item",
        key="add_invoice_item"
    ):

        if item_description.strip():

            st.session_state.invoice_items.append(
                {
                    "Description": item_description,
                    "Quantity": quantity,
                    "Rate": rate,
                    "Amount": item_total
                }
            )

            st.rerun()


        else:

            st.warning(
                "Please enter description"
            )


    # ---------- INVOICE BASIC DETAILS ----------

    col1, col2 = st.columns(2)


    with col1:

        customer_name = st.selectbox(
            "Customer",
            ["Select Client"] + get_clients()
        )


    with col2:

        invoice_date = st.date_input(
            "Invoice Date",
            format="DD-MM-YYYY"
        )


    col3, col4 = st.columns(2)


    with col3:

        if "current_invoice_number" not in st.session_state:

            st.session_state.current_invoice_number = generate_invoice_number()


        invoice_number = st.session_state.current_invoice_number


        st.text_input(
            "Invoice Number",
            value=invoice_number,
            disabled=True
        )


    with col4:

        due_date = st.date_input(
            "Due Date",
            format="DD-MM-YYYY"
        )


    st.divider()


           
    # -------- DISPLAY / EDIT ITEMS --------

    if st.session_state.invoice_items:

        item_df = pd.DataFrame(
            st.session_state.invoice_items
        )


        # recalculate amount

        item_df["Amount"] = (
            pd.to_numeric(
                item_df["Quantity"],
                errors="coerce"
            ).fillna(0)
            *
            pd.to_numeric(
                item_df["Rate"],
                errors="coerce"
            ).fillna(0)
        )


        st.data_editor(
            item_df,
            use_container_width=True,
            hide_index=True,
            column_config={

                "Description": st.column_config.TextColumn(
                    "Description"
                ),

                "Quantity": st.column_config.NumberColumn(
                    "Quantity",
                    min_value=1,
                    step=1
                ),

                "Rate": st.column_config.NumberColumn(
                    "Rate",
                    min_value=0.0,
                    step=0.01
                ),

                "Amount": st.column_config.NumberColumn(
                    "Amount",
                    format="$%.2f",
                    disabled=True
                )

            }
        )


        # update session items with calculated amount

        st.session_state.invoice_items = (
            item_df.to_dict("records")
        )


        amount = item_df["Amount"].sum()


    else:

        amount = 0


    st.info(
        f"Service Amount: ${amount:,.2f}"
    )


    # -------- HST --------

    hst_rate = st.number_input(
        "HST Rate (%)",
        min_value=0.0,
        value=13.0,
        step=0.5
    )


    calculated_hst = amount * (hst_rate / 100)


    tax = st.number_input(
        "HST Amount",
        min_value=0.0,
        value=float(calculated_hst),
        step=0.01
    )


    total = amount + tax

    # -------- TOTAL AMOUNT DUE --------

    st.info(
        f"Service Amount: ${amount:,.2f}"
    )


    st.warning(
        f"HST: ${tax:,.2f}"
    )


    st.success(
        f"Total Amount Due: ${total:,.2f}"
    )


    st.divider()



    # -------- PAYMENT STATUS --------

    payment_status = st.selectbox(
        "Status",
        [
            "Unpaid",
            "Paid"
        ]
    )


    if payment_status == "Paid":

        received_date = st.date_input(
            "Payment Received Date"
        )

    else:

        received_date = None



    st.divider()

        # -------- GENERATE INVOICE --------

    if st.button("🧾 Generate Invoice"):

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            title="Prime Accounting Invoice"
        )


        styles = getSampleStyleSheet()

        content = []

        # ================= INVOICE HEADER =================

        logo_path = "Logo.jpeg"


        logo = Image(
            logo_path,
            width=80,
            height=80
        )


        header_data = [
            [
                Paragraph(
                    "<b><font size=20 color='white'>Prime Accounting & Tax</font></b>"
                    "<br/>"
                    "<font size=11 color='white'>Toronto, Ontario</font>",
                    styles["Normal"]
                ),
                logo
            ]
        ]


        header_table = Table(
            header_data,
            colWidths=[350,100]
        )


        header_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0,0),
                    (-1,-1),
                    colors.HexColor("#1f4e79")
                ),
                (
                    "VALIGN",
                    (0,0),
                    (-1,-1),
                    "MIDDLE"
                ),
            ])
        )


        content.append(header_table)

        content.append(
            Spacer(1,20)
        )



        # ================= INVOICE DETAILS =================


        invoice_info = [

            ["Invoice Sent To", customer_name],

            ["Invoice Number", invoice_number],

            ["Invoice Date", str(invoice_date)],

            ["Due Date", str(due_date)],

            ["Payment Status", payment_status]

        ]


        invoice_table = Table(
            invoice_info,
            colWidths=[150,280]
        )


        invoice_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.grey
                )
            ])
        )


        content.append(invoice_table)

        content.append(
            Spacer(1,20)
        )



        # ================= MULTIPLE ITEMS =================


        item_data = [
            [
                "Description",
                "Qty",
                "Rate",
                "Amount"
            ]
        ]


        for item in st.session_state.invoice_items:

            item_data.append(
                [
                    item["Description"],
                    str(item["Quantity"]),
                    f"${item['Rate']:,.2f}",
                    f"${item['Amount']:,.2f}"
                ]
            )


        item_table = Table(
            item_data,
            colWidths=[220,60,80,80]
        )


        item_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0,0),
                    (-1,0),
                    colors.HexColor("#1f7189")
                ),

                (
                    "TEXTCOLOR",
                    (0,0),
                    (-1,0),
                    colors.white
                )
            ])
        )


        content.append(item_table)


        content.append(
            Spacer(1,20)
        )



        # ================= TOTAL =================


        amount = sum(
            item["Amount"]
            for item in st.session_state.invoice_items
        )


        total = amount + tax



        total_table = Table(
            [
                [
                    "Tax",
                    f"${tax:,.2f}"
                ],

                [
                    "TOTAL",
                    f"${total:,.2f}"
                ]
            ],
            colWidths=[300,120]
        )


        total_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.grey
                )
            ])
        )


        content.append(total_table)


        content.append(
            Spacer(1,30)
        )


        content.append(
            Paragraph(
                "Thank you for your business.",
                styles["Normal"]
            )
        )



        # ================= BUILD PDF =================


        doc.build(
            content
        )


        buffer.seek(0)



# -------- SAVE DATABASE --------

        total_quantity = sum(
            item["Quantity"]
            for item in st.session_state.invoice_items
        )

        add_invoice(
            invoice_number,
            customer_name,
            invoice_date,
            due_date,
            str(st.session_state.invoice_items),
            total_quantity,
            0,
            amount,
            tax,
            total,
            payment_status,
            received_date
        )

        add_invoice_items(
            invoice_number,
            st.session_state.invoice_items
        )


        st.success(
            "Invoice saved successfully ✅"
        )


        # CLEAR ALL INVOICE INPUTS

        st.session_state.invoice_items = []


        for key in [
            "item_description",
            "invoice_quantity",
            "invoice_rate",
            "current_invoice_number"
        ]:

            if key in st.session_state:

                del st.session_state[key]


        st.rerun()

    # -------- UNPAID INVOICES --------

    st.divider()

    st.subheader("📌 Unpaid Invoices")


    invoices = get_invoices()


    unpaid_invoices = [
        inv
        for inv in invoices
        if inv["payment_status"] == "Unpaid"
    ]


    if unpaid_invoices:

        unpaid_df = pd.DataFrame(
            unpaid_invoices
        )


        st.dataframe(
            unpaid_df[
                [
                    "invoice_number",
                    "client_name",
                    "invoice_date",
                    "due_date",
                    "total",
                    "payment_status"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )


    else:

        st.info(
            "No unpaid invoices"
        )



    # ================= INVOICE HISTORY =================


if page == "📄 Invoice History":


    st.title(
        "📄 Invoice History"
    )


    invoices = get_invoices()


    if invoices:


        invoice_df = pd.DataFrame(
            invoices
        )


        st.dataframe(
            invoice_df,
            use_container_width=True,
            hide_index=True
        )


        st.divider()


        st.subheader(
            "Delete & Download Invoice"
        )


        invoice_numbers = [
            row["invoice_number"]
            for row in invoices
        ]


        selected_invoice = st.selectbox(
            "Select Invoice",
            ["Select Invoice"] + invoice_numbers
        )

        if selected_invoice != "Select Invoice":

            pdf_buffer = generate_invoice_pdf(selected_invoice)

            st.download_button(
                label="⬇️ Download Invoice PDF",
                data=pdf_buffer,
                file_name=f"Invoice_{selected_invoice}.pdf",
                mime="application/pdf"
            )


        if "confirm_invoice_delete" not in st.session_state:

            st.session_state.confirm_invoice_delete = False



        if st.button(
            "🗑️ Delete Invoice"
        ):


            if selected_invoice != "Select Invoice":

                st.session_state.confirm_invoice_delete = True


            else:

                st.warning(
                    "Please select an invoice"
                )



        if st.session_state.confirm_invoice_delete:


            st.warning(
                f"⚠️ Are you sure you want to delete invoice {selected_invoice}?"
            )


            c1, c2 = st.columns(2)


            with c1:

                if st.button(
                    "✅ Yes, Delete"
                ):


                    delete_invoice(
                        selected_invoice
                    )


                    st.session_state.confirm_invoice_delete = False


                    st.success(
                        "Invoice deleted successfully"
                    )


                    st.rerun()



            with c2:

                if st.button(
                    "❌ Cancel"
                ):


                    st.session_state.confirm_invoice_delete = False


                    st.rerun()



    else:


        st.info(
            "No invoices created yet"
        )



# ================= MAIN =================

if page == "📊 Reports":

    uploaded_excel = st.file_uploader(
        "Upload Excel File",
        type=["xlsx"]
    )

    uploaded_pdf = st.file_uploader(
        "Upload PDF File(s)",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_excel is not None:

        df = pd.read_excel(uploaded_excel)

        # remove blank Excel columns
        df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]


    elif uploaded_pdf is not None:

        import pdfplumber

    if uploaded_pdf:
        st.success(f"{len(uploaded_pdf)} PDF file(s) uploaded successfully")

        transactions = []

    for pdf_file in uploaded_pdf:

        with pdfplumber.open(pdf_file) as pdf:

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

    if uploaded_excel is not None or uploaded_pdf:

        if "df" not in locals():
            st.warning("PDF could not be read. No transactions found.")
            st.stop()

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
        👋 Welcome to Prime Accounting
        </h2>

        <p style="font-size:18px;color:#555;">
        Upload a bank statement or credit card statement
        to start automated categorization and reporting
        </p>

        </div>
        """, unsafe_allow_html=True)

    if ("df" in locals()) and (uploaded_excel is not None or uploaded_pdf):

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

elif page == "🏠 Dashboard":

    st.markdown("""
    <style>

    .main-title {
        font-size:45px;
        font-weight:700;
        color:#1f4e79;
        margin-bottom:0px;
    }

    .sub-title {
        font-size:22px;
        color:#666;
        margin-top:0px;
    }

    .card {
        background:white;
        padding:25px;
        border-radius:18px;
        border:1px solid #e5e7eb;
        box-shadow:0 4px 15px rgba(0,0,0,0.08);
        text-align:center;
    }

    .card-title {
        font-size:18px;
        color:#666;
    }

    .card-number {
        font-size:35px;
        font-weight:bold;
        color:#1f4e79;
    }

    </style>
    """, unsafe_allow_html=True)


    st.markdown(
        """
        <div class="main-title">
        📊 Prime Accounting Dashboard
        </div>

        <div class="sub-title">
        Smart accounting automation platform
        </div>
        """,
        unsafe_allow_html=True
    )


    st.write("")


    st.write("")


    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.markdown(
            """
            <div class="card">
            <div class="card-title">
            👥 Clients
            </div>

            <div class="card-number">
            {}
            </div>

            </div>
            """.format(len(get_clients())),
            unsafe_allow_html=True
        )


    with c2:

        st.markdown(
            """
            <div class="card">

            <div class="card-title">
            📄 Statements
            </div>

            <div class="card-number">
            0
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with c3:

        st.markdown(
            """
            <div class="card">

            <div class="card-title">
            💰 Revenue
            </div>

            <div class="card-number">
            $0
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with c4:

        st.markdown(
            """
            <div class="card">

            <div class="card-title">
            💸 Expenses
            </div>

            <div class="card-number">
            $0
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.write("")

    st.divider()


    st.subheader("🚀 Quick Actions")


    a,b,c = st.columns(3)


    with a:
        st.button(
            "👥 Manage Clients",
            use_container_width=True
        )


    with b:
        st.button(
            "📂 Upload Statement",
            use_container_width=True
        )


    with c:
        st.button(
            "📊 View Reports",
            use_container_width=True
        )


    st.divider()


    st.subheader("📌 Recent Activity")


    empty_df = pd.DataFrame(
        columns=[
            "Client",
            "Activity",
            "Date",
            "Status"
        ]
    )


    st.dataframe(
        empty_df,
        use_container_width=True,
        hide_index=True
    )
