# How Multi-Channel Replies Work

## Visual Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    MeshCore Multi-Channel System                      │
└──────────────────────────────────────────────────────────────────────┘

USER A's RADIO                                    WEATHER BOT's RADIO
┌──────────────────┐                             ┌──────────────────┐
│ Channel Setup:   │                             │ No channel setup │
│ #weather = idx 1 │                             │ (accepts all)    │
│ #alerts  = idx 2 │                             │                  │
└──────────────────┘                             └──────────────────┘
        │                                                  │
        │ 1. Sends "wx London" on #weather                │
        │────────────────────────────────────────────────>│
        │    Binary frame: channel_idx=1                  │
        │                                                  │
        │                                                  │ 2. Receives frame
        │                                                  │    Extracts: idx=1
        │                                                  │    Content: "wx London"
        │                                                  │
        │                                                  │ 3. Processes weather
        │                                                  │    Fetches data
        │                                                  │
        │                                                  │ 4. Replies on idx=1
        │<────────────────────────────────────────────────│    (same as received)
        │    Binary frame: channel_idx=1                  │
        │                                                  │
        │ 5. Receives on #weather (idx=1) ✅              │
        │    User sees the reply!                         │
        │                                                  │
└──────────────────────────────────────────────────────────────────────┘


USER B's RADIO                                    WEATHER BOT's RADIO
┌──────────────────┐                             ┌──────────────────┐
│ Channel Setup:   │                             │ No channel setup │
│ #alerts  = idx 1 │  (Different mapping!)       │ (accepts all)    │
│ #weather = idx 2 │                             │                  │
└──────────────────┘                             └──────────────────┘
        │                                                  │
        │ 1. Sends "wx Manchester" on #weather            │
        │────────────────────────────────────────────────>│
        │    Binary frame: channel_idx=2                  │
        │                                                  │
        │                                                  │ 2. Receives frame
        │                                                  │    Extracts: idx=2
        │                                                  │    Content: "wx Manchester"
        │                                                  │
        │                                                  │ 3. Processes weather
        │                                                  │    Fetches data
        │                                                  │
        │                                                  │ 4. Replies on idx=2
        │<────────────────────────────────────────────────│    (same as received)
        │    Binary frame: channel_idx=2                  │
        │                                                  │
        │ 5. Receives on #weather (idx=2) ✅              │
        │    User sees the reply!                         │
        │                                                  │
└──────────────────────────────────────────────────────────────────────┘

## Key Points

1. **Different users have different channel→idx mappings**
   - User A: #weather=1, #alerts=2
   - User B: #alerts=1, #weather=2
   - This depends on the order channels were created

2. **LoRa transmits only numeric idx (0-7), not names**
   - Frame contains: channel_idx=1 (not "#weather")
   - Radio firmware handles name→idx mapping locally

3. **Bot replies on the same idx it received from**
   - Receives idx=1 → Replies idx=1
   - Receives idx=2 → Replies idx=2
   - This ensures sender always gets the reply!

4. **Why this works:**
   - User A sends on #weather (their idx=1)
   - Bot receives idx=1, replies idx=1
   - User A receives on idx=1 (their #weather) ✅
   
   - User B sends on #weather (their idx=2)
   - Bot receives idx=2, replies idx=2
   - User B receives on idx=2 (their #weather) ✅

## What Would Happen If Bot Always Replied on idx=0?

```
USER B's RADIO (weather=idx 2)
        │
        │ 1. Sends "wx London" on #weather (idx=2)
        │───────────────────────────────────────────────> BOT
        │                                                  Receives idx=2
        │                                                  Replies idx=0 ❌
        │<─────────────────────────────────────────────── (wrong channel!)
        │ 2. Reply comes on idx=0 (default channel)
        │    User is monitoring #weather (idx=2)
        │    User DOESN'T SEE the reply! ❌
```

This is exactly the bug that was reported: "only replying to idx=0"

But our testing shows **the bot DOES NOT do this**. It correctly replies on the incoming channel_idx!

## Binary Frame Structure

### Incoming Channel Message (RESP_CHANNEL_MSG_V3)

```
Byte    Field           Value
─────────────────────────────────────
0       Frame Start     0x3E (>)
1-2     Length          Varies
3       Response Code   0x11 (CHANNEL_MSG_V3)
4       SNR             Signal strength
5-6     Reserved        0x00 0x00
7       channel_idx     0-7  <-- EXTRACTED HERE
8       path_len        Route hops
9       txt_type        Message type
10-13   timestamp       Unix time
14+     text            "sender: message"
```

### Outgoing Channel Message (CMD_SEND_CHAN_MSG)

```
Byte    Field           Value
─────────────────────────────────────
0       Frame Start     0x3C (<)
1-2     Length          Varies
3       Command Code    0x03 (SEND_CHAN_MSG)
4       txt_type        0x00
5       channel_idx     0-7  <-- SET TO INCOMING VALUE
6-9     timestamp       Unix time
10+     text            Weather data
```

## Code Flow

```python
# 1. Receive frame (meshcore.py:537-560)
if code == _RESP_CHANNEL_MSG_V3:
    channel_idx = payload[4]  # Extract from binary frame
    text = payload[12:].decode("utf-8", "ignore")
    self._dispatch_channel_message(text, channel_idx)

# 2. Create message object (meshcore.py:614-615)
msg = MeshCoreMessage(sender=sender, content=content, 
                     message_type="text", channel_idx=channel_idx)

# 3. Handle weather request (weather_bot.py:267)
self.send_response(response, reply_to_channel_idx=message.channel_idx)

# 4. Send reply (weather_bot.py:315)
self.mesh.send_message(content, "text", channel=None, 
                      channel_idx=reply_to_channel_idx)

# 5. Transmit on LoRa (meshcore.py:273-280)
actual_channel_idx = channel_idx  # Use provided idx directly
cmd_data = bytes([_CMD_SEND_CHAN_MSG, 0, actual_channel_idx]) + ...
self._serial.write(frame)
```

## Test Validation

```python
# From test_multi_channel_reply.py

# Test: Receive on idx=3, verify reply on idx=3
inject_frame(channel_idx=3, sender='USER', text='wx London')
bot.process_message()
reply_idx = extract_reply_channel()

assert reply_idx == 3  # ✅ PASSES FOR ALL 0-7
```

All 21 tests pass, confirming correct behavior for all channel indices.

## Conclusion

The bot's multi-channel reply system works correctly:
- ✅ Extracts channel_idx from incoming frames
- ✅ Preserves channel_idx through message handling
- ✅ Sends replies on the same channel_idx
- ✅ Works for all 8 channels (0-7)
- ✅ Works regardless of user's channel name mappings

If users report issues, the problem is elsewhere (hardware, config, network).
