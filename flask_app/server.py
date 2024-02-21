from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

#User Daten
user_list = [
            {'username': 'philipp', 'password': '12345', 'address': {'name': "Philipp Kraus",'addr1': "König-Karl-Straße 33", 'addr2': "70372 Stuttgart"}, 'puk_key': None, 'open_drinks': []}, 
            {'username': 'rico', 'password': '12345', 'address': {'name': "Rico Szodruch",'addr1': "König-Karl-Straße 33", 'addr2': "70372 Stuttgart"}, 'puk_key': None, 'open_drinks': []}
            ]

# Getränke Daten
drinks= [
            {'name': "Bier", 'price': 4.50, 'IDs': ["3B4ECE22"]}, 
            {'name': "Cola", 'price': 3.50, 'IDs': ["07C22C34"]}
        ]

#Rechnungs Daten
current_invoice_number = 1
from_addr = {
    'company_name': "PayPuk GmbH",
    'addr1': "Musterstraße 45",
    'addr2': "12345 Musterstadt"
}
iban = "DE02 5001 0517 9343 9317 83"




@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((item for item in user_list if item['username'] == username), None)
        if user != None:
            if (user['password'] == password): return redirect(url_for('dashboard', username=username))
            else: return render_template('username.html', error='Falsches Password')
        else:
            return render_template('username.html', error='Username exestiert nicht')
    return render_template('username.html')

@app.route('/dashboard/<username>', methods=['GET', 'POST'])
def dashboard(username):
    if request.method == 'POST':
        return redirect(url_for('dashboard', username=username))
    return render_template('dashboard.html', username=username)

@app.route('/data', methods=['POST'])
def receive_puk_data():
    data = request.json
    print("Received data:", data)
    esp32_id = data['esp_id']
    user = next((item for item in user_list if item['puk_key'] == esp32_id), None)
    drink = next((item for item in drinks if isinstance(item['IDs'], list) and data['rfid_id'] in item['IDs']), None)
    user_drink = {'name': drink['name'], 'price': drink['price'], 'rfid_id': data['rfid_id'], 'timestamp': datetime.now().strftime("%d.%m.%Y %H:%MUhr")}
    if(user != None and drink != None and (next((user['username'] for user in user_list if any(drink['rfid_id'] == data['rfid_id'] for drink in user['open_drinks'])), None)) == None):
        user['open_drinks'].append(user_drink)
    else:
        #Code wenn Getränk nicht gebucht werden kann
        pass
    print(user)
    return 'Data received successfully'

@app.route('/puk_id_data', methods=['POST'])
def receive_puk_id():
    data = request.json
    print("Received data:", data)
    user = next((item for item in user_list if item['username'] == data['username']), None)
    if(next((item for item in user_list if item['puk_key'] == data['esp_id']), None) == None or data['esp_id'] == None):
        user['puk_key'] = data['esp_id']
    else:
        #Puk ID schon vergeben
        pass
    print(user)
    return 'Data received successfully'

@app.route('/pay_bill', methods=['POST'])
def pay():
    global current_invoice_number
    data = request.json
    user = next((item for item in user_list if item['username'] == data['username']), None)
    if user['open_drinks']:
        date_today = datetime.today()
        due_date = date_today + timedelta(days=30)
        invoice = render_template('invoice.html',
                            date=date_today.strftime('%d.%m.%Y'),
                            from_addr=from_addr,
                            to_addr=user['address'],
                            items=user['open_drinks'],
                            total = sum(item['price'] for item in user['open_drinks']),
                            invoice_number=str(current_invoice_number).zfill(8),
                            duedate=due_date.strftime('%d.%m.%Y'),
                            iban = iban)
        user['open_drinks'] = []
        current_invoice_number +=  1
        print(user)
        return invoice
    else:
        #Keine Getränke
        return None

@app.route('/get_data/<username>', methods=['GET'])
def get_data(username):
    # Die gespeicherten Daten für den angegebenen ESP32-ID zurückgeben
    user = next((item for item in user_list if item['username'] == username), None)
    return jsonify(user)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
