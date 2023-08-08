import requests
import json

url = "https://api.vectara.io/v1/query"

payload = json.dumps({
  "query": [
    {
      "query": "How can I colorize an ICON from NED?",
      "start": 0,
      "numResults": 10,
      "contextConfig": {
        "charsBefore": 30,
        "charsAfter": 30,
        "sentencesBefore": 3,
        "sentencesAfter": 3,
        "startTag": "<b>",
        "endTag": "</b>"
      },
      "corpusKey": [
        {
          "customerId": 0,
          "corpusId": 1,
          "semantics": "DEFAULT",
          "dim": [
            {
              "name": "string",
              "weight": 0
            }
          ],
          "metadataFilter": "part.lang = 'eng'",
          "lexicalInterpolationConfig": {
            "lambda": 0
          }
        }
      ],
      "rerankingConfig": {
        "rerankerId": 272725717
      },
      "summary": [
        {
          "summarizerPromptName": "string",
          "maxSummarizedResults": 0,
          "responseLang": "string"
        }
      ]
    }
  ]
})
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'customer-id': '3477902017',
  'x-api-key': 'zwt_z0ySwQpfdrAjiNbz27T0S7cN51TaMIWj0Mb28Q'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.content)