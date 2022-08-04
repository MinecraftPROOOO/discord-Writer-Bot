import interactions
from models.database import Database
from models.guild import Guild
from models.helper import Helper
from models.project import Project
from models.user import User

class WroteCommand(interactions.ext.autosharder.ShardedExtension):

    def __init__(self, client: interactions.Client):
        self.db = Database.instance()
        self.bot: interactions.Client = client
        self.helper = Helper.instance()

    @interactions.extension_command(
        name="wrote",
        description="Add to your total words written statistic",
        options=[
            interactions.Option(
                name="amount",
                description="How many words did you write? (Use negative numbers to remove words)",
                type=interactions.OptionType.INTEGER,
                required=True
            ),
            interactions.Option(
                name="project",
                description="The shortname of the project you also want to add the words to",
                type=interactions.OptionType.STRING,
                required=False
            )
        ],
    )
    async def _wrote(self, context: interactions.CommandContext, amount: int, project: str = None):
        """
        Add words to the user's total written statistic
        :param context:
        :param amount:
        :param project:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('wrote'):
            return await context.send('Your guild has disabled this command')

        user = User(context.author.id, context.guild_id, context)
        message = None

        # If they specified a project, add the words to that as well.
        if project is not None:

            user_project = Project.get(user.id, project)
            if not user_project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({project})")

            # Increment project word count.
            user_project.words += amount
            user_project.save()

            # Send the message about adding to a project
            written_stat = user.get_stat('total_words_written')
            if written_stat is None:
                written_stat = 0
            total = int(written_stat) + int(amount)
            message = f"added {amount} words to your project **{user_project.name} ({user_project.shortname})** ({user_project.words}) [{total}]"

        user.add_stat('total_words_written', amount)
        total = user.get_stat('total_words_written')

        # Update any goals they are running.
        await user.add_to_goals(amount)

        if message is None:
            message = f"added {amount} to your total words written **({total})**"

        return await context.send(f"{user.get_mention()}, {message}")




def setup(client):
    WroteCommand(client)