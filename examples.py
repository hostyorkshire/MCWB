#!/usr/bin/env python3
"""
Example usage of MeshCore Weather Bot
This script demonstrates how to use the weather bot programmatically
"""

from weather_bot import WeatherBot
from meshcore import MeshCoreMessage
import time


def example_1_simple_query():
    """Example 1: Simple weather query"""
    print("=" * 60)
    print("Example 1: Simple Weather Query")
    print("=" * 60)

    bot = WeatherBot(node_id="example_bot", debug=False)
    bot.start()

    # Simulate a weather request
    message = MeshCoreMessage(
        sender="user_node",
        content="wx London",
        message_type="text"
    )

    print("\nSending: 'wx London'")
    print("-" * 40)
    bot.handle_message(message)

    bot.stop()
    print()


def example_2_multiple_locations():
    """Example 2: Query multiple locations"""
    print("=" * 60)
    print("Example 2: Multiple Location Queries")
    print("=" * 60)

    bot = WeatherBot(node_id="example_bot", debug=False)
    bot.start()

    locations = ["London", "Manchester", "Edinburgh", "Cardiff"]

    for location in locations:
        message = MeshCoreMessage(
            sender="user_node",
            content=f"wx {location}",
            message_type="text"
        )

        print(f"\n{'=' * 40}")
        print(f"Query: wx {location}")
        print('=' * 40)
        bot.handle_message(message)
        time.sleep(1)  # Small delay between requests

    bot.stop()
    print()


def example_3_command_variations():
    """Example 3: Different command formats"""
    print("=" * 60)
    print("Example 3: Command Format Variations")
    print("=" * 60)

    bot = WeatherBot(node_id="example_bot", debug=False)
    bot.start()

    commands = [
        "wx York",
        "weather Leeds",
        "WX Bristol",
        "WEATHER Cambridge",
    ]

    for command in commands:
        message = MeshCoreMessage(
            sender="user_node",
            content=command,
            message_type="text"
        )

        print(f"\n{'=' * 40}")
        print(f"Command: '{command}'")
        print('=' * 40)
        bot.handle_message(message)
        time.sleep(1)

    bot.stop()
    print()


def example_4_custom_handler():
    """Example 4: Custom message handler"""
    print("=" * 60)
    print("Example 4: Custom Message Handler")
    print("=" * 60)

    from meshcore import MeshCore

    mesh = MeshCore("custom_node", debug=False)

    def custom_weather_handler(message):
        """Custom handler that processes weather responses"""
        print(f"\n📡 Received from {message.sender}:")
        print("-" * 40)
        print(message.content)
        print("-" * 40)

    mesh.register_handler("text", custom_weather_handler)
    mesh.start()

    # Simulate receiving a weather response
    response = MeshCoreMessage(
        sender="weather_bot",
        content="London, GB\nCond: Partly cloudy\nTemp: 12°C",
        message_type="text"
    )

    mesh.receive_message(response)

    mesh.stop()
    print()


def example_5_error_handling():
    """Example 5: Error handling"""
    print("=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)

    bot = WeatherBot(node_id="example_bot", debug=True)
    bot.start()

    # Test with invalid commands
    invalid_commands = [
        "hello",  # Not a weather command
        "wx",     # Missing location
        "weather",  # Missing location
    ]

    for command in invalid_commands:
        message = MeshCoreMessage(
            sender="user_node",
            content=command,
            message_type="text"
        )

        print(f"\nTesting: '{command}'")
        print("-" * 40)
        bot.handle_message(message)

    bot.stop()
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "MeshCore Weather Bot - Usage Examples" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    print("Note: These examples demonstrate the bot's functionality.")
    print("API calls may fail in environments without internet access.")
    print()

    try:
        # Run examples
        example_4_custom_handler()  # This one works without API
        example_5_error_handling()  # This one shows command parsing

        # Uncomment to run API-dependent examples (requires internet):
        # example_1_simple_query()
        # example_2_multiple_locations()
        # example_3_command_variations()

        print("=" * 60)
        print("Examples completed!")
        print("=" * 60)
        print("\nTo run with real API access, uncomment the API examples")
        print("in the main() function.")
        print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
