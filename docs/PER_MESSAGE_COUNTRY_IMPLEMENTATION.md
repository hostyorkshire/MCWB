# Per-Message Country Specification - Implementation Summary

## Problem Statement
Users requested the ability to specify country directly in their weather commands instead of configuring a default country at bot startup. This addresses the issue where ambiguous city names (like York, Paris, Birmingham) might return results from the wrong country.

**User Request:**
> "Some of my users are in the UK and when they request a town sometimes it's in the USA. Eg. York. would we add an extra command for the bot? eg. wx york uk, eg. york USA"

## Solution
Implemented per-message country specification that allows users to append a country code to their weather query.

### User Experience

**Before:**
- User: `wx York` → Bot returns York, Pennsylvania USA (wrong city for UK users)
- Only solution: Configure bot with `--country GB` at startup (affects all users)

**After:**
- User: `wx York UK` → Bot returns York, United Kingdom ✓
- User: `wx York USA` → Bot returns York, Pennsylvania USA ✓
- Users can override any default country setting per query

## Implementation Details

### 1. Updated Command Parser
Modified `_parse_command()` method in `weather_bot.py` to extract optional country from the end of location strings:

**Supported formats:**
- `wx York UK` → Extracts location="York", country="GB"
- `wx York USA` → Extracts location="York", country="US"
- `wx Paris FR` → Extracts location="Paris", country="FR"
- `wx New York USA` → Extracts location="New York", country="US" (multi-word cities)
- `wx York, UK` → Preserves location="York, UK", country=None (comma format)

**Country code mapping:**
- Common variations: `UK`→`GB`, `USA`→`US`, `United Kingdom`→`GB`, `United States`→`US`
- Any ISO-3166-1 alpha-2 code (2 letters): `FR`, `DE`, `CA`, `JP`, `AU`, etc.
- Case-insensitive: `uk`, `UK`, `Uk` all work

### 2. Enhanced Geocoding
Updated `geocode_location()` method to accept per-query country override:
- Per-query country takes precedence over bot's default `--country` setting
- Maintains full backward compatibility

### 3. Updated Call Chain
Modified methods to pass country parameter through:
- `handle_message()` → extracts country from command
- `_get_weather()` → passes country to geocoding
- `geocode_location()` → uses country in API request

## Code Changes

### Key Files Modified
1. **weather_bot.py** (~70 lines changed)
   - Enhanced `_parse_command()` method with country extraction
   - Updated `geocode_location()` to accept country override
   - Modified `_get_weather()` and `handle_message()` signatures

2. **test_per_message_country.py** (new file, ~300 lines)
   - Comprehensive test suite with 10 test cases
   - Tests parsing, API calls, overrides, edge cases

3. **test_weather_bot.py** (updated)
   - Updated to handle new tuple return from `parse_weather_command()`

4. **README.md** (updated)
   - New "Specifying Country in Your Query" section
   - Enhanced troubleshooting with per-message solution
   - Updated command examples

## Testing

### New Test Suite (`test_per_message_country.py`)
✅ **10 comprehensive tests:**
1. Parse UK country code
2. Parse USA country code
3. Parse US country code
4. Parse without country
5. Parse comma-separated format
6. Weather request with UK
7. Weather request with USA (override default)
8. Case-insensitive parsing
9. ISO country codes (FR, DE, CA, JP, AU)
10. Edge cases (multi-word cities, commas)

### Backward Compatibility Tests
✅ All existing tests pass:
- `test_country_filter.py` - Bot-level country filter still works
- `test_york_ambiguity.py` - Demonstrates problem and solution
- `test_weather_bot.py` - Core functionality unchanged

### Security Testing
✅ CodeQL scan: **0 vulnerabilities found**

## Usage Examples

### Basic Usage
```
User: wx York UK
Bot:  York, GB
      Partly cloudy
      Temp: 12.5°C (feels 10.8°C)
      ...

User: wx York USA
Bot:  York, US
      Clear sky
      Temp: 22.5°C (feels 21.2°C)
      ...
```

### With Default Country Setting
```bash
# Start bot with UK as default
python3 weather_bot.py --country GB
```

**User queries:**
- `wx York` → Returns York, UK (uses default)
- `wx York USA` → Returns York, USA (overrides default)
- `wx Paris` → Returns Paris, UK if exists, else France
- `wx Paris FR` → Returns Paris, France (overrides default)

