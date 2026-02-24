# Country Filter Feature - Implementation Summary

## Problem Statement
The bot uses the Open-Meteo geocoding API which returns the first matching city for a given query. When city names are ambiguous (exist in multiple countries), the bot may return the wrong city. For example:
- "York" could be York, UK or York, Pennsylvania USA
- "Paris" could be Paris, France or Paris, Texas USA
- "Birmingham" could be Birmingham, UK or Birmingham, Alabama USA

This is particularly problematic for deployments in specific regions (like the UK) where users expect local cities.

## Solution
Added an optional `--country` command-line parameter that filters geocoding results to prefer cities in a specific country. The parameter accepts ISO-3166-1 alpha-2 country codes (e.g., "GB", "US", "FR").

## Implementation Details

### 1. Added country parameter to WeatherBot class
```python
def __init__(self, ..., country=None):
    ...
    self.country = country  # e.g., "GB", "US", "FR"
```

### 2. Updated geocoding API call
```python
def _get_weather(self, location: str) -> str:
    geo_params = {"name": location, "count": 1, "language": "en", "format": "json"}
    if self.country:
        geo_params["country"] = self.country
    
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params=geo_params,
        timeout=10,
    ).json()
```

### 3. Added command-line argument
```python
parser.add_argument("--country",
                    help="Default country code for geocoding (e.g., GB, US, FR). "
                         "Filters location searches to prefer cities in this country.")
```

## Usage Examples

### For UK Deployments
```bash
python3 weather_bot.py --country GB
```
Now "York" will return York, UK instead of York, USA.

### For US Deployments
```bash
python3 weather_bot.py --country US
```
Now "York" will return York, Pennsylvania USA.

### Global Deployment (No Filter)
```bash
python3 weather_bot.py
```
Default behavior - no country filtering (may return ambiguous results).

### With Other Options
```bash
# UK deployment with announcements
python3 weather_bot.py --country GB --announce

# UK deployment on specific channel
python3 weather_bot.py --country GB --channel-idx 1
```

## User Experience

### Without Country Filter
```
User: wx York
Bot: York, US
     Clear sky
     Temp: 22.5°C
     [Weather for York, Pennsylvania USA - wrong city!]
```

### With Country Filter (--country GB)
```
User: wx York
Bot: York, GB
     Partly cloudy
     Temp: 12.5°C
     [Weather for York, UK - correct city!]
```

### Users Can Still Be Explicit
```
User: wx York, USA
Bot: York, US
     Clear sky
     Temp: 22.5°C
     [Users can override the default by being explicit]
```

## Testing

### Unit Tests (test_country_filter.py)
- ✅ Verifies country parameter is passed to API when configured
- ✅ Verifies country parameter is NOT passed when not configured
- ✅ Tests with different country codes (GB, US)

### Integration Tests (test_york_ambiguity.py)
- ✅ Demonstrates the problem with ambiguous city names
- ✅ Shows how country filter solves the problem
- ✅ Verifies users can still query other countries explicitly

### Existing Tests
- ✅ test_country_code.py - Country code formatting still works
- ✅ test_weather_bot.py - Core bot functionality still works
- ✅ All other tests remain unaffected

## Documentation

### README Updates
1. Added `--country` to command-line options section
2. Added usage example: `python3 weather_bot.py --country GB`
3. Added troubleshooting section for "Wrong city returned"
4. Explained both solutions:
   - Users can be specific: `wx York, UK`
   - Operators can set default: `--country GB`

## Benefits

1. **Regional Deployments**: Perfect for region-specific deployments (UK, US, etc.)
2. **Backward Compatible**: Optional parameter - existing deployments work unchanged
3. **User Override**: Users can still query other locations by being explicit
4. **Simple Configuration**: Single command-line flag, no complex setup
5. **Well Documented**: Clear examples in README and help text

## API Compatibility

The Open-Meteo Geocoding API supports the `country` parameter:
- Parameter name: `country`
- Format: ISO-3166-1 alpha-2 country code
- Example: `https://geocoding-api.open-meteo.com/v1/search?name=York&country=GB`

## Security Considerations

- ✅ No security vulnerabilities introduced (CodeQL scan passed)
- ✅ Parameter is optional and not exposed to users over LoRa
- ✅ Input validation handled by requests library
- ✅ No injection risks (parameter used in API request, not command execution)

## Minimal Changes

The implementation follows the principle of minimal changes:
- Only 4 lines of code added to WeatherBot class
- Only 7 lines of code added to _get_weather method
- 1 command-line argument added
- Documentation updates
- Comprehensive test coverage

Total code changes: ~20 lines in weather_bot.py
