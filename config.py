# the number of scheduler cycles that the channel needs to be idle
# before the bot posts a generic "did you know"
# message

CHANNEL_IDLE_INTERVAL: int = 4

# the name of the directory where the text files are
# located which contain the messages
# which the bot will randomly send
#  (1 file = 1 message)

IDLE_MESSAGE_DIR: str = "bot_messages"

# the channel where the bot will post messages to

IDLE_MESSAGE_CHANNEL_ID = 758271650226765848

# Variable that indicates when the bot answers after a question has been asked
# (in scheduler cycles)

QUESTION_SLEEPING_TIME = 2

# The Auto Events.
# this is used in three contexts:
# 1. Automatic creation of the event
# 2. Automatic reminder of subscribed users
# 3. in the /subscribe command

# ALL TIMES LOCAL TIMEZONE OF THE BOT !!!!

AUTO_EVENTS = [
    {
        "title": "Sunday Funday session (AM)",
        "description": "Chat with Marc and the folks here on the server ! Share your screen if you want to walk through a problem. Talk about tech stuff with the other members or just listen in...",
        "channel": 758271650688008202,
        "notify_hint": "get notified when the AM session starts",
        "subscription_role": "notify_am",
        "subscription_role_num": 764893618066161695,
        "notify_minutes": 30,
        "day_of_week": 6,
        "start_time": "09:00:00",
        "end_time": "10:00:00",
    },
    {
        "title": "Sunday Funday session (PM)",
        "description": "Chat with Marc and the folks here on the server ! Share your screen if you want to walk through a problem. Talk about tech stuff with the other members or just listen in...",
        "channel": 758271650688008202,
        "notify_hint": "get notified when the PM session starts",
        "subscription_role": "notify_pm",
        "subscription_role_num": 769829891419537448,
        "notify_minutes": 30,
        "day_of_week": 6,
        "start_time": "18:00:00",
        "end_time": "19:00:00",
    },
]
