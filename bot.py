import discord
from discord import app_commands
from dis_events import DiscordEvents
import random
from glob import glob
import numpy as np
import config
from secret import BOT_TOKEN, CLIENT_ID, GUILD_ID
import utils
from discord.ext import tasks
import datetime
from dateutil import tz

# #######################################
# The OMFClient class
# #######################################


class OMFClient(discord.Client):

    channel_idle_timer: int
    asked_question = False
    last_question: discord.Message = None
    guild_Events = None
    lastNotifyTimeStamp = None

    # #######################################
    # init constructor
    # #######################################

    def __init__(self) -> None:

        print("Init")

        # Try to set all intents

        intents = discord.Intents.all()
        super().__init__(intents=intents)

        # We need a `discord.app_commands.CommandTree` instance
        # to register application commands (slash commands in this case)

        self.tree = app_commands.CommandTree(self)

        self.channel_idle_timer = 0
        self.idle_channel = self.get_channel(config.IDLE_MESSAGE_CHANNEL_ID)

    # #########################
    # setup_hook waits for the
    # command tree to sync
    # #########################

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        await self.tree.sync()

    # ######################################################
    # send_random_message is called when the server is idle
    # and posts a random message to the server
    # ######################################################

    async def send_random_message(self):
        print("Sending random message")
        if self.idle_channel == None:
            self.idle_channel = self.get_channel(config.IDLE_MESSAGE_CHANNEL_ID)
        await self.idle_channel.send(f"{random.choice(self.idle_messages)}")

    # ######################################################
    # on_ready is called once the client is initialized
    # it then reads in the files in the config.IDLE_MESSAGE_DIR
    # directory and posts them randomly every
    # config.CHANNEL_IDLE_INTERVAL seconds into the
    # config.IDLE_MESSAGE_CHANNEL_ID channel
    # ######################################################

    async def on_ready(self):
        print("Logged on as", self.user)

        # read in the random message files
        # the idle_messages array holds one element per message
        # every file is read in as a whole into one element of the array

        self.idle_messages = []

        for filename in glob(config.IDLE_MESSAGE_DIR + "/*.txt"):
            print("read {}", filename)
            with open(filename) as f:
                self.idle_messages.append(f.read())

        self.idle_messages = np.array(self.idle_messages)

        # start the schedulers

        self.task_scheduler.start()
        self.daily_tasks.start()

    # ######################################################
    # handle_ping is called when a user sends ping
    # it just replies with pong
    # ######################################################

    async def handle_ping(self, message: discord.Message):
        await message.channel.send("pong", reference=message)

    # ######################################################
    # create_events will create the Sunday Funday events
    # for the next sunday
    # ######################################################

    async def create_events(self):

        print("Create Events")

        newEvent = DiscordEvents(
            BOT_TOKEN,
            f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot",
        )

        for theEvent in config.AUTO_EVENTS:

            # calculate the date of the future event
            theDate: datetime.datetime = utils.onDay(
                datetime.date.today(), theEvent["day_of_week"]
            )
            # we need the offset from local time to UTC for the date of the event,
            # not the date when we create the event. The event is on a Sunday and might be the
            # first daylight saving day
            utcOffset = tz.tzlocal().utcoffset(
                datetime.datetime.strptime(f"{theDate}", "%Y-%m-%d")
            )
            # the times are stored in local time in the dictionary but will
            # be UTC in the discord API
            utcStartTime = format(
                datetime.datetime.strptime(theEvent["start_time"], "%H:%M:%S")
                - utcOffset,
                "%H:%M:%S",
            )
            utcEndTime = format(
                datetime.datetime.strptime(theEvent["end_time"], "%H:%M:%S")
                - utcOffset,
                "%H:%M:%S",
            )
            # Now we just add the date portion and the time portion
            # of course this will not work for events where the UTCOffset is bigger
            # than the start time - for Germany this is OK as long as the start time is
            # after 2 AM
            strStart = theDate.strftime(f"%Y-%m-%dT{utcStartTime}")
            strEnd = theDate.strftime(f"%Y-%m-%dT{utcEndTime}")
            await newEvent.create_guild_event(
                GUILD_ID,
                theEvent["title"],
                theEvent["description"],
                f"{strStart}",
                f"{strEnd}",
                {},
                2,
                theEvent["channel"],
            )

            # once we have created the event, we let everyone know
            channel = self.get_channel(config.IDLE_MESSAGE_CHANNEL_ID)
            await channel.send(
                f'Hi - I have created the scheduled Event {theEvent["title"]}'
            )

    # ######################################################
    # get_event_list gives a list of scheduled events
    # ######################################################

    async def get_events_list(self):
        newEvent = DiscordEvents(
            BOT_TOKEN,
            f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot",
        )
        eventList = await newEvent.list_guild_events(GUILD_ID)
        self.guild_Events = eventList
        return eventList

    # ######################################################
    # on_message scans for message contents and takes
    # corresponding actions.
    # User sends ping - bot replies with pong
    # User asks a question - bot checks if question has been
    # answered
    # ######################################################

    async def on_message(self, message: discord.Message):
        print("{} has just sent {}".format(message.author, message.content))

        # don't respond to ourselves
        if message.author == self.user:
            return
        # reset the idle timer if a message has been sent or received
        self.channel_idle_timer = 0

        # reply to ping
        if message.content == "ping":
            await self.handle_ping(message)

        # check if there is a question

        if "?" in message.content:
            self.asked_question = True
            self.last_question = message
        else:
            self.asked_question = False
            self.last_question = None

    # ######################################################
    # on_typing detects if a user types.
    # We might use this one day to have users agree to policies etc.
    # before they are allowed to speak
    # ######################################################

    async def on_typing(self, channel, user, _):
        # we do not want the bot to reply to itself
        if user.id == self.user.id:
            return
        print(f"{user} is typing in {channel}")
        self.channel_idle_timer = 0
        # await channel.trigger_typing()

    # ######################################################
    # daily_tasks runs once a day and checks the following:
    # - does an event need to be created ?
    # ######################################################

    @tasks.loop(hours=24)
    async def daily_tasks(self):
        print("DAILY TASKS")

        # Every Monday we want to create the scheduled events
        # for the next Sunday

        if datetime.date.today().weekday() == 0:
            print("create events")
            try:
                await self.create_events()
            except Exception as e:
                print(f"Daily Task create Events failed: {e}")

    # ######################################################
    # task_scheduler is the main supervisor task
    # it runs every 10 minutes and checks the following:
    # - has a question been asked that has not been answered ?
    # - do reminders need to be sent out ?
    # - does a random message need to be sent out ?
    # ######################################################

    @tasks.loop(minutes=10)
    async def task_scheduler(self):

        self.channel_idle_timer += 1
        print("SCHEDULE")

        # #####################################
        # See if there are unanswered questions
        # #####################################
        try:
            if self.asked_question:
                print("scheduler: Question")
                print(self.last_question.created_at)
                # TODO - we need to send out a message to the @here role
                # asking users to help if the question had not been answered
                # Also - if the message is a reply then we should not post into the channel
                if self.channel_idle_timer > config.QUESTION_SLEEPING_TIME:
                    print("QUESTION WITHOUT REPLY")
                    self.asked_question = False
        except Exception as e:
            print(f"Scheduler question failed: {e}")

        # #####################################
        # see if we need to send a random message
        # if the counter is greater than CHANNEL_IDLE_INTERVAL
        # then send a random message into the idle_channel
        # #####################################
        try:
            if self.channel_idle_timer >= config.CHANNEL_IDLE_INTERVAL:
                self.channel_idle_timer = 0
                await self.send_random_message()
        except Exception as e:
            print(f"Scheduler random_message failed: {e}")

        # see if we need to send out notifications for events
        # The Event details are stored in config.
        eventList = None
        for theEvent in config.AUTO_EVENTS:
            # first let's convert the String dates to datetime:
            theDate = utils.onDay(datetime.date.today(), theEvent["day_of_week"])
            startTime = theEvent["start_time"]
            eventScheduledTimeDate = datetime.datetime.fromisoformat(
                theDate.strftime(f"%Y-%m-%dT{startTime}")
            )
            # now let's figure out the time deltas:
            timeUntilEvent = eventScheduledTimeDate - datetime.datetime.today()
            earliestPing = (
                eventScheduledTimeDate
                - datetime.timedelta(minutes=theEvent["notify_minutes"])
                - datetime.timedelta(minutes=10)
            )
            latestPing = eventScheduledTimeDate - datetime.timedelta(
                minutes=theEvent["notify_minutes"]
            )
            # print("found scheduled event")
            # print(f"The event is on {theDate} at {startTime} - that is in {timeUntilEvent}")
            # print (f"we ping between {earliestPing} and {latestPing}")
            # If we are in the interval then let's initiate the reminder
            if earliestPing < datetime.datetime.today() <= latestPing:
                # let's first check if the event is still on
                # it may have been deleted or modified on the server
                # we don't want to alert for non-existing events
                # we'll just use the title to compare for the time being.
                print("Let me check if the event is still on")
                try:
                    if eventList == None:
                        newEvent = DiscordEvents(
                            BOT_TOKEN,
                            f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot",
                        )
                        eventList = await newEvent.list_guild_events(GUILD_ID)
                    for theScheduledEvent in eventList:
                        if theScheduledEvent["name"] == theEvent["title"]:
                            channel = self.get_channel(config.IDLE_MESSAGE_CHANNEL_ID)
                            theMessageText = f'Hi <@&{theEvent["subscription_role_num"]}>, the event *** {theEvent["title"]} *** will start in roughly {theEvent["notify_minutes"]} minutes in the <#{theEvent["channel"]}> channel. {theEvent["description"]}'
                            await channel.send(f"{theMessageText}")
                except Exception as e:
                    print(f"Scheduler event_reminder failed: {e}")
