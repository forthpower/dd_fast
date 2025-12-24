from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/workflow', methods=['POST'])
def workflow():
    try:
        data = request.get_json()
        print('data: ', data)
        return jsonify({'message': 'success'}), 200
    except Exception as e:
        print('error: ', e)
    try:
        data = request.get_data()
        print('data: ', data)
        return jsonify({'message': 'success'}), 200
    except Exception as e:
        print('error: ', e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5027, debug=True)