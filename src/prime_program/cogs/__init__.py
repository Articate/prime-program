from disnake.ext import commands

EXTENSIONS: tuple[str, ...] = (
    "prime_program.cogs.elite",
)


def load_extensions(bot: commands.InteractionBot) -> None:
    for extension in EXTENSIONS:
        bot.load_extension(extension)
