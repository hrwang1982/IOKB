import json

# Simulated response from the logs
response_json = """
{
    "status_code": 200, 
    "request_id": "1f62bfb91ca047ecadbe40a5e832d762", 
    "code": "", 
    "message": "", 
    "output": {
        "sentence": [
            {
                "sentence_id": 1, 
                "begin_time": 5360, 
                "end_time": 44380, 
                "text": "好，各位媒体朋友大家上午好。", 
                "channel_id": 0, 
                "speaker_id": null, 
                "sentence_end": true
            }
        ]
    }
}
"""

def parse_response(response_data):
    text = ""
    # Original logic
    if "sentences" in response_data:
        for sentence in response_data["sentences"]:
            text += sentence.get("text", "")
    elif "text" in response_data:
        text += response_data["text"]
    
    return text

def parse_response_fixed(response_data):
    text = ""
    # Fixed logic
    if "sentences" in response_data:
        for sentence in response_data["sentences"]:
            text += sentence.get("text", "")
    elif "sentence" in response_data:  # Handle singular 'sentence'
        for sentence in response_data["sentence"]:
            text += sentence.get("text", "")
    elif "text" in response_data:
        text += response_data["text"]
    
    return text

data = json.loads(response_json)
output = data.get("output", {})

print("Original Logic Result:")
original_result = parse_response(output)
print(f"'{original_result}'")

print("\nFixed Logic Result:")
fixed_result = parse_response_fixed(output)
print(f"'{fixed_result}'")

expected_text_start = "好，各位媒体朋友大家上午好。"
if fixed_result.startswith(expected_text_start):
    print("\nSUCCESS: Fixed logic correctly extracted the text.")
else:
    print("\nFAILURE: Fixed logic failed to extract text.")
