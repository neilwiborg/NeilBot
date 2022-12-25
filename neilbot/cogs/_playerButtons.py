from collections.abc import Awaitable, Callable

import discord


class PlayerButtons(discord.ui.View):
    """View class to contain music control buttons."""

    def __init__(
        self,
        toggle_pause_callback: Callable[
            [discord.ApplicationContext | discord.Interaction], Awaitable[str]
        ],
        skip_callback: Callable[
            [discord.ApplicationContext | discord.Interaction], Awaitable[str]
        ],
        queue_callback: Callable[
            [discord.ApplicationContext | discord.Interaction], Awaitable[str]
        ],
        stop_callback: Callable[
            [discord.ApplicationContext | discord.Interaction], Awaitable[str]
        ],
    ):
        """Inits the buttons for music controls.

        Args:
            toggle_pause_callback (Callable[
                [discord.ApplicationContext | discord.Interaction], Awaitable[str]
            ]): method to toggle music pause/play
            skip_callback (Callable[
                [discord.ApplicationContext | discord.Interaction], Awaitable[str]
            ]): method to skip the current song
            queue_callback (Callable[
                [discord.ApplicationContext | discord.Interaction], Awaitable[str]
            ]): method to show the music queue
            stop_callback (Callable[
                [discord.ApplicationContext | discord.Interaction], Awaitable[str]
            ]): method to stop the current song
        """
        # need to call the parent constructor first or else the view will not work
        super().__init__(timeout=None)

        # store the callback methods for usage on each button
        self._toggle_pause_callback = toggle_pause_callback
        self._skip_callback = skip_callback
        self._queue_callback = queue_callback
        self._stop_callback = stop_callback

    @discord.ui.button(
        label="Play/Pause",
        custom_id="play_pause",
        row=0,
        style=discord.ButtonStyle.secondary,
        emoji="⏯️",
    )
    async def toggle_play_pause_callback(
        self, button: discord.Button, interaction: discord.Interaction
    ) -> None:
        """Button to toggle the music playing state between paused and resumed.

        Args:
            button (discord.Button): a message button
            interaction (discord.Interaction): the Discord message interaction
        """
        # give us 15 minutes instead of 3 seconds to respond
        await interaction.response.defer()

        # don't need to use the button
        del button
        message = await self._toggle_pause_callback(interaction)
        await interaction.followup.send(message)

    @discord.ui.button(
        label="Skip",
        custom_id="skip",
        row=0,
        style=discord.ButtonStyle.secondary,
        emoji="⏭",
    )
    async def skip_callback(
        self, button: discord.Button, interaction: discord.Interaction
    ) -> None:
        """Button to skip the current song.

        Args:
            button (discord.Button): a message button
            interaction (discord.Interaction): the Discord message interaction
        """
        # give us 15 minutes instead of 3 seconds to respond
        await interaction.response.defer()

        # don't need to use the button
        del button
        message = await self._skip_callback(interaction)
        await interaction.followup.send(message)

    @discord.ui.button(
        label="Stop",
        custom_id="stop",
        row=0,
        style=discord.ButtonStyle.secondary,
        emoji="⏹️",
    )
    async def stop_callback(
        self, button: discord.Button, interaction: discord.Interaction
    ) -> None:
        """Button to stop the current song.

        Args:
            button (discord.Button): a message button
            interaction (discord.Interaction): the Discord message interaction
        """
        # give us 15 minutes instead of 3 seconds to respond
        await interaction.response.defer()

        # don't need to use the button
        del button
        message = await self._stop_callback(interaction)
        await interaction.followup.send(message)

    @discord.ui.button(
        label="Show Queue",
        custom_id="queue",
        row=0,
        style=discord.ButtonStyle.secondary,
        emoji="🎶",
    )
    async def queue_callback(
        self, button: discord.Button, interaction: discord.Interaction
    ) -> None:
        """Button to show the music queue.

        Args:
            button (discord.Button): a message button
            interaction (discord.Interaction): the Discord message interaction
        """
        # give us 15 minutes instead of 3 seconds to respond
        await interaction.response.defer()

        # don't need to use the button
        del button
        message = await self._queue_callback(interaction)
        await interaction.followup.send(message)