### All Supported Formats
```
wx York           # No country (uses default or first match)
wx York UK        # UK variations: UK, GB, United Kingdom
wx York USA       # US variations: USA, US, United States
wx Paris FR       # Any ISO-3166-1 alpha-2 code
wx Berlin DE
wx Toronto CA
wx Tokyo JP
wx Sydney AU
wx New York USA   # Multi-word cities work
wx York, UK       # Comma format preserved (no extraction)
```

## Benefits

### 1. User Convenience
- ✅ Users can disambiguate city names directly in their query
- ✅ No need to remember full city names or states
- ✅ Simple, intuitive syntax
- ✅ Works for any country in the world

### 2. Flexibility
- ✅ Per-query override of default country
- ✅ Works with or without `--country` flag
- ✅ Multiple formats supported (space-separated, comma-separated)

### 3. Backward Compatibility
- ✅ Existing commands still work (`wx London`)
- ✅ Existing `--country` flag still works
- ✅ No breaking changes to API or behavior

### 4. Global Support
- ✅ Supports all ISO-3166-1 alpha-2 country codes
- ✅ Common variations mapped (UK→GB, USA→US)
- ✅ Case-insensitive

## Edge Cases Handled

### Multi-word Cities
```
wx New York USA → Correctly extracts "New York" + "US"
wx Los Angeles USA → Correctly extracts "Los Angeles" + "US"
```

### Comma-Separated Format
```
wx York, UK → Preserves "York, UK" (no country extraction)
wx Washington, D.C. → Preserves "Washington, D.C."
```

### Case Variations
```
wx York uk → Works (converts to GB)
wx York UK → Works (converts to GB)
wx York Uk → Works (converts to GB)
```

### ISO Codes
```
wx Paris FR → Works (France)
wx Paris fr → Works (France, case-insensitive)
```

## Documentation

### README Updates
1. **Overview section** - Highlighted new feature
2. **Usage section** - Added "Specifying Country in Your Query" subsection
3. **Troubleshooting** - Per-message solution now option #1
4. **Examples** - Show UK, USA, and ISO code usage

### Test Documentation
- Comprehensive inline comments in test files
- Clear test case descriptions
- Example outputs for verification

## API Compatibility

### Open-Meteo Geocoding API
The implementation leverages the existing `country` parameter support:
```
https://geocoding-api.open-meteo.com/v1/search?name=York&country=GB
```

**How it works:**
1. User sends: `wx York UK`
2. Bot parses: location="York", country="GB"
3. Bot calls API with: `?name=York&country=GB`
4. API returns: York, United Kingdom (first match in GB)

## Minimal Changes Principle

This implementation follows the principle of **minimal, surgical changes**:

**Code Changes:**
- ✅ Only 3 methods modified in core bot
- ✅ ~70 lines changed in weather_bot.py
- ✅ No changes to MeshCore protocol or networking
- ✅ No changes to weather API integration

**Backward Compatibility:**
- ✅ Zero breaking changes
- ✅ All existing functionality preserved
- ✅ Optional feature (works without country specification)

## Security Considerations

### Input Validation
- ✅ Country codes limited to 2-letter ISO codes or mapped variations
- ✅ No arbitrary text accepted as country code
- ✅ Regex-based parsing prevents injection

### No New Attack Vectors
- ✅ Country parameter passed to trusted API (Open-Meteo)
- ✅ No command execution or file system access
- ✅ Input sanitization same as before

### CodeQL Analysis
- ✅ 0 vulnerabilities found
- ✅ No security warnings
- ✅ Clean code review

## Future Enhancements (Optional)

Potential future improvements (not required for this feature):
1. Support for 3-letter ISO country codes (USA, GBR, FRA)
2. Natural language country names (e.g., "wx York England")
3. State/region specification (e.g., "wx York Yorkshire")
4. Multiple result options when ambiguous

## Conclusion

✅ **Feature Complete**
- Implements user-requested functionality exactly as specified
- Supports both "wx York UK" and "wx York USA" formats
- Works with any ISO country code

✅ **Quality Assured**
- 10 comprehensive test cases
- All existing tests pass
- Security scan clean

✅ **Well Documented**
- README updated with examples
- Implementation documented
- Code comments clear

✅ **Production Ready**
- Minimal code changes
- Backward compatible
- No breaking changes

The per-message country specification feature is now fully implemented, tested, and ready for use!
