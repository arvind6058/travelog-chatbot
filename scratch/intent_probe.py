"""Read-only probe of the intent classifier to confirm routing defects."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ai.intent import detect_intent, extract_destination, extract_duration, normalize_text

CASES = [
    "Where is my flight AI 582?",
    "train status",
    "running status of 17309",
    "what can you help me plan?",
    "I need to plan a vacation",
    "can you make a plan for me",
    "I want to travel to Paris",
    "What is the weather like today?",
    "how far is it from Goa Airport to Baga Beach",
    "what is your cancellation policy",
]

print(f"{'MESSAGE':<58} {'INTENT':<20} ENTITIES")
print("-" * 120)
for msg in CASES:
    intent, ents = detect_intent(msg)
    shown = {k: v for k, v in ents.items() if v is not None}
    print(f"{msg[:56]:<58} {intent.value:<20} {shown}")

print()
print("extract_destination('Hello, what can you help me with? Reply in one short sentence.') =",
      repr(extract_destination("Hello, what can you help me with? Reply in one short sentence.")))
print("extract_duration('Reply in one short sentence') =",
      repr(extract_duration("Reply in one short sentence")))
print("normalize_text('Please explain your pricing') =", repr(normalize_text("Please explain your pricing")),
      "-> contains 'plan':", "plan" in normalize_text("Please explain your pricing"))
print("'track' in 'I want to track' vs 'Where is the nearest hotel':",
      "where is" in "where is the nearest hotel in goa?")
