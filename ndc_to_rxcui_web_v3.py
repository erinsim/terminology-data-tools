import http.server
import socketserver
import urllib.parse
import requests
import json

# Define the port number for the server
PORT = 8080  # Change the port number here if needed

# Function to convert NDC to RXCUI using the RxNorm API
def ndc_to_rxcui(ndc):
    url = f"https://rxnav.nlm.nih.gov/REST/ndcstatus.json?ndc={ndc}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()
    
    if 'ndcStatus' in data and 'rxcui' in data['ndcStatus']:
        return data['ndcStatus']['rxcui'], url
    else:
        raise Exception("RXCUI not found for the given NDC")

# Function to get RXCUI information using the RxNorm API
def get_rxcui_info(rxcui):
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()
    
    if 'properties' in data:
        return data['properties'], url
    else:
        raise Exception("Properties not found for the given RXCUI")

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
                <title>NDC to RXCUI Converter</title>
                <style>
                    body {
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <h1>NDC to RXCUI Converter</h1>
                <form method="post">
                    <label for="ndc" title="National Drug Code (NDC) is a unique identifier for medicines in the United States.">NDC:</label>
                    <input type="text" name="ndc">
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
        if self.path == "/download_json":
            self.do_POST_download_json()
        else:
            self.do_POST_convert()

    # Handle POST requests for conversion
    def do_POST_convert(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        params = urllib.parse.parse_qs(post_data.decode('utf-8'))
        ndc = params.get('ndc', [None])[0]
        show_urls = 'show_urls' in params

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        try:
            rxcui, ndc_url = ndc_to_rxcui(ndc)
            properties, rxcui_url = get_rxcui_info(rxcui)
            result = {
                "ndc": ndc,
                "rxcui": rxcui,
                "term_type": properties['tty'],
                "name": properties['name'],
                "ndc_url": ndc_url,
                "rxcui_url": rxcui_url
            }
            response = f'''
                <!doctype html>
                <html>
                <head>
                    <title>NDC to RXCUI Converter</title>
                    <style>
                        body {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <h1>NDC to RXCUI Converter</h1>
                    <form method="post">
                        <label for="ndc" title="National Drug Code (NDC) is a unique identifier for medicines in the United States.">NDC:</label>
                        <input type="text" name="ndc">
                        <br>
                        <input type="checkbox" name="show_urls" value="yes" {'checked' if show_urls else ''}>
                        <label for="show_urls">Show API URLs</label>
                        <br>
                        <input type="submit" value="Convert">
                    </form>
                    <form method="post" action="/download_json">
                        <input type="hidden" name="ndc" value="{ndc}">
                        <input type="hidden" name="rxcui" value="{rxcui}">
                        <input type="hidden" name="term_type" value="{properties['tty']}">
                        <input type="hidden" name="name" value="{properties['name']}">
                        <input type="hidden" name="ndc_url" value="{ndc_url}">
                        <input type="hidden" name="rxcui_url" value="{rxcui_url}">
                        <input type="submit" value="Download Results as JSON">
                    </form>
                    <h2>The RXCUI for NDC {ndc} is {rxcui}</h2>
                    <h3>Term Type (TTY): {properties['tty']}</h3>
                    <button type="button" onclick="toggleTermTypes()">Show Term Types</button>
                    <div id="termTypes" style="display:none;">
                        <p><strong>BN:</strong> Brand Name</p>
                        <p><strong>IN:</strong> Ingredient</p>
                        <p><strong>PIN:</strong> Precise Ingredient</p>
                        <p><strong>MIN:</strong> Multiple Ingredients</p>
                        <p><strong>SCD:</strong> Semantic Clinical Drug</p>
                        <p><strong>SBD:</strong> Semantic Branded Drug</p>
                        <p><strong>GPCK:</strong> Generic Pack</p>
                        <p><strong>BPCK:</strong> Branded Pack</p>
                    </div>
                    <h3>Name: {properties['name']}</h3>
                    <p>View in RxNav: <a href="https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={rxcui}" target="_blank">RxNav Result</a></p>
            '''
            if show_urls:
                response += f'''
                    <p>API URL used for NDC: <a href="{ndc_url}" target="_blank">{ndc_url}</a></p>
                    <p>API URL used for RXCUI: <a href="{rxcui_url}" target="_blank">{rxcui_url}</a></p>
                    <p>API Documentation: <a href="https://rxnav.nlm.nih.gov/RxNormAPIs.html" target="_blank">RxNorm API Documentation</a></p>
                '''
            response += '''
                    <p><a href="https://github.com/erinsim/terminology-data-tools" target="_blank">Python Script Behind This Webpage: Terminology Data Tools Repository</a></p>
                    <script>
                        function toggleTermTypes() {
                            var x = document.getElementById("termTypes");
                            if (x.style.display === "none") {
                                x.style.display = "block";
                            } else {
                                x.style.display = "none";
                            }
                        }
                    </script>
                </body>
                </html>
            '''
        except Exception as e:
            response = f'''
                <!doctype html>
                <html>
                <head>
                    <title>NDC to RXCUI Converter</title>
                    <style>
                        body {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <h1>NDC to RXCUI Converter</h1>
                    <form method="post">
                        <label for="ndc" title="National Drug Code (NDC) is a unique identifier for medicines in the United States.">NDC:</label>
                        <input type="text" name="ndc">
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

    # Handle POST requests for downloading JSON results
    def do_POST_download_json(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        params = urllib.parse.parse_qs(post_data.decode('utf-8'))
        result = {
            "ndc": params.get('ndc', [None])[0],
            "rxcui": params.get('rxcui', [None])[0],
            "term_type": params.get('term_type', [None])[0],
            "name": params.get('name', [None])[0],
            "ndc_url": params.get('ndc_url', [None])[0],
            "rxcui_url": params.get('rxcui_url', [None])[0]
        }
        json_data = json.dumps(result)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Disposition", "attachment; filename=result.json")
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))

# Start the HTTP server
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()