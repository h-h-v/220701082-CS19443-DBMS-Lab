from flask import Flask, render_template, request, session, redirect, url_for
import psycopg2
from psycopg2 import sql
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connection string to PostgreSQL database
conn_string = 'postgres://wnoqsymb:d3lVJfHNP5xs7A8-nyKHmMzehIqSDK3b@cornelius.db.elephantsql.com/wnoqsymb'

def create_connection():
    try:
        connection = psycopg2.connect(conn_string)
        return connection
    except psycopg2.DatabaseError as e:
        print(f"Error: {e}")
        return None

def log_action(username, action):
    conn = create_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO loginhistory (username, action) VALUES (%s, %s)", (username, action))
            conn.commit()
            cur.close()
        except psycopg2.Error as e:
            print(f"Error executing SQL query: {e}")
        finally:
            conn.close()

@app.route('/')
def index():
    return render_template('login.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        session['username'] = username

        # Insert login information with timestamp into the database
        log_action(username, 'Login attempt')
        log_action(username, 'Login successful')
        return redirect(url_for('get_otp'))
    return render_template("login.html")

@app.route("/get_otp", methods=["GET", "POST"])
def get_otp():
    if request.method == "POST":
        if request.form['otp'] == "123456":  # Dummy OTP validation
            log_action(session['username'], 'OTP validated')
            return redirect(url_for('render_products'))
        else:
            log_action(session['username'], 'OTP validation failed')
            error = 'Invalid OTP. Please try again.'
            return render_template("get_otp.html", error=error)
    return render_template("get_otp.html")

@app.route("/render_products")
def render_products():
    conn = create_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM stock")
            rows = cur.fetchall()
            cur.close()
        except psycopg2.Error as e:
            print(f"Error fetching products: {e}")
            rows = []
        finally:
            conn.close()
    else:
        rows = []

    product_data = [{'id': row[0], 'product_name': row[1], 'price': row[3]} for row in rows]
    return render_template("products.html", products=product_data)

@app.route("/add_to_cart/<int:product_id>", methods=["GET", "POST"])
def add_to_cart(product_id):
    if request.method == "POST":
        quantity = int(request.form.get('quantity', 1))  # Get quantity from form, default to 1
        
        conn = create_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM stock WHERE id = %s", (product_id,))
                row = cur.fetchone()
                cur.close()
            except psycopg2.Error as e:
                print(f"Error retrieving product: {e}")
                row = None
            finally:
                conn.close()
            
            if row:
                product_name = row[1]
                price = row[3]
                product = {'id': product_id, 'name': product_name, 'price': price, 'quantity': quantity}
                cart = session.get('cart', [])

                for item in cart:
                    if item['id'] == product_id:
                        item['quantity'] += quantity
                        break
                else:
                    cart.append(product)

                session['cart'] = cart
                username = session.get('username', 'Anonymous')
                action = f'Added {quantity} of {product_name} (ID: {product_id}) to cart'
                log_action(username, action)

                return redirect(url_for('payment'))
    
    return redirect(url_for('render_products'))

@app.route("/payment")
def payment():
    cart = session.get('cart', [])
    valid_items = [item for item in cart if item['price'] is not None]
    total_price = sum(float(item['price']) * item['quantity'] for item in valid_items)
    return render_template("payment.html", cart=cart, total_price=total_price)

@app.route("/clear_cart", methods=["POST"])
def clear_cart():
    session.pop('cart', None)
    return '', 204

@app.route("/view_logs", methods=["GET", "POST"])
def view_logs():
    filter_type = request.form.get('filter_type', 'all')
    conn = create_connection()
    logs = []

    if conn:
        try:
            cur = conn.cursor()

            if filter_type == 'weekly':
                cur.execute("""
                    SELECT * FROM loginhistory 
                    WHERE login_time >= NOW() - INTERVAL '1 week' 
                    ORDER BY login_time DESC
                """)
            elif filter_type == 'monthly':
                cur.execute("""
                    SELECT * FROM loginhistory 
                    WHERE login_time >= NOW() - INTERVAL '1 month' 
                    ORDER BY login_time DESC
                """)
            elif filter_type == 'yearly':
                cur.execute("""
                    SELECT * FROM loginhistory 
                    WHERE login_time >= NOW() - INTERVAL '1 year' 
                    ORDER BY login_time DESC
                """)
            else:
                cur.execute("SELECT * FROM loginhistory ORDER BY login_time DESC")

            logs = cur.fetchall()
            cur.close()
        except psycopg2.Error as e:
            print(f"Error fetching logs: {e}")
        finally:
            conn.close()

    stats = get_statistics()
    return render_template("view_logs.html", logs=logs, filter_type=filter_type, stats=stats)


def get_statistics():
    stats = {
        'most_purchased_product': (None, None, 0),
        'least_purchased_product': (None, None, 0),
        'avg_purchases_per_product': 0,
        'avg_quantity_per_product': []
    }
    conn = create_connection()
    
    if conn:
        try:
            cur = conn.cursor()

            # Most purchased product
            cur.execute("""
                SELECT 
                    s.id,
                    s.product_name,
                    COUNT(lh.action) AS purchase_count
                FROM loginhistory lh
                JOIN stock s ON s.id = CAST(SPLIT_PART(SPLIT_PART(lh.action, 'ID: ', 2), ')', 1) AS INTEGER)
                WHERE lh.action LIKE 'Added%'
                GROUP BY s.id, s.product_name
                ORDER BY purchase_count DESC
                LIMIT 1
            """)
            result = cur.fetchone()
            if result:
                stats['most_purchased_product'] = result

            # Least purchased product
            cur.execute("""
                SELECT 
                    s.id,
                    s.product_name,
                    COUNT(lh.action) AS purchase_count
                FROM loginhistory lh
                JOIN stock s ON s.id = CAST(SPLIT_PART(SPLIT_PART(lh.action, 'ID: ', 2), ')', 1) AS INTEGER)
                WHERE lh.action LIKE 'Added%'
                GROUP BY s.id, s.product_name
                ORDER BY purchase_count ASC
                LIMIT 1
            """)
            result = cur.fetchone()
            if result:
                stats['least_purchased_product'] = result

            # Average purchases per product
            cur.execute("""
                SELECT AVG(purchase_count) AS average_purchases
                FROM (
                    SELECT 
                        COUNT(lh.action) AS purchase_count
                    FROM loginhistory lh
                    JOIN stock s ON s.id = CAST(SPLIT_PART(SPLIT_PART(lh.action, 'ID: ', 2), ')', 1) AS INTEGER)
                    WHERE lh.action LIKE 'Added%'
                    GROUP BY s.id
                ) AS subquery
            """)
            result = cur.fetchone()
            if result and result[0] is not None:
                stats['avg_purchases_per_product'] = result[0]

            # Average quantity per product
            cur.execute("""
                SELECT 
                    s.id,
                    s.product_name,
                    AVG(CAST(SPLIT_PART(lh.action, ' ', 2) AS INTEGER)) AS avg_quantity
                FROM loginhistory lh
                JOIN stock s ON s.id = CAST(SPLIT_PART(SPLIT_PART(lh.action, 'ID: ', 2), ')', 1) AS INTEGER)
                WHERE lh.action LIKE 'Added%'
                GROUP BY s.id, s.product_name
                ORDER BY s.id
            """)
            stats['avg_quantity_per_product'] = cur.fetchall()

            cur.close()
        except psycopg2.Error as e:
            print(f"Error fetching statistics: {e}")
        finally:
            conn.close()

    return stats





if __name__ == "__main__":
    app.run(debug=True)
