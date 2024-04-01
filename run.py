from flask import Flask, render_template, redirect, url_for, request, session, make_response, jsonify
from flask_mysqldb import MySQL
import sys
import requests
import redis
import json
import os
from uuid import uuid4
import time
import schedule
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Y1012Jqkhkp'
app.config['MYSQL_DB'] = 'ganeshdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = os.urandom(24)

mysql = MySQL(app)

# Establish the connection
connection = mysql.connection

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)


def connect_to_redis():
    global redis_client
    try:
        # Attempt to connect to Redis
        redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        redis_client.ping()  # Check if Redis is available
        print("Connected to Redis")
    except redis.exceptions.ConnectionError:
        # Handle connection errors
        print("Error: Unable to connect to Redis. Exiting program.")
        sys.exit(1)

# Call the connect_to_redis function to establish the connection
connect_to_redis()

def fetch_and_cache_products():
    api_url = "https://fakestoreapi.com/products"
    try:
        # Fetch products from the API
        response = requests.get(api_url)
        response.raise_for_status()  # Raise exception for HTTP errors
        products = response.json()

        # Cache the obtained products in Redis
        redis_client.set('products', json.dumps(products))
        redis_client.expire('products', 60)  # Set expiration time to 60 seconds (1 minute)

        return products
    except requests.exceptions.RequestException as e:
        print("Error fetching products from API:", e)
        return []

def fetch_products():
    # Attempt to fetch products from Redis cache
    cached_products = redis_client.get('products')
    if cached_products:
        print("Products retrieved from Redis cache")
        return json.loads(cached_products)
    else:
        print("Products not found in cache")
        return None


@app.route('/products')
def display_products():
    products = fetch_products()
    user_name = None
    if 'user_id' in session:
        user_id = session['user_id']
        user_name = fetch_user_name(user_id)  # Assuming fetch_user_name is defined elsewhere
    if products is not None:
        #print("Products fetched from Redis cache")
        return render_template('products.html', products=products, user_name=user_name)
    else:
        # Fetch and cache products if not available
        products = fetch_and_cache_products()
        if products:
            print("Products fetched from API and cached in Redis")
            return render_template('products.html', products=products, user_name=user_name)
        else:
            print("Error: Failed to fetch and cache products")
            return "<h1>Error: Failed to fetch and cache products</h1>"

def fetch_user_name(user_id):
    try:
        # Create cursor
        cur = mysql.connection.cursor()

        # Fetch user's name from the database based on the user ID
        cur.execute("SELECT name FROM registration WHERE id = %s", (user_id,))
        user = cur.fetchone()

        # Close cursor
        cur.close()

        if user:
            return user['name']
        else:
            return None
    except Exception as e:
        print("Error fetching user's name:", e)
        return None

@app.route('/increase_quantity/<int:product_id>', methods=['POST'])
def increase_quantity(product_id):
    # Retrieve user ID from session
    user_id = session.get('user_id')

    # Check if user ID is available
    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401

    try:
        # Retrieve updated quantity from request data
        new_quantity = request.json['quantity']
        print("New_quantity ",new_quantity)
        # Connect to the database
        cur = mysql.connection.cursor()
        # Check if the product is already in the cart
        #cur.execute("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        #result = cur.fetchone()

# Access the value from the dictionary and convert it to an integer
        #quantity_str = result['quantity']
        #quantity_int = int(quantity_str)
        #print("integer qu:",quantity_int)
                                          
        #new_total_quantity = quantity_int + new_quantity
        #print("new total: ",new_total_quantity)
        #cur.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s", (new_total_quantity, user_id, product_id))
        
        
#Below query is to replace value instead of adding the new value with existing value        
        cur.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s", (new_quantity, user_id, product_id))

        # Commit the transaction
        mysql.connection.commit()

        # Close the cursor
        cur.close()

        # Return success response
        return jsonify({'message': 'Quantity increased successfully'})
    except Exception as e:
        return jsonify({'error': 'Failed to increase quantity', 'details': str(e)}), 500


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):

        # Retrieve user ID from session
    user_id = session.get('user_id')

    # Check if user ID is available
    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401
    try:
        
        # Print received product_id
        print("Received product_id:", product_id)

        # Extract user_id from session or request cookies
        user_id = session.get('user_id') or request.cookies.get('user_id')

        # Print user_id for debugging
        print("User ID:", user_id)
        # Retrieve user ID from session or cookies
        user_id = session.get('user_id') or request.cookies.get('user_id')

        # Ensure user is logged in
        if not user_id:
            return redirect(url_for('login'))

        # Delete the product from the cart for the current user
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('view_cart'))
    except Exception as e:
        print("Error removing item from cart:", e)
        return "Error removing item from cart"


