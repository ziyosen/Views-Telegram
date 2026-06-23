# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS          
from threading import Thread, active_count
from time import sleep as swait
from auto_proxy import Proxy
from telegram import Api
from utilitys import *
import uuid

app = Flask(__name__)
CORS(app)                            

# Dictionary untuk menyimpan state per session
sessions = {}

# -------------------- FUNGSI PER SESSION --------------------
def view_updater(session_id):
    session = sessions[session_id]
    while session['running']:
        try:
            Api.views(session['api_instance'])
            swait(2)
        except Exception as e:
            logger(e)

def send_views(session_id):
    session = sessions[session_id]
    while session['running']:
        threads = []
        session['proxy_manager'].init()
        for proxy_type, proxy in session['proxy_manager'].proxies:
            while active_count() > THREADS:
                swait(0.05)
            thread = Thread(
                target=session['api_instance'].send_view,
                args=(proxy, proxy_type)
            )
            thread.daemon = True
            threads.append(thread)
            thread.start()
        for t in threads:
            t.join()

# -------------------- ENDPOINT API --------------------
@app.route('/create_session', methods=['POST'])
def create_session():
    """Buat session baru, return session_id"""
    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = {
        'running': False,
        'channel': None,
        'post': None,
        'api_instance': None,
        'proxy_manager': None,
        'views': 0,
        'token_errors': 0,
        'proxy_errors': 0,
    }
    return jsonify({'session_id': session_id})

@app.route('/status')
def status():
    session_id = request.args.get('session_id')
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Session tidak valid.'}), 400
    
    session = sessions[session_id]
    api = session['api_instance']
    
    return jsonify({
        'running': session['running'],
        'channel': session['channel'],
        'post': session['post'],
        'views': api.real_views if api else 0,
        'token_errors': api.token_errors if api else 0,
        'proxy_errors': api.proxy_errors if api else 0,
        'active_threads': active_count()
    })

@app.route('/start', methods=['POST'])
def start_bot():
    data = request.get_json()
    session_id = data.get('session_id')
    channel = data.get('channel')
    post = data.get('post')
    
    if not session_id or session_id not in sessions:
        return jsonify({'message': 'Session tidak valid.'}), 400
    if not channel or not post:
        return jsonify({'message': 'Channel dan post diperlukan.'}), 400
    
    session = sessions[session_id]
    if session['running']:
        return jsonify({'message': 'Bot sudah berjalan.'}), 400

    session['channel'] = channel
    session['post'] = post

    # Reset counter per session
    Api.real_views = 0
    Api.token_errors = 0
    Api.proxy_errors = 0
    Api.success_views = 0

    http_src, socks4_src, socks5_src = config_loader()
    session['proxy_manager'] = Proxy(
        http_sources=http_src,
        socks4_sources=socks4_src,
        socks5_sources=socks5_src
    )
    session['api_instance'] = Api(channel=channel, post=post)

    session['running'] = True
    Thread(target=view_updater, args=(session_id,), daemon=True).start()
    Thread(target=send_views, args=(session_id,), daemon=True).start()
    return jsonify({'message': f'Bot dimulai untuk @{channel}/{post}'})

@app.route('/stop', methods=['POST'])
def stop_bot():
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'message': 'Session tidak valid.'}), 400
    
    session = sessions[session_id]
    if not session['running']:
        return jsonify({'message': 'Bot belum berjalan.'}), 400
    
    session['running'] = False
    
    # Reset counter
    if session['api_instance']:
        session['api_instance'].real_views = 0
        session['api_instance'].token_errors = 0
        session['api_instance'].proxy_errors = 0
        session['api_instance'].success_views = 0
    Api.real_views = 0
    Api.token_errors = 0
    Api.proxy_errors = 0
    Api.success_views = 0
    
    return jsonify({'message': 'Bot dihentikan.'})

if __name__ == '__main__':
    print(LOGO)
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
