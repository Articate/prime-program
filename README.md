# Prime Program Bot

Discord bot built with `disnake` and `pydantic-settings`.

## Structure

- `src/prime_program/main.py`: bot bootstrap + event hooks.
- `src/prime_program/cogs/`: slash command cogs/extensions.
- `src/prime_program/cogs/__init__.py`: extension list + loader.
- `src/prime_program/services/`: shared domain/service logic.
- `src/prime_program/settings.py`: environment-backed config.

## Settings

Configured through `.env`:

- `BOT_KEY` (required)
- `LOG_LEVEL` (optional, default `INFO`)
- `ELO_SCALE` (optional, default `2000`)
- `ELO_K_FACTOR` (optional, default `20`)
- `COMMAND_SYNC_GUILD_IDS` (optional, default `[1378169042514481245]`)

For list settings like `COMMAND_SYNC_GUILD_IDS`, use JSON in `.env`, for example:

`COMMAND_SYNC_GUILD_IDS=[1378169042514481245,123456789012345678]`

## Adding New Interactions

1. Create `src/prime_program/cogs/<name>.py` with a cog class and `setup(bot)` function.
2. Add the cog module path to `EXTENSIONS` in `src/prime_program/cogs/__init__.py`.
3. Keep domain logic in `src/prime_program/services/` so command handlers stay thin.

## Elite Rank Inference

- Rank-to-points inference lives in `src/prime_program/services/rank_points.py`.
- Top ranks use manual anchors (`TOP_RANK_POINT_ANCHORS`) with linear interpolation between known ranks.
- All other ranks use configurable log-linear segments (`LOG_LINEAR_SEGMENTS`) with:
  - `points = intercept - slope * ln(rank)`
