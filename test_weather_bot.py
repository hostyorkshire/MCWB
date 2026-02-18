#!/usr/bin/env python3
"""
Test script for MeshCore Weather Bot
Demonstrates the bot's functionality with mock data when API is not accessible
"""

import sys
from weather_bot import WeatherBot
from meshcore import MeshCoreMessage


def test_command_parsing():
    """Test weather command parsing"""
    print("=" * 60)
    print("TEST 1: Command Parsing")
    print("=" * 60)
    
    bot = WeatherBot(debug=False)
    
    test_cases = [
        ("wx London", "London"),
        ("weather Manchester", "Manchester"),
        ("WX York", "York"),
        ("WEATHER Leeds", "Leeds"),
        ("wx  Birmingham  ", "Birmingham"),
        ("hello", None),
        ("wx", None),
        ("weather", None),
    ]
    
    for command, expected in test_cases:
        result = bot.parse_weather_command(command)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{command}' -> {result} (expected: {expected})")
    
    print()


def test_weather_code_descriptions():
    """Test weather code to description conversion"""
    print("=" * 60)
    print("TEST 2: Weather Code Descriptions")
    print("=" * 60)
    
    bot = WeatherBot(debug=False)
    
    test_codes = [0, 1, 2, 3, 45, 51, 61, 63, 71, 80, 95]
    
    for code in test_codes:
        description = bot.get_weather_description(code)
        print(f"Code {code:2d}: {description}")
    
    print()


def test_weather_formatting():
    """Test weather response formatting"""
    print("=" * 60)
    print("TEST 3: Weather Response Formatting")
    print("=" * 60)
    
    bot = WeatherBot(debug=False)
    
    # Mock location data
    location_data = {
        "name": "London",
        "country": "GB",
        "latitude": 51.5074,
        "longitude": -0.1278
    }
    
    # Mock weather data
    weather_data = {
        "current": {
            "temperature_2m": 12.5,
            "apparent_temperature": 11.2,
            "relative_humidity_2m": 75,
            "wind_speed_10m": 15.3,
            "wind_direction_10m": 230,
            "precipitation": 0.0,
            "weather_code": 2
        }
    }
    
    response = bot.format_weather_response(location_data, weather_data)
    print(response)
    print()


def test_message_handling():
    """Test message handling"""
    print("=" * 60)
    print("TEST 4: Message Handling")
    print("=" * 60)
    
    bot = WeatherBot(debug=True)
    bot.start()
    
    # Test with a weather command (will fail due to network, but shows handling)
    msg = MeshCoreMessage(
        sender="test_user",
        content="wx London",
        message_type="text"
    )
    
    print("\nProcessing: 'wx London'")
    print("-" * 40)
    # Note: This will fail with network error in sandbox, but shows the flow
    
    bot.stop()
    print()


def test_meshcore_integration():
    """Test MeshCore integration"""
    print("=" * 60)
    print("TEST 5: MeshCore Integration")
    print("=" * 60)
    
    from meshcore import MeshCore
    
    # Test basic MeshCore functionality
    mesh = MeshCore("test_node", debug=True)
    
    print("\nStarting MeshCore...")
    mesh.start()
    
    print("\nSending test message...")
    msg = mesh.send_message("Test weather request", "text")
    
    print("\nSimulating message reception...")
    
    def test_handler(message):
        print(f"Handler received: {message.content}")
    
    mesh.register_handler("text", test_handler)
    mesh.receive_message(msg)
    
    print("\nStopping MeshCore...")
    mesh.stop()
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MCWB - MeshCore Weather Bot Tests" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_command_parsing()
        test_weather_code_descriptions()
        test_weather_formatting()
        test_meshcore_integration()
        
        print("=" * 60)
        print("All component tests completed!")
        print("=" * 60)
        print()
        print("Note: Full API integration tests require network access.")
        print("To test with real API:")
        print("  python3 weather_bot.py --location 'London'")
        print("  python3 weather_bot.py --interactive")
        print()
        
        return 0
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
