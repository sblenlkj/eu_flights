I have a text file with aggregated European airport nodes.

Each line has the format:
<city, country_code>: <ICAO_code_1, ICAO_code_2, ...>

Example:
London, GB: EGLL, EGLC, EGKK

Context:
I am building a European air traffic graph and want to clean the dataset by removing military-only airports.

Task:
For every ICAO airport code in the file, determine whether the airport is:

1. military_only — military-only / air force base / naval air station / army airfield, with no regular civilian airport function
2. joint_use — joint civil-military airport or airport with meaningful civilian use
3. civilian — civilian / commercial / general aviation
4. unknown — cannot be identified confidently from reliable sources

Instructions:
- Check every ICAO code individually.
- Be conservative.
- Only classify an airport as military_only if there is clear evidence that it is military-only and not a regular civilian airport.
- Do not include joint civil-military airports in the drop list.
- If the evidence is weak, conflicting, outdated, or uncertain, classify the airport as unknown rather than guessing.
- Use reliable aviation or official airport sources where possible.
- Keep each ICAO code exactly as written in my file.
- Do not skip any airport codes.

Output format:
Return a single valid JSON object with exactly these 4 keys:

{
  "military_only": [...],
  "joint_use": [...],
  "civilian": [...],
  "unknown": [...]
}

Rules for the JSON:
- Each value must be a JSON array of ICAO codes.
- Do not include city names.
- Do not include explanations inside the arrays.
- Put each ICAO code into exactly one category.
- Do not add any extra keys.
- Do not wrap the JSON in markdown.
- The final list I should drop is the value of "military_only".