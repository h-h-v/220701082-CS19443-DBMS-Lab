import psycopg2

# Connect to PostgreSQL database
conn_string = 'postgres://wnoqsymb:d3lVJfHNP5xs7A8-nyKHmMzehIqSDK3b@cornelius.db.elephantsql.com/wnoqsymb'
conn = psycopg2.connect(conn_string)

# Create a cursor object to execute SQL queries
cur = conn.cursor()

# Sample product data
products_data = [
    ('Kerosine', 30, 25.00),
    ('Wheat', 50, 10.00),
    ('Tumeric', 75, 15.00),
    ('GoldWinner', 50, 40.00),
    ('Salt', 75, 10.00),
    ('Wheat', 50, 10.00),
    ('Turmeric', 75, 15.00)
    # Add more products as needed
]

# SQL statement to insert products into the 'stock' table
insert_query = '''
INSERT INTO stock (product_name, quantity, price) 
VALUES (%s, %s, %s);
'''

# Execute the SQL statement to insert products
cur.executemany(insert_query, products_data)

# Commit the transaction
conn.commit()

# Close cursor and connection
cur.close()
conn.close()
