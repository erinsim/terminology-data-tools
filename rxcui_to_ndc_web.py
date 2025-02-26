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
        return data['ndcGroup']['ndcList']['ndc'], url
    else:
        raise Exception("NDC not found for the given RXCUI")

# Function to get the drug name and term type for a given RXCUI using the RxNorm API
def get_rxcui_info(rxcui):
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
    response = requests.get(url)
    
    if response.status_code != 200:
        return "Unknown", "Unknown"
    
    data = response.json()
    
    if 'properties' in data and 'name' in data['properties'] and 'tty' in data['properties']:
        return data['properties']['name'], data['properties']['tty']
    else:
        return "Unknown", "Unknown"

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
                <p><a href="https://github.com/erinsim/terminology-data-tools" target="_blank">Python Script Behind This Webpage: Terminology Data Tools Repository</a></p>
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
            ndcs, api_url = rxcui_to_ndc(rxcui)
            drug_name, term_type = get_rxcui_info(rxcui)
            ndc_list = ', '.join(ndcs)
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
                    <h2>The NDCs for RXCUI {rxcui} ({drug_name}, {term_type}) are:</h2>
                    <p>{ndc_list}</p>
            '''
            if show_urls:
                response += f'''
                    <p>API URL used: <a href="{api_url}" target="_blank">{api_url}</a></p>
                    <p>API Documentation: <a href="https://rxnav.nlm.nih.gov/RxNormAPIs.html" target="_blank">RxNorm API Documentation</a></p>
                '''
            response += '''
                <p><a href="https://github.com/erinsim/terminology-data-tools" target="_blank">Python Script Behind This Webpage: Terminology Data Tools Repository</a></p>
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
                    <p><a href="https://github.com/erinsim/terminology-data-tools" target="_blank">Python Script Behind This Webpage: Terminology Data Tools Repository</a></p>
                </body>
                </html>
            '''
        
        self.wfile.write(response.encode('utf-8'))

# Start the HTTP server
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()