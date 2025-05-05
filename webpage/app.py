from flask import Flask, render_template, request, send_file, jsonify, session
import psycopg2
import os
import pandas as pd
from io import StringIO
import uuid
import datetime
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'card_database')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# Create directory for CSV exports
if not os.path.exists('exports'):
    os.makedirs('exports')

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    search_type = 'number'  # Default search type
    export_filename = None
    
    # Initialize selected cards in session if not present
    if 'selected_cards' not in session:
        session['selected_cards'] = []
    
    if request.method == 'POST':
        # Check if we're adding to cart or searching
        if 'add_to_selection' in request.form:
            # Get the selected card IDs from form
            selected_ids = request.form.getlist('select_card')
            
            # Get the card data to add to session
            cards_to_add = []
            for card_id in selected_ids:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Get all columns for the selected cards
                    cursor.execute(
                        'SELECT * FROM one_piece_cards WHERE "TCGplayer Id" = %s',
                        (card_id,)
                    )
                    
                    card_row = cursor.fetchone()
                    if card_row:
                        # Get column names
                        column_names = [desc[0] for desc in cursor.description]
                        # Create a dictionary of column name -> value
                        card_dict = dict(zip(column_names, card_row))
                        
                        # Only add if not already in the list
                        if not any(c.get('TCGplayer Id') == card_dict.get('TCGplayer Id') for c in session['selected_cards']):
                            cards_to_add.append(card_dict)
                    
                    cursor.close()
                    conn.close()
                    
                except Exception as e:
                    error = f"Database error: {str(e)}"
            
            # Add to session
            session['selected_cards'].extend(cards_to_add)
            # Save session
            session.modified = True
            
        elif 'clear_selection' in request.form:
            # Clear the selected cards
            session['selected_cards'] = []
            session.modified = True
            
        elif 'export_selected' in request.form:
            # Export selected cards to CSV
            if session['selected_cards']:
                # Convert list of dictionaries to DataFrame
                df = pd.DataFrame(session['selected_cards'])
                
                # Ensure columns are in the right order and match expected format
                expected_columns = [
                    "TCGplayer Id", "Product Line", "Set Name", "Product Name", "Title", 
                    "Number", "Rarity", "Condition", "TCG Market Price", "TCG Direct Low", 
                    "TCG Low Price With Shipping", "TCG Low Price", "Total Quantity", 
                    "Add to Quantity", "TCG Marketplace Price", "Photo URL"
                ]
                
                # Create a DataFrame with all expected columns
                export_df = pd.DataFrame(columns=expected_columns)
                
                # Fill with data from selected cards
                for column in expected_columns:
                    if column in df.columns:
                        export_df[column] = df[column]
                
                export_filename = export_to_csv(export_df, "selected_cards")
        
        else:
            # Normal search operation
            search_type = request.form.get('search_type')
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if search_type == 'number':
                    card_number = request.form.get('card_number')
                    
                    # Execute the search query by card number only
                    cursor.execute(
                        'SELECT "TCGplayer Id", "Product Name", "Number", "Set Name" FROM one_piece_cards WHERE "Number" = %s',
                        (card_number,)
                    )
                    
                    result = cursor.fetchall()
                    
                elif search_type == 'tcgplayer_id':
                    tcgplayer_id = request.form.get('tcgplayer_id')
                    
                    # Execute the search query by TCGplayer Id
                    cursor.execute(
                        'SELECT * FROM one_piece_cards WHERE "TCGplayer Id" = %s',
                        (tcgplayer_id,)
                    )
                    
                    row = cursor.fetchone()
                    if row:
                        # Get column names
                        column_names = [desc[0] for desc in cursor.description]
                        # Create a dictionary of column name -> value
                        result = dict(zip(column_names, row))
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                error = f"Database error: {str(e)}"
    
    return render_template('index.html', 
                          result=result, 
                          error=error, 
                          search_type=search_type, 
                          export_filename=export_filename,
                          selected_cards=session.get('selected_cards', []))

