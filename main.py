from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import os
from requests import get, put
import urllib.parse
import json

def run(handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

class HttpGetHandler(BaseHTTPRequestHandler):
    def get_uploaded_files(self):
        ya_folder = "Backup"
        resp = get(
            f"https://cloud-api.yandex.net/v1/disk/resources?path={urllib.parse.quote(ya_folder)}",
            headers={"Authorization": ""},
        )
        if resp.status_code == 200:
            items = json.loads(resp.text).get("_embedded", {}).get("items", [])
            return {item['name'] for item in items}
        return set()

    def do_GET(self):
        def fname2html(fname, uploaded):
            color = "rgba(0, 200, 0, 0.25)" if uploaded else "transparent"
            return f"""
                <li style=\"background-color: {color};\" onclick=\"fetch('/upload', {{'method': 'POST', 'body': '{fname}'}})\">
                    {fname}
                </li>
            """

        uploaded_files = self.get_uploaded_files()
        local_files = os.listdir("pdfs")

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(f"""
            <html>
                <head>
                </head>
                <body>
                    <ul>
                      {''.join(fname2html(fname, fname in uploaded_files) for fname in local_files)}
                    </ul>
                </body>
            </html>
        """.encode())

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        fname = self.rfile.read(content_len).decode("utf-8")
        local_path = f"pdfs/{fname}"
        ya_path = f"Backup/{urllib.parse.quote(fname)}"

        resp = get(
            f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={ya_path}",
            headers={"Authorization": ""}
        )
        print(resp.text)
        upload_url = json.loads(resp.text).get("href")

        if upload_url:
            with open(local_path, 'rb') as file_data:
                resp = put(upload_url, files={'file': (fname, file_data)})
            print(resp.status_code)

        self.send_response(200)
        self.end_headers()

run(handler_class=HttpGetHandler)
