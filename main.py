# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS          
from threading import Thread, active_count
from time import sleep as swait
from auto_proxy import Proxy
from telegram import Api
from utilitys import *

app = Flask(__name__)
CORS(app)                            

running = False
current_channel = None
current_post = None
api_instance = None
proxy_manager = None

# -------------------- FUNGSI ASLI --------------------
def view_updater():
    while running:
        try:
            Api.views(api_instance)
            swait(2)
        except Exception as e:
            logger(e)

def send_views():
    while running:
        threads = []
        proxy_manager.init()
        for proxy_type, proxy in proxy_manager.proxies:
            while active_count() > THREADS:
                swait(0.05)
            thread = Thread(
                target=api_instance.send_view,
                args=(proxy, proxy_type)
            )
            thread.daemon = True
            threads.append(thread)
            thread.start()
        for t in threads:
            t.join()

# -------------------- ENDPOINT API --------------------
@app.route('/status')
def status():
    return jsonify({
        'running': running,
        'channel': current_channel,
        'post': current_post,
        'views': Api.real_views,
        'token_errors': Api.token_errors,
        'proxy_errors': Api.proxy_errors,
        'active_threads': active_count()
    })

@app.route('/start', methods=['POST'])
def start_bot():
    global running, current_channel, current_post, api_instance, proxy_manager
    if running:
        return jsonify({'message': 'Bot sudah berjalan.'}), 400

    data = request.get_json()
    channel = data.get('channel')
    post = data.get('post')
    if not channel or not post:
        return jsonify({'message': 'Channel dan post diperlukan.'}), 400

    current_channel = channel
    current_post = post

    # Reset counter
    Api.real_views = 0
    Api.token_errors = 0
    Api.proxy_errors = 0
    Api.success_views = 0

    http_src, socks4_src, socks5_src = config_loader()
    proxy_manager = Proxy(
        http_sources=http_src,
        socks4_sources=socks4_src,
        socks5_sources=socks5_src
    )
    api_instance = Api(channel=channel, post=post)

    running = True
    Thread(target=view_updater, daemon=True).start()
    Thread(target=send_views, daemon=True).start()
    return jsonify({'message': f'Bot dimulai untuk @{channel}/{post}'})

@app.route('/stop', methods=['POST'])
def stop_bot():
    global running
    if not running:
        return jsonify({'message': 'Bot belum berjalan.'}), 400
    running = False
    
    # Reset counter
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
