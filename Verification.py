from flask import Flask, request, jsonify

app = Flask(__name__)

# Token එක සුරැකීමට තාවකාලික ගොනුවක්
@app.route('/collect', methods=['POST'])
def collect():
    data = request.json
    token = data.get('token')
    
    if token:
        # මෙතැනදී ඔබට අවශ්‍ය පරිදි Token එක සුරැකිය හැක
        # උදාහරණය: file එකක ලියා තැබීම හෝ DB එකකට යැවීම
        with open("tokens.txt", "a") as f:
            f.write(token + "\n")
        
        return jsonify({"status": "success", "message": "Token Received!"}), 200
    
    return jsonify({"status": "error", "message": "No token found"}), 400

if __name__ == '__main__':
    app.run()
