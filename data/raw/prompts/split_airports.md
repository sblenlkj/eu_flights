You are given a text file containing ICAO airport codes, one or more codes per line.

Task:
Classify EVERY ICAO code from the file into exactly one of these 3 groups:

- small
- medium
- large

Return STRICT JSON with exactly these 3 top-level keys:
{
  "small": [...],
  "medium": [...],
  "large": [...]
}

Important requirements:
1. Use ICAO codes exactly as given in the input.
2. Every input code must appear in the output exactly once.
3. No code may be omitted.
4. No code may appear in more than one list.
5. No duplicates inside a list.
6. Output JSON only, with no commentary before or after.
7. Sort each list alphabetically.
8. If a code cannot be confidently matched, do NOT omit it. Make the best-supported classification and still include it.

Classification policy:
Use real-world airport significance and infrastructure, not arbitrary balancing.
Prefer to classify based on a combination of:
- airport type and role in the air transport system
- passenger importance / network importance
- presence of regular commercial traffic
- runway scale / infrastructure
- whether it is a major international airport, regional commercial airport, or small/local airport

Guiding interpretation:
- large:
  major international airports, primary national/capital airports, major tourist gateways, major commercial hubs, clearly high-capacity airports
- medium:
  regional commercial airports with scheduled service, meaningful but not hub-scale importance
- small:
  small local airports, minor fields, limited-service airports, small islands/remote airports, general aviation-heavy airports, airports with weak commercial importance

Quality control steps you must perform before finalizing:
- Build the union of all output lists and verify it matches the full input set exactly.
- Verify the intersection between any two lists is empty.
- Verify the total number of unique output codes equals the total number of input codes.
- Verify there are no missing ICAO codes.
- Verify there are no extra codes not present in the input.

Final output format:
Return only valid JSON:
{
  "small": ["...."],
  "medium": ["...."],
  "large": ["...."]
}

Before producing the final answer, explicitly self-check:
- count of input codes
- count of unique output codes
- missing codes = []
- duplicated-across-groups codes = []
- duplicated-within-group codes = []

But do not print that check. Only print the final JSON after all checks pass.