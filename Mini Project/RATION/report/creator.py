import psycopg2

# Connect to PostgreSQL database
# Replace 'your_connection_string' with the connection string provided by ElephantSQL
conn_string = 'postgres://wnoqsymb:d3lVJfHNP5xs7A8-nyKHmMzehIqSDK3b@cornelius.db.elephantsql.com/wnoqsymb'
conn = psycopg2.connect(conn_string)

# Create a cursor object to execute SQL queries
cur = conn.cursor()

# SQL statement to create the 'stock' table
create_table_query = '''
CREATE TABLE loginhistory (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action varchar(1000)
);
'''

# Execute the SQL statement to create the table
cur.execute(create_table_query)

# Commit the transaction
conn.commit()

# Close cursor and connection
cur.close()
conn.close()
