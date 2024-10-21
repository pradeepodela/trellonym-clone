import sys
sys.path.insert(0, './lib')
import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import os
import zcatalyst_sdk
import logging

# Catalyst configuration
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.debug = True  # Enable debug mode for Flask
# app = zcatalyst_sdk.initialize()
#Get Data Store component instance 

# Static admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Catalyst table details
tableName = 'Messages'
columnName = 'message_content'

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def convert_time(entry):
    return datetime.datetime.strptime(entry['MODIFIEDTIME'], '%Y-%m-%d %H:%M:%S:%f')


# Home page (User page)
@app.route('/')
def index():
    return render_template('user.html')

# Submit anonymous message
@app.route('/submit', methods=['POST'])
def submit_message():
    # try:
        # Initialize Catalyst app
        # logger.info("Initializing Catalyst SDK")
        app = zcatalyst_sdk.initialize(req=request)
        # logger.info("Initialized Catalyst SDK")

        table = app.datastore().table(tableName)
        # logger.info("checking table{}".format(table))
        # print('ceheck point 1 initailized{}'.format(table))
        message = request.form.get('message')

        # logger.info(f"Received message: {message}")
        # print('ceheck point 2 message{}'.format(message))
  
        row = table.insert_row({columnName: message})
        # print('ceheck point 3 row{}'.format(row))
        # logger.debug(f"Inserted row: {row}")
        return redirect(url_for('index'))
        

      

# Admin login
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template('login.html')

# Admin Dashboard - View Anonymous Messages
@app.route('/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    try:
        logger.info("Fetching messages for admin")

        # Initialize Catalyst app
        app = zcatalyst_sdk.initialize(req=request)
       
        # Fetch all messages from Catalyst Data Store
        table = app.datastore().table(tableName)
        rows = table.get_paged_rows(None, max_rows=100)

        # Sort rows based on MODIFIEDTIME
        sorted_rows = sorted(rows['data'], key=convert_time, reverse=True)

        # Extract message_content and CREATEDTIME from sorted rows
        messages = [{'content': row['message_content'], 'created_time': row['CREATEDTIME']} for row in sorted_rows]

        # logger.info(f"Fetched messages: {messages}")

        return render_template('admin.html', messages=messages)

    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return jsonify({"message": f"Internal server error Error fetching messages: {str(e)}"}), 500

# Admin logout
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# Helper function to check if the message exists
def getMessageFromCatalystDataStore(request, message):
    try:
        logger.info(f"Querying message: {message}")
        capp = zcatalyst_sdk.initialize(req=request)
        zcql_service = capp.zcql()
        query = f"SELECT * FROM {tableName} WHERE {columnName} = '{message}'"
        output = zcql_service.execute_query(query)
        logger.debug(f"Query result: {output}")
        return output
    except Exception as e:
        logger.error(f"Error querying message from Catalyst: {str(e)}")
        return []

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('X_ZOHO_CATALYST_LISTEN_PORT', 9000))
    app.run(host='0.0.0.0', port=port)
