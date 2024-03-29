import aiohttp
import json


class AIODiscord:
    def __init__(self, *, url):
        self.url = url

    async def post(
        self,
        *,
        content=None,
        username=None,
        avatar_url=None,
        tts=False,
        file=None,
        embeds=None,
        allowed_mentions=None
    ):
        if content is None and file is None and embeds is None:
            raise ValueError("required one of content, file, embeds")
        data = {}
        if content is not None:
            data["content"] = content
        if username is not None:
            data["username"] = username
        if avatar_url is not None:
            data["avatar_url"] = avatar_url
        data["tts"] = tts
        if embeds is not None:
            data["embeds"] = embeds
        if allowed_mentions is not None:
            data["allowed_mentions"] = allowed_mentions
        async with aiohttp.ClientSession() as session:
            if file is not None:
                async with session.post(self.url, data={"payload_json": json.dumps(data)}, files=file):
                    ...
            else:
                async with session.post(
                        self.url,
                        data={"payload_json": json.dumps(data)},
                        headers={"Content-Type": "application/json"}
                ):
                    ...
