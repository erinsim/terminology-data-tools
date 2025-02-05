import http.server
import socketserver
import urllib.parse
import requests

PORT = 8000

def ndc_to_rxcui(ndc):
    url = f"https://rxnav.nlm.nih.gov/REST/ndcstatus.json?ndc={ndc}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()
    
    if 'ndcStatus' in data and 'rxcui' in data['ndcStatus']:
        return data['ndcStatus']['rxcui']
    else:
        raise Exception("RXCUI not found for the given NDC")

def get_rxcui_info(rxcui):
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()
    
    if 'properties' in data:
        return data['properties']
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
                <label for="ndc">NDC:</label>
                <input type="text" name="ndc">
                <input type="submit" value="Convert">
            </form>
        ''')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        params = urllib.parse.parse_qs(post_data.decode('utf-8'))
        ndc = params.get('ndc', [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        try:
            rxcui = ndc_to_rxcui(ndc)
            properties = get_rxcui_info(rxcui)
            response = f'''
                <!doctype html>
                <title>NDC to RXCUI Converter</title>
                <h1>NDC to RXCUI Converter</h1>
                <form method="post">
                    <label for="ndc">NDC:</label>
                    <input type="text" name="ndc">
                    <input type="submit" value="Convert">
                </form>
                <h2>The RXCUI for NDC {ndc} is {rxcui}</h2>
                <h3>Term Type (TTY): {properties['tty']}</h3>
                <h3>Name: {properties['name']}</h3>
            '''
        except Exception as e:
            response = f'''
                <!doctype html>
                <title>NDC to RXCUI Converter</title>
                <h1>NDC to RXCUI Converter</h1>
                <form method="post">
                    <label for="ndc">NDC:</label>
                    <input type="text" name="ndc">
                    <input type="submit" value="Convert">
                </form>
                <h2>Error: {str(e)}</h2>
            '''
        
        self.wfile.write(response.encode('utf-8'))

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()