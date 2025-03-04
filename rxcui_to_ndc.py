import requests

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

# Example usage
if __name__ == "__main__":
    rxcui = input("Please enter an RXCUI: ")  # Prompt the user to input an RXCUI
    try:
        ndcs, api_url = rxcui_to_ndc(rxcui)
        print(f"The NDCs for RXCUI {rxcui} are: {ndcs}")
        print(f"API URL used: {api_url}")
    except Exception as e:
        print(f"Error: {str(e)}")