@app.route('/view_cart')
def view_cart():

        # Retrieve user ID from session
    user_id = session.get('user_id')

    # Check if user ID is available
    if user_id is None:
        return  redirect(url_for('login'))
    # Retrieve user ID from request cookies
    
    try:
        # Create cursor
        cur = mysql.connection.cursor()

        # Fetch cart items with quantity for the current user
        cur.execute("""
            SELECT product_id, quantity
            FROM cart 
            WHERE user_id = %s
        """, (user_id,))
        cart_items = cur.fetchall()

        # Close the cursor
        cur.close()

        # List to store cart items with product details
        cart_with_details = []
        overall_price = 0
        # Fetch product details for each cart item from the API
        for item in cart_items:
            product_id = item['product_id']
            quantity = item['quantity']

            # Fetch product details from the API
            response = requests.get(f'https://fakestoreapi.com/products/{product_id}')
            if response.status_code == 200:
                product_data = response.json()
                # Extract product name and price from the JSON response
                product_name = product_data.get('title', 'Unknown Product')
                product_price = product_data.get('price', 0)
                # Add product details to the cart item
                item['product_name'] = product_name
                item['product_price'] = round(product_price,2)                
                item['total_price'] = round(quantity * product_price,2)
                overall_price += item['total_price']
                cart_with_details.append(item)

            else:
                # Handle API request failure
                print(f"Failed to fetch product details for product ID {product_id}")
        print("overall_price:", overall_price)
        # Render the template with cart items and product informations
        rounded_total_price=round(product_price,2)
        rounded_overall_price = round(overall_price, 2)
        return render_template('cart.html', cart_items=cart_items, overall_price=rounded_overall_price, product_price=rounded_total_price)
    except Exception as e:
        # Handle any errors that occur during fetching cart items
        print("Error fetching cart items:", e)
        return "No products in cart"

@app.route('/register',  methods=['GET', 'POST'])
def register():

    if 'user_id' in session:
        # User is already logged in, redirect them to their profile
        return redirect(url_for('display_products'))
    if request.method == 'POST':
        # Fetch form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phonenumber = request.form['phonenumber']

        # Create cursor
        cur = mysql.connection.cursor()

       # Check if user with the same email exists
        cur.execute("SELECT * FROM registration WHERE email = %s", (email,))
        existing_email_user = cur.fetchone()

        # Check if user with the same phone number exists
        cur.execute("SELECT * FROM registration WHERE phonenumber = %s", (phonenumber,))
        existing_phonenumber_user = cur.fetchone()

        if existing_email_user:
            cur.close()
            return render_template('register.html', error_message='User with this email already exists!')

        if existing_phonenumber_user:
            cur.close()
            return render_template('register.html', error_message='User with this phone number already exists!')
       # Insert user into database
        cur.execute("INSERT INTO registration (name, email, password, phonenumber) VALUES (%s, %s, %s, %s)", (name, email, password, phonenumber))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        return redirect(url_for('login'),error_message='User already exists with ')

    return render_template('register.html')

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id: int):
    if 'user_id' not in session:
        # If user is not logged in, return an error response
        return jsonify({'error': 'User not logged in'})

    user_id = session['user_id']

    try:
        # Create cursor
        cur = mysql.connection.cursor()
        user_quantity = request.json['quantity']
        print("user_quantity ",user_quantity)
            # Otherwise, add a new item to the cart
        cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)", (user_id, product_id,user_quantity))

        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Item added to cart successfully'})
    except Exception as e:
        print("Error adding item to cart:", e)
        return jsonify({'error': 'Error adding item to cart'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # User is already logged in, redirect them to their profile
        return redirect(url_for('display_products'))

    if request.method == 'POST':
        # Fetch form data
        email_or_phonenumber = request.form['email_or_phonenumber']
        password = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Check if user exists with given email or phone number
        cur.execute("SELECT * FROM registration WHERE email = %s OR phonenumber = %s", (email_or_phonenumber, email_or_phonenumber))
        user = cur.fetchone()

        if user and password == user['password']:
            # Generate session token
            session_token = str(uuid4())

            # Set user id, session token, and last activity time in session
            session['user_id'] = user['id']
            session['session_token'] = session_token
            #session['last_activity'] = datetime.now()

            # Set user id, session token, and expiration time as cookies
            response = make_response(redirect(url_for('display_products')))
            response.set_cookie('user_id', str(user['id']))
            response.set_cookie('session_token', session_token)
            #response.set_cookie('session_expiration', str(SESSION_TIMEOUT))

            return response  # Redirect to user's profile page after successful login
        else:
            #error = "Invalid email/phone number or password"
            return render_template('login.html', error='Invalid credentials')  # Render login page with error message

    return render_template('login.html')

@app.route('/check_cart/<int:product_id>', methods=['GET'])
def check_cart(product_id):
    # Retrieve user ID from session
    user_id = session.get('user_id')

    # Check if user ID is available
    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401

    try:
        # Connect to the database
        cur = mysql.connection.cursor()

        # Execute the SELECT query to check if the product is in the cart
        cur.execute("SELECT * FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))

        # Fetch one row (if exists)
        row = cur.fetchone()

        # Close the cursor
        cur.close()

        # Return JSON response indicating if the product exists in the cart
        return jsonify({'exists': bool(row)})

    except Exception as e:
        return jsonify({'error': 'Failed to check cart', 'details': str(e)}), 500


@app.route('/logout')
def logout():
    # Clear session data
    session.clear()

    # Clear user_id, session_token, and session_expiration cookies
    response = make_response(redirect(url_for('login')))
    response.set_cookie('user_id', '', expires=0)
    response.set_cookie('session_token', '', expires=0)
    response.set_cookie('session_expiration', '', expires=0)

    return response

@app.route('/session-details')
def session_details():
    # Retrieve user ID from session
    user_id = session.get('user_id')

    # Check if user ID is available
    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401
   
    return render_template('session_details.html')



if __name__ == '__main__':
    connect_to_redis()
    app.run(debug=True)
