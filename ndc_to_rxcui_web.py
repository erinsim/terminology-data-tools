import http.server
import socketserver
import urllib.parse
import requests

PORT = 8080  # Change the port number here if needed

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

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b'''
            <!doctype html>
            <title>NDC to RXCUI Converter</title>
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
        ''')

    def do_POST(self):
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
            response = f'''
                <!doctype html>
                <title>NDC to RXCUI Converter</title>
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
            '''
            if show_urls:
                response += f'''
                    <p>API URL used for NDC: <a href="{ndc_url}" target="_blank">{ndc_url}</a></p>
                    <p>API URL used for RXCUI: <a href="{rxcui_url}" target="_blank">{rxcui_url}</a></p>
                '''
            response += '''
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
            '''
        except Exception as e:
            response = f'''
                <!doctype html>
                <title>NDC to RXCUI Converter</title>
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
            '''
        
        self.wfile.write(response.encode('utf-8'))

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()