import sqlite3
import random
import string
import pandas as pd
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from datetime import datetime
import mysql.connector
MYSQL_HOST = 'YOUR_MYSQL_HOST'
MYSQL_USER = 'YOUR_MYSQL_USERNAME'
MYSQL_PASSWORD = 'YOUR_MYSQL_PASSWORD'
MYSQL_DB = 'YOUR_MYSQL_DATABASE'
def load_masterdata():
    mydb = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM MASTER")
    masterdata_records = mycursor.fetchall()
    mycursor.close()
    mydb.close()

    master_conn = sqlite3.connect('MASTER.db')
    master_cursor = master_conn.cursor()
    master_cursor.execute('''CREATE TABLE IF NOT EXISTS MASTER (
                        REF TEXT,
                        SKU TEXT PRIMARY KEY,
                        PRODUCT_NAME TEXT,
                        COLOUR TEXT,
                        MRP TEXT,
                        CATEGORY TEXT,
                        CAPACITY TEXT,
                        HEIGHT TEXT,
                        WIDTH TEXT,
                        DEPTH TEXT,
                        COST TEXT
                        )''')

    for record in masterdata_records:
        sku = record[1]
        master_cursor.execute("SELECT * FROM MASTER WHERE SKU = ?", (sku,))
        if master_cursor.fetchone() is None:
            
            master_cursor.execute("INSERT INTO MASTER VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", record)

    master_conn.commit()
    master_conn.close()
conn = sqlite3.connect('product_database.db')
cursor = conn.cursor()
def update_mysql_database():
    mydb = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
    )
    mycursor = mydb.cursor()
    cursor.execute("SELECT * FROM product")
    sqlite_data = cursor.fetchall()
    for row in sqlite_data:
        unique_code = row[5]
        mycursor.execute("SELECT COUNT(*) FROM product WHERE Unique_Code = %s", (unique_code,))
        count = mycursor.fetchone()[0]
        if count == 0:
            sql = "INSERT INTO product (Product_Name, Colour, Batch_No, Date, Qty, Unique_Code, Link) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            mycursor.execute(sql, row)
    mydb.commit()
    mycursor.close()
    mydb.close()
load_masterdata()
cursor.execute('''CREATE TABLE IF NOT EXISTS product (
                    Product_Name TEXT,
                    Colour TEXT,
                    Batch_No TEXT,
                    Date TEXT,
                    Qty INTEGER,
                    Unique_Code TEXT,
                    Link TEXT
                )''')
def generate_unique_code(product_name, color):
    characters = string.ascii_letters + string.digits + "!@#$%^*"
    master_conn = sqlite3.connect('MASTER.db')
    master_cursor = master_conn.cursor()
    while True:
        code = ''.join(random.choice(characters) for _ in range(6))
        cursor.execute("SELECT * FROM product WHERE Unique_Code = ?", (code,))
        if cursor.fetchone():
            continue
        query = "SELECT COUNT(*) FROM MASTER WHERE PRODUCT_NAME = ? AND COLOUR = ?"
        master_cursor.execute(query, (product_name, color))
        count = master_cursor.fetchone()[0]
        if count == 0:
            master_conn.close()
            return None
        master_conn.close()
        return code
    master_conn.close()
def add_product():
    for _ in range(int(qty_entry.get())):
        product_name = name_entry.get().upper()
        colour = colour_entry.get().upper()
        unique_code = generate_unique_code(product_name, colour)
        if unique_code is None:
            messagebox.showerror("Error", "No matching product name and color found in Masterdata.")
            return
        batch_no = batch_no_entry.get().upper()
        long_link = f"{YOUR_URL_FOR_QR}?p={product_name}&c={colour}&u={unique_code}"
        cursor.execute("INSERT INTO product VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (product_name, colour, batch_no, date_entry.get(), 1, unique_code, long_link))
    conn.commit()
    messagebox.showinfo("Success", "Product(s) added successfully!")
    export_to_excel(batch_no)
def export_to_excel(batch_no):
    df = pd.read_sql_query("SELECT Product_Name, Colour, Unique_Code, Link FROM product WHERE Batch_No = ?", conn, params=(batch_no,))
    filename = f"{batch_no}_products.xlsx"
    filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=filename, filetypes=[("Excel files", "*.xlsx")])
    if filepath:
        df.to_excel(filepath, index=False)
        messagebox.showinfo("Exported", f"Data exported to {filepath}")
