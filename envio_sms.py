import requests, base64, json

userToken = "gerencia@crea-online.co:Byg6JbjNicHdhX6BS3rzEREBuDwpj0UL"
credentials = (base64.b64encode(userToken.encode()).decode())

url = "https://api.labsmobile.com/json/send"

payload = json.dumps({
 "message": "Probando API SMS LabsMobile",
 "tpoa": "Sender",
 "recipient": [
   {
     "msisdn": "573102718763"
   }
 ]
})
headers = {
 'Content-Type': 'application/json',
 'Authorization': 'Basic %s' % credentials,
 'Cache-Control': "no-cache"
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
              