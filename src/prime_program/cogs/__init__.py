from disnake.ext import commands

EXTENSIONS: tuple[str, ...] = (
    "prime_program.cogs.elite",
    "prime_program.cogs.test_cog",
    "prime_program.cogs.demo_cog",
)


def load_extensions(bot: commands.InteractionBot) -> None:
    for extension in EXTENSIONS:
        bot.load_extension(extension)
