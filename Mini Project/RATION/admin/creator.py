import psycopg2

# Connect to PostgreSQL database
# Replace 'your_connection_string' with the connection string provided by ElephantSQL
conn_string = 'postgres://wnoqsymb:d3lVJfHNP5xs7A8-nyKHmMzehIqSDK3b@cornelius.db.elephantsql.com/wnoqsymb'
conn = psycopg2.connect(conn_string)

# Create a cursor object to execute SQL queries
cur = conn.cursor()

# SQL statement to create the 'stock' table
create_table_query = '''
CREATE TABLE IF NOT EXISTS stock (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);
'''

# Execute the SQL statement to create the table
cur.execute(create_table_query)

# Commit the transaction
conn.commit()

# Close cursor and connection
cur.close()
conn.close()
