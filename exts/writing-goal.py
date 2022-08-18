import interactions, math, time
from models.database import Database
from models.guild import Guild
from models.helper import Helper
from models.user import User

GOAL_TYPE_DAILY = 'daily'
GOAL_TYPE_WEEKLY = 'weekly'
GOAL_TYPE_MONTHLY = 'monthly'
GOAL_TYPE_YEARLY = 'yearly'
GOAL_TYPES = [GOAL_TYPE_DAILY, GOAL_TYPE_WEEKLY, GOAL_TYPE_MONTHLY, GOAL_TYPE_YEARLY]

class GoalCommand(interactions.Extension):

    def __init__(self, client: interactions.Client):
        self.db = Database.instance()
        self.bot: interactions.Client = client
        self.helper = Helper.instance()

    @interactions.extension_command(
        name="goal",
        description="Manage your writing goals",
        options=[
            interactions.Option(
                name="set",
                description="Update a writing goal",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="type",
                        description="Type of goal to set",
                        type=interactions.OptionType.STRING,
                        required=True,
                        choices=[
                            interactions.Choice(name=value, value=value) for value in GOAL_TYPES
                        ]
                    ),
                    interactions.Option(
                        name="amount",
                        description="Word count to set as the goal",
                        type=interactions.OptionType.INTEGER,
                        required=True
                    )
                ]
            ),
            interactions.Option(
                name="check",
                description="Check the status of one or all of your writing goals",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="type",
                        description="Type of goal to check. If not specified, will check all goals.",
                        type=interactions.OptionType.STRING,
                        required=False,
                        choices=[
                            interactions.Choice(name=value, value=value) for value in GOAL_TYPES
                        ]
                    ),
                ]
            ),
            interactions.Option(
                name="delete",
                description="Delete one of your writing goals",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="type",
                        description="Type of goal to delete.",
                        type=interactions.OptionType.STRING,
                        required=True,
                        choices=[
                            interactions.Choice(name=value, value=value) for value in GOAL_TYPES
                        ]
                    ),
                ]
            ),
            interactions.Option(
                name="time",
                description="Check how long you have left for a goal",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="type",
                        description="Type of goal to check.",
                        type=interactions.OptionType.STRING,
                        required=True,
                        choices=[
                            interactions.Choice(name=value, value=value) for value in GOAL_TYPES
                        ]
                    ),
                ]
            ),
            interactions.Option(
                name="update",
                description="Update your progress on a writing goal, without affecting your Level/XP or any other goals",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="type",
                        description="Type of goal to update",
                        type=interactions.OptionType.STRING,
                        required=True,
                        choices=[
                            interactions.Choice(name=value, value=value) for value in GOAL_TYPES
                        ]
                    ),
                    interactions.Option(
                        name="amount",
                        description="Word count to update the goal's progress to",
                        type=interactions.OptionType.INTEGER,
                        required=True
                    )
                ]
            ),
            interactions.Option(
                name="history",
                description="Check the historical data for one of your writing goals",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="type",
                        description="Type of goal to check.",
                        type=interactions.OptionType.STRING,
                        required=True,
                        choices=[
                            interactions.Choice(name=value, value=value) for value in GOAL_TYPES
                        ]
                    ),
                ]
            )
        ]
    )
    async def _goal(self, context: interactions.CommandContext, sub_command: str, type: str = None, amount: int = None):
        """
        Run the goal command and whatever subcommand is chosen.
        :param context:
        :param sub_command:
        :param type:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('goal'):
            return await context.send('Your guild has disabled this command')

        user = User(context.author.id, context.guild_id, context)

        # Setting a goal.
        if sub_command == 'set':

            # Check the amount is valid.
            amount = self.helper.is_number(amount)
            if not amount:
                return await context.send(user.get_mention() + ', Error: Please enter a valid amount')

            # Set the goal.
            user.set_goal(type, amount)
            return await context.send(f"{type.title()} goal set to **{amount}** words. Now, get writing!")

        elif sub_command == 'check':

            # Specific goal.
            if type is not None:

                goal = user.get_goal(type)
                if goal:
                    progress = user.get_goal_progress(type)
                    return await context.send(
                        f"{user.get_mention()}, you are **{progress['percent']}%** of the way to your {type} goal. ({progress['current']}/{progress['goal']})")
                else:
                    return await context.send(
                        f"{user.get_mention()}, you do not currently have a {type} goal. Maybe you should set one? `/goal update {type} <wordcount>`")

            # All goals.
            else:

                now = int(time.time())
                fields = []

                for type in GOAL_TYPES:

                    text = ''
                    goal = user.get_goal(type)
                    if goal:

                        progress = user.get_goal_progress(type)
                        seconds_left = goal['reset'] - now
                        left = self.helper.secs_to_days(seconds_left)
                        current_wordcount = progress['current']
                        goal_wordcount = progress['goal']
                        words_remaining = goal_wordcount - current_wordcount

                        if words_remaining <= 0:
                            words_remaining = 0

                        text += f"Your {type} goal is to write **{goal['goal']}** words.\n"
                        text += f"You are **{progress['percent']}%** of the way to your {type} goal. ({current_wordcount}/{goal_wordcount}).\n"
                        text += f"{self.helper.format_secs_to_days(seconds_left)} left until {type} goal reset.\n"

                        if type != GOAL_TYPE_DAILY:

                            days = left['days']
                            hours = left['hours']
                            days = days + (1 if hours > 0 else 0)

                            if words_remaining > 0:
                                average_wordcount_needed = math.ceil(words_remaining / (1 if days == 0 else days))
                                text += f"If you write approx {average_wordcount_needed} words a day, you will meet your {type} goal!\n"

                        if words_remaining <= 0:
                            text += f"You have met your {type} goal of {goal_wordcount} words!\n"

                    else:
                        text = 'None'

                    fields.append(interactions.EmbedField(name=type.title(), value=text, inline=False))

                footer = interactions.EmbedFooter(
                    text=f"Requested by {context.author.user.username}#{context.author.user.discriminator}",
                    icon_url=f"{context.author.user.avatar_url}",
                )

                embed = interactions.Embed(
                    title="Writing Goals",
                    color=10038562,
                    footer=footer,
                    fields=fields
                )

                await context.send(embeds=embed)

        elif sub_command == 'delete':

            user.delete_goal(type)
            return await context.send(f"{user.get_mention()}, you have cancelled your {type} goal.")

        elif sub_command == 'time':

            goal = user.get_goal(type)
            if goal:
                now = int(time.time())
                reset = goal['reset']
                left = self.helper.format_secs_to_days(reset - now)
                return await context.send(f"{user.get_mention()}, {left} left until {type} goal reset.")
            else:
                return await context.send(
                    f"{user.get_mention()}, you do not currently have a {type} goal. Maybe you should set one? `/goal update {type} <wordcount>`")

        elif sub_command == 'update':

            # Check the amount is valid.
            amount = self.helper.is_number(amount)
            if not amount:
                return await context.send(f"{user.get_mention()}, Error: Please enter a valid amount")

            goal = user.get_goal(type)
            if goal and user.update_goal(type, amount):
                return await context.send(
                    f"{user.get_mention()}, manually updated {type} goal word count to: **{amount}**.")
            else:
                return await context.send(
                    f"{user.get_mention()}, you do not currently have a {type} goal. Maybe you should set one? `/goal update {type} <wordcount>`")

        elif sub_command == 'history':

            fields = []

            history = user.get_goal_history(type)
            for record in history:
                title = record['date']
                text = str(record['result']) + '/' + str(record['goal'])
                text += ' :white_check_mark:' if record['completed'] else ''
                fields.append(interactions.EmbedField(name=title, value=text, inline=False))

            footer = interactions.EmbedFooter(
                text=f"Requested by {context.author.user.username}#{context.author.user.discriminator}",
                icon_url=f"{context.author.user.avatar_url}",
            )

            embed = interactions.Embed(
                title=type.title() + " Goal History",
                color=10038562,
                footer=footer,
                fields=fields
            )

            await context.send(embeds=embed)


def setup(client):
    GoalCommand(client)