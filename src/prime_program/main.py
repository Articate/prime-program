import disnake

from prime_program.settings import settings

__version__ = "0.0.1a1"


class MyClient(disnake.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

    async def on_message(self, message: disnake.Message):
        # Ignore ourselves + other bots
        if message.author.bot:
            return

        content = (message.content or "").strip().lower()
        print(f"Message from {message.author}: {message.content}")
        print(f"Message channel: {message.channel}")
        if content == "ping" and message.channel:
            await message.channel.send("pong")


def main() -> None:
    intents = disnake.Intents.default()
    intents.message_content = True

    client = MyClient(intents=intents)
    client.run(settings.bot_key)


if __name__ == "__main__":
    main()
