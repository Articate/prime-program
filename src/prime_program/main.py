import disnake
from disnake.ext import commands

from prime_program.cogs import load_extensions
from prime_program.settings import settings

__version__ = "0.0.1a1"


class PrimeBot(commands.InteractionBot):
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


def build_bot() -> PrimeBot:
    intents = disnake.Intents.default()
    intents.message_content = True

    bot = PrimeBot(intents=intents, test_guilds=settings.command_sync_guild_ids)
    load_extensions(bot)
    return bot


def main() -> None:
    bot = build_bot()
    bot.run(settings.bot_key)


if __name__ == "__main__":
    main()
