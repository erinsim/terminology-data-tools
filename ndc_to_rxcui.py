import requests

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

if __name__ == "__main__":
    ndc = input("Enter the NDC: ")
    try:
        rxcui = ndc_to_rxcui(ndc)
        print(f"The RXCUI for NDC {ndc} is {rxcui}")
    except Exception as e:
        print(e)        from flask import Flask, request, render_template_string
        import requests
        
        app = Flask(__name__)
        
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
        
        @app.route('/', methods=['GET', 'POST'])
        def index():
            rxcui = None
            error = None
            if request.method == 'POST':
                ndc = request.form['ndc']
                try:
                    rxcui = ndc_to_rxcui(ndc)
                except Exception as e:
                    error = str(e)
            return render_template_string('''
                <!doctype html>
                <title>NDC to RXCUI Converter</title>
                <h1>NDC to RXCUI Converter</h1>
                <form method=post>
                    <label for=ndc>NDC:</label>
                    <input type=text name=ndc>
                    <input type=submit value=Convert>
                </form>
                {% if rxcui %}
                    <h2>The RXCUI for NDC {{ ndc }} is {{ rxcui }}</h2>
                {% elif error %}
                    <h2>Error: {{ error }}</h2>
                {% endif %}
            ''', rxcui=rxcui, error=error)
        
        if __name__ == "__main__":
            app.run(debug=True)