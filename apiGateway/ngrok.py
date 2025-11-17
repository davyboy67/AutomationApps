import http.server
from http.server import BaseHTTPRequestHandler
import socketserver
import os
import asyncio
import socket
from aiohttp import web
from pyngrok import ngrok, conf
import threading
import traceback
import time
import socketserver
import functools

_ngrok_state = {}
_server_state = {}


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

class SingleFileHandler(BaseHTTPRequestHandler):
    file_path = None
    filename = None
    
    def do_GET(self):
        if self.path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", f"/{self.filename}")
            self.end_headers()
            return
        
        try:
            with open(self.file_path, 'rb') as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{self.filename}"')
            self.send_header('Content-Length', str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")

            self.end_headers()
            self.wfile.write(content)
            self.wfile.flush()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal server error')

def _run_ngrok_in_thread(port):
    try:
        token = os.getenv("NGROK_AUTHTOKEN")
        ngrok.set_auth_token(token)

        tunnel = ngrok.connect(port)
        _ngrok_state["tunnel"] = tunnel
        _ngrok_state["public_url"] = tunnel.public_url

    except Exception as e:
        err = str(e) or repr(e)
        print(f"Error starting ngrok tunnel: {err}")

def expose_file_via_ngrok(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        directory, filename = os.path.split(file_path)
        SingleFileHandler.file_path = file_path
        SingleFileHandler.filename = filename

        server = ReusableTCPServer(("0.0.0.0", 8080), SingleFileHandler)
        _server_state["server"] = server
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        #test
        
        print(f"Local: http://127.0.0.1:8080/{filename}")
        
        # Ngrok Tunnel
        ngrok_thread = threading.Thread(target=_run_ngrok_in_thread, args=(8080,), daemon=True)
        ngrok_thread.start()
        
        while "public_url" not in _ngrok_state:
            time.sleep(1)
            
        return _ngrok_state["public_url"]
    except Exception as e:       
        err = str(e) or repr(e)
        print(f"Error exposing file via ngrok: {err}")
        raise
    
    
def stop_ngrok_tunnel():
    if "tunnel" in _ngrok_state:
        ngrok.disconnect(_ngrok_state["public_url"])
    
    if "server" in _server_state:
        try:
            _server_state["server"].shutdown()
            _server_state["server"].server_close()
        except Exception as e:
            print(f"Error stopping server: {e}")    
        