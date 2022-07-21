import json
import aiohttp

# #########################################################
# The class for Discord scheduled events
# as of 2022-07, discord.py does not support
# scheduled Events. Therefore we need to use the Rest API
# #########################################################


class DiscordEvents:
    """Class to create and list Discord events utilizing their API"""

    def __init__(self, discord_token: str, bot_url: str) -> None:
        self.base_api_url = "https://discord.com/api/v10"
        self.auth_headers = {
            "Authorization": f"Bot {discord_token}",
            "User-Agent": f"DiscordBot ({bot_url}) Python/3.9 aiohttp/3.8.1",
            "Content-Type": "application/json",
        }

    async def list_guild_events(self, guild_id: str) -> list:

        print("list_guild_events")

        """Returns a list of upcoming events for the supplied guild ID
        Format of return is a list of one dictionary per event containing information."""
        event_retrieve_url = f"{self.base_api_url}/guilds/{guild_id}/scheduled-events"
        async with aiohttp.ClientSession(headers=self.auth_headers) as session:
            try:
                async with session.get(event_retrieve_url) as response:
                    response.raise_for_status()
                    assert response.status == 200
                    response_list = json.loads(await response.read())
            except Exception as e:
                print(f"EXCEPTION: {e}")
            finally:
                await session.close()
        return response_list

    async def create_guild_event(
        self,
        guild_id: str,
        event_name: str,
        event_description: str,
        event_start_time: str,
        event_end_time: str,
        event_metadata: dict,
        event_privacy_level=2,
        channel_id=None,
    ) -> None:
        """Creates a guild event using the supplied arguments
        The expected event_metadata format is event_metadata={'location': 'YOUR_LOCATION_NAME'}
        The required time format is %Y-%m-%dT%H:%M:%S"""

        print("create_guild_event")

        event_create_url = f"{self.base_api_url}/guilds/{guild_id}/scheduled-events"
        event_data = json.dumps(
            {
                "name": event_name,
                "privacy_level": event_privacy_level,
                "scheduled_start_time": event_start_time,
                "scheduled_end_time": event_end_time,
                "description": event_description,
                "channel_id": channel_id,
                "entity_metadata": event_metadata,
                "entity_type": 2,
            }
        )
        async with aiohttp.ClientSession(headers=self.auth_headers) as session:
            try:
                async with session.post(event_create_url, data=event_data) as response:
                    response.raise_for_status()
                    assert response.status == 200
            except Exception as e:
                print(f"EXCEPTION: {e}")
            finally:
                await session.close()
