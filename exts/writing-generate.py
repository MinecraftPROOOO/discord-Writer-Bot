import interactions, time
from models.database import Database
from models.generator import Generator
from models.guild import Guild
from models.helper import Helper
from models.user import User

class GenerateCommand(interactions.ext.autosharder.ShardedExtension):

    def __init__(self, client: interactions.Client):
        self.db = Database.instance()
        self.bot: interactions.Client = client
        self.helper = Helper.instance()
        self.urls = {
            'face': 'https://thispersondoesnotexist.com/image'
        }

    @interactions.extension_command(
        name="generate",
        description="Random generator for character names, place names, book titles, story ideas, etc...",
        options=[
            interactions.Option(
                name="type",
                description="What do you want to generate?",
                type=interactions.OptionType.STRING,
                required=True,
                choices=[
                    interactions.Choice(name=name, value=value) for value, name in Generator.SUPPORTED_TYPES.items()
                ]
            ),
            interactions.Option(
                name="amount",
                description="How many did you want to generate? (Where applicable)",
                type=interactions.OptionType.INTEGER,
                required=False
            )
        ],
        scope=[730804290595061873,503593039541960704],
    )
    async def _generate(self, context: interactions.CommandContext, type: str, amount: int = None):
        """
        Random generator for various things
        :param context:
        :param type:
        :param amount:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('generate'):
            return await context.send('Your guild has disabled this command')

        user = User(context.author.id, context.guild_id, context)

        if amount is None or amount <= 0:
            amount = Generator.DEFAULT_AMOUNT

        # For faces it can only do one.
        if type == 'face':
            return await context.send(self.urls['face'] + '?t=' + str(int(time.time())))

        generator = Generator(type, context)
        results = generator.generate(amount)
        join = '\n'

        # For prompts, add an extra line between them.
        if type == 'prompt':
            join += '\n'

        names = join.join(results['names'])

        return await context.send(user.get_mention() + ', ' + results['message'] + names)


def setup(client):
    GenerateCommand(client)