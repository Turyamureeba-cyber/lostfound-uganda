from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
import sqlite3
import re
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['DATABASE'] = 'lostfound.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Your database already exists with the category table
    # Just verify and add sample data if needed
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if we have categories, if not add some
    c.execute('SELECT COUNT(*) FROM category')
    if c.fetchone()[0] == 0:
        # Insert default categories matching your PHP app
        categories = [
            ('Electronics', '📱'),
            ('Documents', '📄'),
            ('Jewelry', '💎'),
            ('Bags', '🎒'),
            ('Clothing', '👕'),
            ('Keys', '🔑'),
            ('Pets', '🐕'),
            ('Vehicles', '🚗'),
            ('Books', '📚'),
            ('Money', '💰'),
            ('Others', '📦')
        ]
        c.executemany('INSERT INTO category (name, icon) VALUES (?, ?)', categories)
    
    # Check if we have sample items
    c.execute('SELECT COUNT(*) FROM items')
    if c.fetchone()[0] == 0:
        sample_items = [
            ('lost', 'iPhone 13 Pro Max', 'Lost my black iPhone near Nakumatt Oasis Mall.', 'Electronics', 'Kampala', 'iphone.jpg', 1),
            ('found', 'Black Wallet', 'Found wallet with IDs and cards inside.', 'Others', 'Wakiso', 'wallet.jpg', 1),
            ('lost', 'School Bag', 'Red backpack with school books and calculator.', 'Bags', 'Mukono', 'bag.jpg', 1),
            ('found', 'Car Keys', 'Set of Toyota car keys found in parking lot.', 'Keys', 'Kampala', 'keys.jpg', 1),
        ]
        c.executemany('INSERT INTO items (type, title, description, category, location, image_url, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)', sample_items)
    
    conn.commit()
    conn.close()

def validate_uganda_phone(phone):
    clean_phone = re.sub(r'\D', '', phone)
    if clean_phone.startswith('256') and len(clean_phone) == 12:
        return clean_phone
    elif clean_phone.startswith('7') and len(clean_phone) == 9:
        return '256' + clean_phone
    elif clean_phone.startswith('07') and len(clean_phone) == 10:
        return '256' + clean_phone[1:]
    return None

def is_logged_in():
    return 'user_id' in session

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    if is_logged_in():
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return render_template('home.html', user=user)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        validated_phone = validate_uganda_phone(phone)
        
        if not validated_phone:
            return render_template('login.html', error='Invalid Uganda phone number')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE phone = ?', (validated_phone,)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Phone not registered')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        if not name:
            return render_template('register.html', error='Please enter your name')
        
        validated_phone = validate_uganda_phone(phone)
        if not validated_phone:
            return render_template('register.html', error='Invalid Uganda phone number')
        
        conn = get_db_connection()
        
        # Check if user exists
        existing_user = conn.execute('SELECT * FROM users WHERE phone = ?', (validated_phone,)).fetchone()
        if existing_user:
            conn.close()
            return render_template('register.html', error='Phone already registered')
        
        # Create user
        conn.execute('INSERT INTO users (name, phone) VALUES (?, ?)', (name, validated_phone))
        conn.commit()
        
        # Get the new user ID
        user = conn.execute('SELECT * FROM users WHERE phone = ?', (validated_phone,)).fetchone()
        conn.close()
        
        session['user_id'] = user['id']
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/items')
def get_items():
    page = int(request.args.get('page', 1))
    limit = 10
    offset = (page - 1) * limit
    item_type = request.args.get('type', 'all')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    
    query = 'SELECT * FROM items WHERE status = "active"'
    params = []
    
    if item_type in ['lost', 'found']:
        query += ' AND type = ?'
        params.append(item_type)
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    items = conn.execute(query, params).fetchall()
    conn.close()
    
    items_data = []
    for item in items:
        # Simple fix: use the database path as is, but ensure it starts with /static/
        image_url = ''
        if item['image_url'] and item['image_url'].strip():
            db_path = item['image_url'].strip()
            # Ensure the path starts with /static/
            if not db_path.startswith('/static/'):
                image_url = f"/static/{db_path}"
            else:
                image_url = db_path
        else:
            image_url = "/static/placeholder.png"
        
        items_data.append({
            'id': item['id'],
            'title': item['title'],
            'description': item['description'],
            'category': item['category'],
            'location': item['location'],
            'type': item['type'],
            'image_url': image_url,
            'created_at': item['created_at']
        })
    
    return jsonify({
        'items': items_data,
        'has_next': len(items) == limit,
        'page': page
    })

@app.route('/api/categories')
def get_categories():
    conn = get_db_connection()
    # Use your existing category table
    categories = conn.execute('SELECT * FROM category ORDER BY name').fetchall()
    conn.close()
    return jsonify([{
        'id': cat['id'],
        'name': cat['name'], 
        'icon': cat['icon']
    } for cat in categories])

# Serve uploaded files
@app.route('/static/uploads/')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

    