def export_to_csv(df, prefix):
    # Generate unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{prefix}_{timestamp}_{unique_id}.csv"
    filepath = os.path.join('exports', filename)
    
    # Export dataframe to CSV
    df.to_csv(filepath, index=False)
    
    return filename

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    filepath = os.path.join('exports', filename)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    # Create templates directory and index.html if they don't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    with open('templates/index.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>One Piece Card Search</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
        .search-form, .selection-panel {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .checkbox-group {
            margin-top: 15px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
        }
        button:hover {
            background-color: #45a049;
        }
        .btn-blue {
            background-color: #2196F3;
        }
        .btn-blue:hover {
            background-color: #0b7dda;
        }
        .btn-red {
            background-color: #f44336;
        }
        .btn-red:hover {
            background-color: #d32f2f;
        }
        .download-btn {
            background-color: #2196F3;
        }
        .download-btn:hover {
            background-color: #0b7dda;
        }
        .result {
            padding: 15px;
            background-color: #e8f5e9;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .error {
            padding: 15px;
            background-color: #ffebee;
            color: #c62828;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .search-fields {
            margin-top: 15px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .card-count {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .actions {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        .overflow-table {
            overflow-x: auto;
        }
    </style>
    <script>
        function toggleSearchFields() {
            const searchType = document.getElementById('search_type').value;
            document.getElementById('number_field').style.display = searchType === 'number' ? 'block' : 'none';
            document.getElementById('tcgplayer_id_field').style.display = searchType === 'tcgplayer_id' ? 'block' : 'none';
        }
        
        window.onload = function() {
            toggleSearchFields();
        };
        
        function toggleSelectAll(source) {
            const checkboxes = document.getElementsByName('select_card');
            for(let i=0; i<checkboxes.length; i++) {
                checkboxes[i].checked = source.checked;
            }
        }
    </script>
</head>
<body>
    <h1>One Piece Card Search</h1>
    
    <div class="search-form">
        <form method="POST">
            <div class="form-group">
                <label for="search_type">Search By:</label>
                <select id="search_type" name="search_type" onchange="toggleSearchFields()">
                    <option value="number" {% if search_type == 'number' %}selected{% endif %}>Card Number</option>
                    <option value="tcgplayer_id" {% if search_type == 'tcgplayer_id' %}selected{% endif %}>TCGplayer ID</option>
                </select>
            </div>
            
            <div id="number_field" class="search-fields">
                <div class="form-group">
                    <label for="card_number">Card Number:</label>
                    <input type="text" id="card_number" name="card_number" value="OP09-004" placeholder="e.g., OP09-004">
                </div>
            </div>
            
            <div id="tcgplayer_id_field" class="search-fields">
                <div class="form-group">
                    <label for="tcgplayer_id">TCGplayer ID:</label>
                    <input type="text" id="tcgplayer_id" name="tcgplayer_id" placeholder="Enter TCGplayer ID">
                </div>
            </div>
            
            <button type="submit">Search</button>
        </form>
    </div>
    
    {% if error %}
    <div class="error">
        {{ error }}
    </div>
    {% endif %}
    
    {% if selected_cards %}
    <div class="selection-panel">
        <h2>Selected Cards</h2>
        <div class="card-count">{{ selected_cards|length }} card(s) selected</div>
        
        <div class="overflow-table">
            <table>
                <tr>
                    <th>TCGplayer ID</th>
                    <th>Product Name</th>
                    <th>Number</th>
                    <th>Set Name</th>
                    <th>Rarity</th>
                </tr>
                {% for card in selected_cards %}
                <tr>
                    <td>{{ card.get('TCGplayer Id', '') }}</td>
                    <td>{{ card.get('Product Name', '') }}</td>
                    <td>{{ card.get('Number', '') }}</td>
                    <td>{{ card.get('Set Name', '') }}</td>
                    <td>{{ card.get('Rarity', '') }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="actions">
            <form method="POST">
                <button type="submit" name="clear_selection" class="btn-red">Clear Selection</button>
            </form>
            
            <form method="POST">
                <button type="submit" name="export_selected" class="btn-blue">Export to CSV</button>
            </form>
        </div>
    </div>
    {% endif %}
    
    {% if export_filename %}
    <div class="result">
        <h3>CSV Export</h3>
        <p>Your data has been exported to a CSV file:</p>
        <p><a href="{{ url_for('download_file', filename=export_filename) }}" class="download-btn" style="display: inline-block; padding: 10px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 4px;">Download {{ export_filename }}</a></p>
    </div>
    {% endif %}
    
    {% if result and search_type == 'number' %}
    <div class="result">
        <h2>Search Results</h2>
        
        {% if result|length > 0 %}
            <form method="POST">
                <table>
                    <tr>
                        <th><input type="checkbox" onClick="toggleSelectAll(this)"></th>
                        <th>TCGplayer ID</th>
                        <th>Product Name</th>
                        <th>Number</th>
                        <th>Set</th>
                    </tr>
                    {% for card in result %}
                    <tr>
                        <td><input type="checkbox" name="select_card" value="{{ card[0] }}"></td>
                        <td>{{ card[0] }}</td>
                        <td>{{ card[1] }}</td>
                        <td>{{ card[2] }}</td>
                        <td>{{ card[3] }}</td>
                    </tr>
                    {% endfor %}
                </table>
                
                <div class="actions">
                    <button type="submit" name="add_to_selection">Add Selected to List</button>
                </div>
            </form>
        {% else %}
            <p>No cards found with this number.</p>
        {% endif %}
    </div>
    {% elif result and search_type == 'tcgplayer_id' %}
    <div class="result">
        <h2>Search Results</h2>
        <form method="POST">
            <input type="hidden" name="select_card" value="{{ result['TCGplayer Id'] }}">
            <div class="overflow-table">
                <table>
                    <tr>
                        <th>Field</th>
                        <th>Value</th>
                    </tr>
                    {% for field, value in result.items() %}
                    <tr>
                        <td>{{ field }}</td>
                        <td>{{ value }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            
            <div class="actions">
                <button type="submit" name="add_to_selection">Add to Selection</button>
            </div>
        </form>
    </div>
    {% elif request.method == 'POST' and not error and search_type %}
    <div class="result">
        <p>No results found for the specified criteria.</p>
    </div>
    {% endif %}
</body>
</html>
        ''')
    
    app.run(debug=True, host='0.0.0.0', port=5055)