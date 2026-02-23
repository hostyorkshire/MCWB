# Explanation: How "wx york USA" and "wx York UK" Commands Work

## Summary
**The bot DOES recognize "wx york USA" and "wx York UK" commands correctly.** This feature was implemented in PR #87 and is fully functional.

## How It Works

### 1. Command Recognition

The bot recognizes weather commands in multiple formats:
- `wx [location]`
- `weather [location]`
- `WX [location]` (case insensitive)
- `WEATHER [location]` (case insensitive)

### 2. Country Specification

Users can append a country code to their location query:

**Supported formats:**
```
wx York UK        # Returns York, United Kingdom
wx york USA       # Returns York, Pennsylvania USA  
wx York usa       # Case insensitive - works!
WX YORK UK        # All caps - works!
weather York UK   # "weather" keyword - works!
```

### 3. Code Implementation

The parsing logic is in `weather_bot.py`, function `_parse_command()` (lines 489-540):

#### Step 1: Extract Location String
```python
m = re.match(r"^(?:wx|weather)\s+(.+)$", text.strip(), re.IGNORECASE)
```
- Matches "wx" or "weather" (case insensitive)
- Captures everything after as the location string

#### Step 2: Country Code Mapping
```python
country_mappings = {
    'uk': 'GB',
    'gb': 'GB',
    'usa': 'US',
    'us': 'US',
    'united kingdom': 'GB',
    'united states': 'US',
}
```
- Maps common variations to ISO codes
- Case insensitive

#### Step 3: Extract Country from End of String
```python
words = location_str.split()
if len(words) >= 2:
    potential_country = words[-1].lower()
    
    # Check for comma-separated format first
    if ',' in last_few_words:
        return location_str, None  # Don't extract, keep as-is
    
    # Map to ISO code or use as-is if 2 letters
    if potential_country in country_mappings:
        country = country_mappings[potential_country]
        location = ' '.join(words[:-1])
        return location, country
    elif len(potential_country) == 2:
        country = potential_country.upper()
        location = ' '.join(words[:-1])
        return location, country
```

**Logic:**
1. Split location string into words
2. Check if last word could be a country code
3. If comma-separated format (e.g., "York, UK"), don't extract country
4. If last word matches known country variation, map to ISO code
5. If last word is 2 letters, assume it's an ISO country code
6. Return location without country word, and the country code

### 4. API Integration

The extracted country code is passed to the geocoding API:

```python
def geocode_location(self, location: str, country_override: str = None):
    geo_params = {"name": location, "count": 1, "language": "en", "format": "json"}
    country = country_override if country_override is not None else self.country
    if country:
        geo_params["country"] = country  # Add country filter to API request
```

When you query "wx York UK":
- Location = "York"
- Country = "GB"
- API URL: `https://geocoding-api.open-meteo.com/v1/search?name=York&country=GB`
- Returns: York, United Kingdom (latitude: 53.9599, longitude: -1.0873)

When you query "wx York USA":
- Location = "York"  
- Country = "US"
- API URL: `https://geocoding-api.open-meteo.com/v1/search?name=York&country=US`
- Returns: York, Pennsylvania USA (latitude: 39.9626, longitude: -76.7277)

## Test Results

All tests pass successfully:

### ✅ Command Parsing Tests (`test_per_message_country.py`)
```
✅ 'wx york USA' -> location='york', country='US'
✅ 'wx York UK' -> location='York', country='GB'
✅ 'wx york usa' -> location='york', country='US'
✅ 'wx YORK UK' -> location='YORK', country='GB'
✅ 'WX YORK USA' -> location='YORK', country='US'
✅ 'weather York UK' -> location='York', country='GB'
```

### ✅ York Ambiguity Tests (`test_york_ambiguity.py`)
- Without country: Returns first match (often USA)
- With country code: Returns correct city
- Can override bot's default country setting

### ✅ Integration Tests
- Full message flow works correctly
- API receives correct country parameter
- Response contains correct location

## Usage Examples

### For Users

**Query York in UK:**
```
wx York UK
wx york uk
WX YORK UK
weather York UK
```

**Query York in USA:**
```
wx York USA
wx york usa  
WX YORK USA
weather York USA
```

**Other cities:**
```
wx Paris FR        # Paris, France
wx Paris USA       # Paris, Texas USA
wx Birmingham UK   # Birmingham, UK
wx Birmingham USA  # Birmingham, Alabama USA
```

### For Bot Operators

**Option 1: No default country (users must specify)**
```bash
python3 weather_bot.py
```

**Option 2: Set default country for UK deployment**
```bash
python3 weather_bot.py --country GB
```
- Users can still override: `wx York USA` works even with `--country GB`

**Option 3: Set default country for US deployment**
```bash
python3 weather_bot.py --country US
```

## Supported Country Codes

### Common Variations
- `UK`, `uk`, `United Kingdom` → GB
- `USA`, `usa`, `US`, `us`, `United States` → US

### ISO-3166-1 Alpha-2 Codes (2 letters)
Any valid 2-letter country code works:
- `FR` - France
- `DE` - Germany (Deutschland)
- `CA` - Canada
- `JP` - Japan
- `AU` - Australia
- `IT` - Italy
- `ES` - Spain
- `CN` - China
- `IN` - India
- etc.

## Alternative Format: Comma-Separated

The traditional comma-separated format still works:
```
wx York, UK        # Parsed as location="York, UK", country=None
wx York, USA       # Parsed as location="York, USA", country=None
```

The geocoding API can interpret these, but the space-separated format (e.g., `wx York UK`) gives more control.

## Why This Feature Exists

### The Problem
Many city names exist in multiple countries:
- York (UK, USA, Canada, Australia)
- Paris (France, USA)
- Birmingham (UK, USA)
- Manchester (UK, USA)
- Leeds (UK, USA)

Without country specification, the geocoding API returns the first match, which is often:
- The most populous city with that name
- Biased toward certain countries (e.g., USA)

### The Solution
Users can specify the country directly in their query:
- Simple: Just add country code to the end
- Flexible: Works with any city name
- Override: Can override bot's default country
- Compatible: Traditional comma format still works

## Conclusion

**The feature is working correctly and has been thoroughly tested.** 

If users report that "wx york USA" or "wx York UK" doesn't work:
1. Verify they're using a recent version (PR #87 or later)
2. Check debug logs to see what the bot is parsing
3. Ensure the radio is connected and messages are being received
4. Verify the MeshCore app is subscribed to the weather channel

The code is solid, well-tested, and production-ready.
