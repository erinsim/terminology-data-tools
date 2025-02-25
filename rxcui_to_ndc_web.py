import http.server
import socketserver
import urllib.parse
import requests
import json

# Define the port number for the server
PORT = 8081  # Change the port number here if needed

# Function to convert RXCUI to NDC using the RxNorm API
def rxcui_to_ndc(rxcui):
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/ndcs.json"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()
    
    if 'ndcGroup' in data and 'ndcList' in data['ndcGroup'] and 'ndc' in data['ndcGroup']['ndcList']:
        ndcs = data['ndcGroup']['ndcList']['ndc']
        ndc_names = []
        for ndc in ndcs:
            ndc_name = get_ndc_name(ndc)
            ndc_names.append((ndc, ndc_name))
        return ndc_names, url
    else:
        raise Exception("NDC not found for the given RXCUI")

# Function to get the drug name for a given NDC using the RxNorm API
def get_ndc_name(ndc):
    url = f"https://rxnav.nlm.nih.gov/REST/ndcstatus.json?ndc={ndc}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return "Unknown"
    
    data = response.json()
    
    if 'ndcStatus' in data and 'active' in data['ndcStatus'] and 'name' in data['ndcStatus']['active']:
        return data['ndcStatus']['active']['name']
    else:
        return "Unknown"

# Define a request handler class for the HTTP server
class MyHandler(http.server.SimpleHTTPRequestHandler):
    # Handle GET requests
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b'''
            <!doctype html>
            <html>
            <head>
                <title>RXCUI to NDC Converter</title>
                <style>
                    body {
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <h1>RXCUI to NDC Converter</h1>
                <form method="post">
                    <label for="rxcui" title="RXCUI is a unique identifier for drugs in the RxNorm database.">RXCUI:</label>
                    <input type="text" name="rxcui">
                    <br>
                    <input type="checkbox" name="show_urls" value="yes">
                    <label for="show_urls">Show API URLs</label>
                    <br>
                    <input type="submit" value="Convert">
                </form>
                <p><a href="https://github.com/your-username/terminology-data-tools" target="_blank">Python Script Behind This Webpage: Terminology Data Tools Repository</a></p>
            </body>
            </html>
        ''')

    # Handle POST requests
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        params = urllib.parse.parse_qs(post_data.decode('utf-8'))
        rxcui = params.get('rxcui', [None])[0]
        show_urls = 'show_urls' in params

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        try:
            ndc_names, api_url = rxcui_to_ndc(rxcui)
            response = f'''
                <!doctype html>
                <html>
                <head>
                    <title>RXCUI to NDC Converter</title>
                    <style>
                        body {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <h1>RXCUI to NDC Converter</h1>
                    <form method="post">
                        <label for="rxcui" title="RXCUI is a unique identifier for drugs in the RxNorm database.">RXCUI:</label>
                        <input type="text" name="rxcui">
                        <br>
                        <input type="checkbox" name="show_urls" value="yes" {'checked' if show_urls else ''}>
                        <label for="show_urls">Show API URLs</label>
                        <br>
                        <input type="submit" value="Convert">
                    </form>
                    <h2>The NDCs for RXCUI {rxcui} are:</h2>
                    <ul>
            '''
            for ndc, name in ndc_names:
                response += f'<li>{ndc} - {name}</li>'
            response += '</ul>'
            if show_urls:
                response += f'''
                    <p>API URL used: <a href="{api_url}" target="_blank">{api_url}</a></p>
                    <p>API Documentation: <a href="https://rxnav.nlm.nih.gov/RxNormAPIs.html" target="_blank">RxNorm API Documentation</a></p>
                '''
            response += '''
                <p><a href="https://github.com/your-username/terminology-data-tools" target="_blank">Python Script Behind This Webpage: Terminology Data Tools Repository</a></p>
                </body>
                </html>
            '''
        except Exception as e:
            response = f'''
                <!doctype html>
                <html>
                <head>
                    <title>RXCUI to NDC Converter</title>
                    <style>
                        body {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <h1>RXCUI to NDC Converter</h1>
                    <form method="post">
                        <label for="rxcui" title="RXCUI is a unique identifier for drugs in the RxNorm database.">RXCUI:</label>
                        <input type="text" name="rxcui">
                        <br>
                        <input type="checkbox" name="show_urls" value="yes" {'checked' if show_urls else ''}>
                        <label for="show_urls">Show API URLs</label>
                        <br>
                        <input type="submit" value="Convert">
                    </form>
                    <h2>Error: {str(e)}</h2>
                    <p><a href="https://github.com/your-username/terminology-data-tools" target="_blank">Python Script Behind This Webpage: Terminology Data Tools Repository</a></p>
                </body>
                </html>
            '''
        
        self.wfile.write(response.encode('utf-8'))

# Start the HTTP server
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()