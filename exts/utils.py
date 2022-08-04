import interactions
import pytz
import time
from datetime import datetime, timezone, timedelta
from interactions import Extension, extension_command
from models.database import Database
from models.helper import Helper
from models.guild import Guild
from models.user import User
from config import VERSION, SUPPORT_SERVER, INVITE_URL, WIKI_URL

class Utils(interactions.ext.autosharder.ShardedExtension):

    COMMAND_LIST = ['info', 'invite', 'ping', 'profile', 'reset', '8ball', 'flip', 'reassure', 'roll', 'challenge', 'generate', 'goal', 'project', 'sprint', 'wrote']

    def __init__(self, client: interactions.Client):
        self.bot: interactions.Client = client
        self.db = Database.instance()
        self.helper = Helper.instance()

    @interactions.extension_command(
        name="help",
        description="Help information on how to use the bot",
    )
    async def _help(self, context: interactions.CommandContext):
        """
        Help link generation
        :param context:
        :return:
        """

        # Send "Bot is Waiting" message.
        await context.defer()

        footer = interactions.EmbedFooter(
            text=f"Requested by {context.author.user.username}#{context.author.user.discriminator}",
            icon_url=f"{context.author.user.avatar_url}",
        )

        embed = interactions.Embed(
            title="Help",
            url=WIKI_URL,
            description="Use the above link to navigate to the Wiki help page",
            footer=footer,
        )

        await context.send(embeds=embed)

    @interactions.extension_command(
        name="ping",
        description="Displays latency between client and bot",
    )
    async def _ping(self, context: interactions.CommandContext):
        """
        Displays the latency between client and bot
        :param interactions.CommandContext context:
        :return:
        """

        # Send "Bot is Waiting" message.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('ping'):
            return await context.send('Your guild has disabled this command')

        # Work out latency and respond.
        ping = f"{self.bot._clients[0].latency * 1:.0f}"

        if int(ping) < int(99):
            colour = 0x57F287
        elif int(ping) < int(199):
            colour = 0xFEE75C
        else:
            colour = 0xED4245

        footer = interactions.EmbedFooter(
            text=f"Requested by {context.author.user.username}#{context.author.user.discriminator}",
            icon_url=f"{context.author.user.avatar_url}",
        )
        embed = interactions.Embed(
            title="Hi there! :wave:",
            description=f"Your ping is **{ping}ms**",
            color=colour,
            footer=footer,
        )

        await context.send(embeds=embed)


    @interactions.extension_command(
        name="info",
        description="Display information and statistics about the bot",
    )
    async def _info(self, context: interactions.CommandContext):
        """
        Displays info and statistics about the bot
        :param interactions.CommandContext context :
        :return:
        """

        # Send "Bot is Waiting" message.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('info'):
            return await context.send('Your guild has disabled this command')

        # Work out stats to display.
        now = time.time()
        uptime = int(round(now - self.bot.start_time))
        uptime = f"{timedelta(seconds=uptime)}"
        sprints = self.db.get('sprints', {'completed': 0}, ['COUNT(id) as cnt'])['cnt']

        stats = []
        stats.append(f"• Servers: {format(len(self.bot.guilds))}")
        stats.append(f"• Active Sprints: {str(sprints)}")
        stats = "\n".join(stats)

        version = VERSION
        support_server = SUPPORT_SERVER
        latency = f"{self.bot._clients[0].latency * 1:.0f}ms"

        # Embedded message response.
        fields = [
            interactions.EmbedField(name="Version", value=version, inline=True),
            interactions.EmbedField(name="Owner", value=str(self.bot.me.owner), inline=True),
            interactions.EmbedField(name="Uptime", value=uptime, inline=True),
            interactions.EmbedField(name="Latency", value=latency, inline=True),
            interactions.EmbedField(name="General Statistics", value=stats, inline=False),
            interactions.EmbedField(name="Support Server", value=support_server, inline=False),
        ]

        footer = interactions.EmbedFooter(
            text=f"Requested by {context.author.user.username}#{context.author.user.discriminator}",
            icon_url=f"{context.author.user.avatar_url}",
        )
        embed = interactions.Embed(
            title="About Writer-Bot",
            color=3447003,
            footer=footer,
            fields=fields
        )

        await context.send(embeds=embed)

    @interactions.extension_command(
        name="profile",
        description="Displays your user profile",
    )
    async def _profile(self, context: interactions.CommandContext):
        """
        Display the user profile
        :param context:
        :return:
        """

        # Send "Bot is Waiting" message.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('profile'):
            return await context.send('Your guild has disabled this command')

        user = User(context.author.id, context.guild_id, context)
        profile = {
            'lvlxp': user.get_xp_bar(),
            'words': user.get_stat('total_words_written'),
            'words_sprints': user.get_stat('sprints_words_written'),
            'sprints_started': user.get_stat('sprints_started'),
            'sprints_completed': user.get_stat('sprints_completed'),
            'sprints_won': user.get_stat('sprints_won'),
            'challenges_completed': user.get_stat('challenges_completed'),
            'daily_goals_completed': user.get_stat('daily_goals_completed'),
            'weekly_goals_completed': user.get_stat('weekly_goals_completed'),
            'monthly_goals_completed': user.get_stat('monthly_goals_completed'),
            'yearly_goals_completed': user.get_stat('yearly_goals_completed'),
        }

        fields = [
            interactions.EmbedField(name="Level (XP)", value=profile['lvlxp'], inline=True),
            interactions.EmbedField(name="Words Written", value=profile['words'], inline=True),
            interactions.EmbedField(name="Words Written in Sprints", value=profile['words_sprints'], inline=True),
            interactions.EmbedField(name="Sprints Started", value=profile['sprints_started'], inline=True),
            interactions.EmbedField(name="Sprints Completed", value=profile['sprints_completed'], inline=True),
            interactions.EmbedField(name="Sprints Won", value=profile['sprints_won'], inline=True),
            interactions.EmbedField(name="Challenges Completed", value=profile['challenges_completed'], inline=True),
            interactions.EmbedField(name="Daily Goals Completed", value=profile['daily_goals_completed'], inline=True),
            interactions.EmbedField(name="Weekly Goals Completed", value=profile['weekly_goals_completed'], inline=True),
            interactions.EmbedField(name="Monthly Goals Completed", value=profile['monthly_goals_completed'], inline=True),
            interactions.EmbedField(name="Yearly Goals Completed", value=profile['yearly_goals_completed'], inline=True),
        ]

        footer = interactions.EmbedFooter(
            text=f"Requested by {context.author.user.username}#{context.author.user.discriminator}",
            icon_url=f"{context.author.user.avatar_url}",
        )

        embed = interactions.Embed(
            title=context.author.name,
            color=3066993,
            fields=fields,
            footer=footer
        )

        await context.send(embeds=embed)

    @interactions.extension_command(
        name="reset",
        description="Reset some or all of your user statistics",
        options=[
            interactions.Option(
                name="stat",
                description="What statistic do you want to reset?",
                type=interactions.OptionType.STRING,
                required=True,
                choices=[
                    interactions.Choice(
                        name="WPM Personal Best",
                        value="wpm"
                    ),
                    interactions.Choice(
                        name="Words Written",
                        value="wc"
                    ),
                    interactions.Choice(
                        name="Level/XP",
                        value="xp"
                    ),
                    interactions.Choice(
                        name="Projects",
                        value="projects"
                    ),
                    interactions.Choice(
                        name="All",
                        value="all"
                    ),
                ]
            )
        ]
    )
    async def _reset(self, context: interactions.CommandContext, stat: str):
        """
        Reset some of your user stats
        :param context:
        :param stat:
        :return:
        """

        # Send "Bot is Waiting" message.
        await context.defer(ephemeral=True)

        user = User(context.author.id, context.guild_id, context)

        if stat == 'wpm':
            user.update_record('wpm', 0)
            output = 'Words per minute PB reset to 0'

        elif stat == 'wc':
            user.update_stat('total_words_written', 0)
            output = 'Total word count reset to 0'

        elif stat == 'xp':
            await user.update_xp(0)
            output = 'Level/XP reset to 0'

        elif stat == 'projects':
            user.reset_projects()
            output = 'Projects reset'

        elif stat == 'all':
            user.reset()
            output = 'Profile reset'

        return await context.send(output, ephemeral=True)



    @interactions.extension_command(
        name="setting",
        description="Setting commands",
        options=[
            interactions.Option(
                name="list",
                description="List all of the current settings for this server",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="update",
                description="Update the value of one of the settings for this server",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="setting",
                        description="The name of the setting to update",
                        type=interactions.OptionType.STRING,
                        choices=[
                            interactions.Choice(
                                name="Enable command",
                                value="enable"
                            ),
                            interactions.Choice(
                                name="Disable command",
                                value="disable"
                            ),
                            interactions.Choice(
                                name="Sprint end delay (minutes)",
                                value="sprint_delay_end"
                            )
                        ],
                        required=True
                    ),
                    interactions.Option(
                        name="value",
                        description="The value to set for the setting",
                        type=interactions.OptionType.STRING,
                        required=True
                    )
                ]
            )
        ]
    )
    async def _setting(self, context: interactions.CommandContext, sub_command: str, setting: str = None, value: str = None):

        # Send "Bot is Waiting" message.
        await context.defer()

        # Does user have permissions?
        if not context.author.permissions.MANAGE_GUILD:
            return await context.send('You do not have permission to run this command in this server')

        guild = Guild(context.guild_id)

        # List the settings.
        if sub_command == 'list':

            settings = guild.get_settings()
            output = '```ini\n'
            if settings:
                for setting, value in settings.items():
                    output += setting + '=' + str(value) + '\n'
            else:
                output += 'No settings found'
            output += '```'

            return await context.send(output)

        elif sub_command == 'update':

            # Validate the data sent through.

            # Sprint delay.
            if setting == 'sprint_delay_end' and (not self.helper.is_number(value) or int(value) < 1):
                return await context.send('Value must be a number, greater than 0')

            # Enable/Disable commands.
            elif setting in ['disable', 'enable']:
                if value not in Utils.COMMAND_LIST:
                    return await context.send('You cannot enable/disable this command')
                else:
                    # This is different so run the update and return.
                    guild.disable_enable_command(value, (setting == 'disable'))
                    return await context.send(f"Successfully {setting}d command `{value}`!")

            # Everything is okay with validation, so update the setting.
            guild.update_setting(setting, value)
            return await context.send(f"Updated server setting `{setting}` to `{value}`")

    @interactions.extension_command(
        name="mysetting",
        description="User setting commands",
        options=[
            interactions.Option(
                name="list",
                description="List all of your settings",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="update",
                description="Update the value of one of your settings",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="setting",
                        description="The name of the setting to update",
                        type=interactions.OptionType.STRING,
                        choices=[
                            interactions.Choice(
                                name="Timezone",
                                value="timezone"
                            ),
                            interactions.Choice(
                                name="Max WPM",
                                value="maxwpm"
                            ),
                        ],
                        required=True
                    ),
                    interactions.Option(
                        name="value",
                        description="The value to set for the setting",
                        type=interactions.OptionType.STRING,
                        required=True
                    )
                ]
            )
        ]
    )
    async def _mysetting(self, context: interactions.CommandContext, sub_command: str, setting: str = None,
                       value: str = None):

        # Send "Bot is Waiting" message.
        await context.defer(ephemeral=True)

        user = User(context.author.id, context.guild_id, context)

        # List the settings.
        if sub_command == 'list':

            settings = user.get_settings()
            output = '```ini\n'
            if settings:
                for setting, value in settings.items():
                    output += setting + '=' + str(value) + '\n'
            else:
                output += 'No settings found'
            output += '```'

            return await context.send(output, ephemeral=True)

        elif sub_command == 'update':

            # Validate the data sent through.

            # Timezone.
            if setting == 'timezone':

                try:
                    timezone = pytz.timezone(value)
                except pytz.exceptions.UnknownTimeZoneError:
                    await context.send('Your timezone setting must be a valid TZ Database Name. Please see the following page and choose your timezone: https://kevinnovak.github.io/Time-Zone-Picker/ (It should look something like `Europe/London`)',
                                       ephemeral=True)
                    return


            # Max WPM setting.
            elif setting == 'maxwpm':

                # Must be a number.
                value = self.helper.is_number(value)
                if not value or value <= 0:
                    return await context.send('Max WPM setting must be a number greater than 0', ephemeral=True)

            # Everything is okay with validation, so update the setting.
            user.update_setting(setting, value)
            return await context.send(f"Updated your setting `{setting}` to `{value}`", ephemeral=True)

    @interactions.extension_command(
        name="invite",
        description="Generate the invite link to invite the bot to another server",
    )
    async def _invite(self, context: interactions.CommandContext):
        """
        Invite link generation
        :param context:
        :return:
        """

        # Send "Bot is Waiting" message.
        await context.defer()

        footer = interactions.EmbedFooter(
            text=f"Requested by {context.author.user.username}#{context.author.user.discriminator}",
            icon_url=f"{context.author.user.avatar_url}",
        )

        embed = interactions.Embed(
            title="Invite Link",
            url=INVITE_URL,
            description="Use the above link to invite the bot to your servers!",
            footer=footer,
        )

        await context.send(embeds=embed)


def setup(client):
    Utils(client)