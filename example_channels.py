#!/usr/bin/env python3
"""
Example: Using MeshCore Channels
Demonstrates how to use channel broadcasting and filtering
"""

from meshcore import MeshCore, MeshCoreMessage
import time


def example_1_basic_channel_broadcast():
    """Example 1: Basic channel broadcasting"""
    print("=" * 60)
    print("Example 1: Basic Channel Broadcasting")
    print("=" * 60)
    
    mesh = MeshCore("broadcaster", debug=True)
    mesh.start()
    
    # Broadcast to different channels
    print("\n--- Broadcasting to different channels ---")
    mesh.send_message("General announcement", "text")
    mesh.send_message("Weather: Sunny today!", "text", channel="weather")
    mesh.send_message("Breaking news!", "text", channel="news")
    mesh.send_message("Emergency alert!", "text", channel="alerts")
    
    mesh.stop()
    print()


def example_2_channel_filtering():
    """Example 2: Filtering messages by channel"""
    print("=" * 60)
    print("Example 2: Channel Filtering")
    print("=" * 60)
    
    # Create a receiver that only listens to weather channel
    weather_receiver = MeshCore("weather_listener", debug=False)
    
    received_messages = []
    
    def message_handler(message):
        channel_info = f" [channel: {message.channel}]" if message.channel else " [no channel]"
        received_messages.append(f"{message.content}{channel_info}")
        print(f"  📨 Received: {message.content}{channel_info}")
    
    weather_receiver.register_handler("text", message_handler)
    weather_receiver.start()
    
    # Set filter to only receive weather channel
    print("\n--- Filtering for 'weather' channel only ---")
    weather_receiver.set_channel_filter("weather")
    
    # Create test messages on different channels
    msg_general = MeshCoreMessage("sender", "General message", "text")
    msg_weather = MeshCoreMessage("sender", "Weather update: Cloudy", "text", channel="weather")
    msg_news = MeshCoreMessage("sender", "News update", "text", channel="news")
    msg_weather2 = MeshCoreMessage("sender", "Weather update: Rain later", "text", channel="weather")
    
    # Send messages
    print("\nSending 4 messages (2 on weather channel, 2 on other channels):")
    weather_receiver.receive_message(msg_general)
    weather_receiver.receive_message(msg_weather)
    weather_receiver.receive_message(msg_news)
    weather_receiver.receive_message(msg_weather2)
    
    print(f"\nReceived {len(received_messages)} messages out of 4 (only weather channel)")
    
    # Remove filter and receive all
    print("\n--- Removing filter (receive all channels) ---")
    received_messages.clear()
    weather_receiver.set_channel_filter(None)
    
    print("\nSending same 4 messages:")
    weather_receiver.receive_message(msg_general)
    weather_receiver.receive_message(msg_weather)
    weather_receiver.receive_message(msg_news)
    weather_receiver.receive_message(msg_weather2)
    
    print(f"\nReceived {len(received_messages)} messages out of 4 (all channels)")
    
    weather_receiver.stop()
    print()


def example_3_multi_channel_system():
    """Example 3: Multi-channel communication system"""
    print("=" * 60)
    print("Example 3: Multi-Channel Communication System")
    print("=" * 60)
    
    # Create multiple nodes for different purposes
    weather_node = MeshCore("weather_station", debug=False)
    news_node = MeshCore("news_station", debug=False)
    alert_node = MeshCore("alert_station", debug=False)
    
    # Create a listener that listens to all channels
    listener = MeshCore("main_listener", debug=False)
    
    def listener_handler(message):
        channel_info = f"[{message.channel}]" if message.channel else "[broadcast]"
        print(f"  📡 {channel_info:12} {message.sender:16} -> {message.content}")
    
    listener.register_handler("text", listener_handler)
    listener.start()
    
    # Start all nodes
    weather_node.start()
    news_node.start()
    alert_node.start()
    
    print("\n--- Multi-channel broadcast system ---")
    print("Broadcasting from different stations:\n")
    
    # Broadcast from different channels
    msg1 = weather_node.send_message("Current temp: 15°C", "text", channel="weather")
    listener.receive_message(msg1)
    
    msg2 = news_node.send_message("Local event today at 3pm", "text", channel="news")
    listener.receive_message(msg2)
    
    msg3 = alert_node.send_message("Storm warning issued", "text", channel="alerts")
    listener.receive_message(msg3)
    
    msg4 = weather_node.send_message("Humidity: 65%", "text", channel="weather")
    listener.receive_message(msg4)
    
    msg5 = news_node.send_message("Sports scores updated", "text", channel="news")
    listener.receive_message(msg5)
    
    # General broadcast (no channel)
    msg6 = weather_node.send_message("System announcement", "text")
    listener.receive_message(msg6)
    
    # Stop all nodes
    weather_node.stop()
    news_node.stop()
    alert_node.stop()
    listener.stop()
    
    print()


def example_4_weather_bot_channels():
    """Example 4: Weather bot with channel support"""
    print("=" * 60)
    print("Example 4: Weather Bot with Channels")
    print("=" * 60)
    
    from weather_bot import WeatherBot
    
    print("\n--- Creating weather bot on 'weather' channel ---")
    
    # Create weather bot that broadcasts on weather channel
    bot = WeatherBot(node_id="weather_bot", debug=False, channel="weather")
    bot.start()
    
    print(f"Bot configured to broadcast on channel: {bot.channel}")
    print("Bot is now ready to respond to weather queries")
    print("Responses will be broadcast on the 'weather' channel")
    
    bot.stop()
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MeshCore Channel Usage Examples" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        example_1_basic_channel_broadcast()
        example_2_channel_filtering()
        example_3_multi_channel_system()
        example_4_weather_bot_channels()
        
        print("=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        print()
        print("Key Takeaways:")
        print("  • Channels allow organized communication streams")
        print("  • Messages can be sent with or without a channel")
        print("  • Receivers can filter messages by channel")
        print("  • Weather bot can broadcast on a specific channel")
        print()
        print("Try it yourself:")
        print("  python3 weather_bot.py --channel weather --interactive")
        print("  python3 meshcore_send.py 'Hello' --channel test")
        print()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
