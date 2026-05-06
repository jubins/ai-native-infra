"""
Listing 1.1 — A structured LLM call with Gemini.

Demonstrates the fundamental pattern of AI-native infrastructure:
send unstructured operational data to an LLM, receive structured
output back.

Run:
    export GEMINI_API_KEY="your-key"
    pip install google-generativeai==0.8.0
    python listing_1_1_structured_llm_call.py
"""
import google.generativeai as genai                              # A
import json
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])            # A
model = genai.GenerativeModel("gemini-3-flash-preview")          # B

log_line = """                                                   
2026-03-14 02:13:45 ERROR PaymentService - Timeout
waiting for response from stripe-api.internal:443.
Retry attempt 3/3 failed. Transaction tx_8f2a91
will be marked as UNKNOWN.
"""                                                              # C

prompt = f"""Analyze this log entry and return JSON
with these fields:
- severity: one of "low", "medium", "high", "critical"
- component: the service or component that produced the error
- root_cause: one-sentence summary of the likely root cause
- suggested_action: one-sentence recommended action

Log entry: {log_line}
Return only valid JSON, no markdown formatting."""

response = model.generate_content(prompt)                        # D
analysis = json.loads(response.text)                             # E
print(json.dumps(analysis, indent=2))

# A Configure the Gemini client.
# B Use Flash for cost efficiency.
# C Real infrastructure log data.
# D Send the prompt to the LLM.
# E Parse the structured response.