def search_product():
    search_term = search_entry.get()
    if search_by_var.get() == "Batch No":
        df = pd.read_sql_query("SELECT * FROM product WHERE Batch_No = ?", conn, params=(search_term,))
    else:
        df = pd.read_sql_query("SELECT * FROM product WHERE Unique_Code = ?", conn, params=(search_term,))
    if df.empty:
        messagebox.showinfo("Search", "No results found.")
    else:
        result_window = Toplevel(root)
        result_window.title("Search Results")
        tree = ttk.Treeview(result_window, columns=list(df.columns), show="headings")
        tree.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(result_window, orient='vertical', command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        for row in df.to_numpy().tolist():
            tree.insert("", "end", values=row)
def export_all_to_excel():
    df = pd.read_sql_query("SELECT * FROM product", conn)
    filename = "all_products.xlsx"
    filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=filename, filetypes=[("Excel files", "*.xlsx")])
    if filepath:
        df.to_excel(filepath, index=False) 
        messagebox.showinfo("Exported", f"All data exported to {filepath}")
def update_button_clicked():
    try:
        update_mysql_database()
        messagebox.showinfo("Update Success", "Data successfully updated in the MySQL database!")
    except Exception as e:
        messagebox.showerror("Update Failed", f"An error occurred: {e}")
root = Tk()
root.geometry('400x400')
root.title("QR Generator - Strabo")
separator = ttk.Separator(root, orient='horizontal')
label_width = 20
entry_width = 35
pad_x = 10
pad_y = 5
Label(root, text="Product Name:", width=label_width).grid(row=0, column=0, padx=pad_x, pady=pad_y, sticky='e')
Label(root, text="Colour:", width=label_width).grid(row=1, column=0, padx=pad_x, pady=pad_y, sticky='e')
Label(root, text="Batch No:", width=label_width).grid(row=2, column=0, padx=pad_x, pady=pad_y, sticky='e')
Label(root, text="Date:", width=label_width).grid(row=3, column=0, padx=pad_x, pady=pad_y, sticky='e')
Label(root, text="Quantity:", width=label_width).grid(row=4, column=0, padx=pad_x, pady=pad_y, sticky='e')
name_entry = Entry(root, width=entry_width)
colour_entry = Entry(root, width=entry_width)
batch_no_entry = Entry(root, width=entry_width)
qty_entry = Entry(root, width=entry_width)
date_entry = Entry(root, width=entry_width)
name_entry.grid(row=0, column=1, padx=pad_x, pady=pad_y)
colour_entry.grid(row=1, column=1, padx=pad_x, pady=pad_y)
batch_no_entry.grid(row=2, column=1, padx=pad_x, pady=pad_y)
qty_entry.grid(row=4, column=1, padx=pad_x, pady=pad_y)
date_entry.insert(0, datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
date_entry.grid(row=3, column=1, padx=pad_x, pady=pad_y)
generate_button = Button(root, text="Generate", command=add_product)
generate_button.grid(row=5, column=0, columnspan=3, padx=pad_x, pady=pad_y)
update_mysql_button = Button(root, text="Update MySQL Database", command=update_button_clicked)
update_mysql_button.grid(row=6, column=0, columnspan=2, padx=pad_x, pady=pad_y)
separator.grid(row=8, columnspan=2, sticky='ew', padx=10, pady=10)
Label(root, text="Search by:", width=label_width).grid(row=9, column=0, padx=pad_x, pady=pad_y, sticky='e')
search_by_var = StringVar(root, "Batch No")
OptionMenu(root, search_by_var, "Batch No", "Unique Code").grid(row=9, column=1, padx=pad_x, pady=pad_y)
search_entry = Entry(root, width=entry_width)
search_entry.grid(row=10, column=0, columnspan=2, padx=pad_x, pady=pad_y)
search_button = Button(root, text="Search", command=search_product)
search_button.grid(row=11, column=0, columnspan=2, padx=pad_x, pady=pad_y)
export_all_button = Button(root, text="Export All to Excel", command=export_all_to_excel)
export_all_button.grid(row=12, column=0, columnspan=2, padx=pad_x, pady=pad_y)
root.mainloop()
