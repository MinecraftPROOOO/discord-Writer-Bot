import interactions
import random
from models.guild import Guild
from models.helper import Helper

class Fun(interactions.ext.autosharder.ShardedExtension):

    ROLL_MAX_SIDES = 1000000
    ROLL_MAX_ROLLS = 100
    EIGHT_BALL_ANSWERS = [
        ":blue_circle: It is certain",
        ":blue_circle: It is decidedly so",
        ":blue_circle: Without a doubt",
        ":blue_circle: Yes - definitely",
        ":blue_circle: You may rely on it",
        ":blue_circle: Of course",
        ":blue_circle: Most likely",
        ":blue_circle: Outlook good",
        ":blue_circle: Yes",
        ":blue_circle: Signs point to yes",
        ":white_circle: Reply hazy, try again",
        ":white_circle: Ask again later",
        ":white_circle: Better not tell you now",
        ":white_circle: Cannot predict now",
        ":white_circle: Concentrate and ask again",
        ":red_circle: Don't count on it",
        ":red_circle: My reply is no",
        ":red_circle: My sources say no",
        ":red_circle: Outlook not so good",
        ":red_circle: Very doubtful",
        ":red_circle: Absolutely not"
    ]

    def __init__(self, client: interactions.Client):
        self.bot: interactions.Client = client
        self.helper = Helper.instance()

    @interactions.extension_command(
        name="flip",
        description="Flip a coin",
        scope=[730804290595061873,503593039541960704]
    )
    async def _flip(self, context: interactions.CommandContext):
        """
        Flip a coin and respond with outcome
        :param context:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('flip'):
            return await context.send('Your guild has disabled this command')

        # Random number between 1-2 to choose heads or tails.
        rand = random.randrange(2)
        side = 'heads' if rand == 0 else 'tails'

        # Send the message.
        await context.send('It landed on ' + side + '!')


    @interactions.extension_command(
        name="8ball",
        description="Ask the magic 8-ball a question",
        scope=[730804290595061873,503593039541960704],
        options=[
            interactions.Option(
                name="question",
                description="What is your question for the magic 8-ball?",
                type=interactions.OptionType.STRING,
                required=True
            )
        ]
    )
    async def _8ball(self, context: interactions.CommandContext, question: str):
        """
        Ask the magic 8-ball a question
        :param context:
        :param question:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('8ball'):
            return await context.send('Your guild has disabled this command')

        max = len(self.EIGHT_BALL_ANSWERS) - 1
        answer = self.EIGHT_BALL_ANSWERS[random.randrange(max)]

        await context.send(f"You asked the magic 8-ball: **{question}**\n\n*{answer}*")

    @interactions.extension_command(
        name="roll",
        description="Roll one or more dice and get the result",
        scope=[730804290595061873,503593039541960704],
        options=[
            interactions.Option(
                name="dice",
                description="What dice do you want to roll? Format: {number}d{sides}, e.g. 1d6, 2d20, etc...",
                type=interactions.OptionType.STRING,
                required=False
            )
        ]
    )
    async def _roll(self, context: interactions.CommandContext, dice: str = '1d6'):
        """
        Roll some dice
        :param context:
        :param question:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('roll'):
            return await context.send('Your guild has disabled this command')

        # Make sure the format is correct (1d6).
        try:
            sides = int(dice.split('d')[1])
            rolls = int(dice.split('d')[0])
        except Exception as e:
            await context.send('Dice option must be in format #d# (e.g. 1d6 or 2d20)');
            return

        # Make sure the sides and rolls are valid.
        if sides < 1:
            sides = 1
        elif sides > self.ROLL_MAX_SIDES:
            return await context.send(f"The dice cannot have more than {self.ROLL_MAX_SIDES} sides")

        if rolls < 1:
            rolls = 1
        elif rolls > self.ROLL_MAX_ROLLS:
            return await context.send(f"The dice cannot be rolled more than {self.ROLL_MAX_ROLLS} times")

        total = 0
        output = ''

        # Roll the dice {rolls} amount of times.
        for x in range(rolls):
            val = random.randint(1, sides)
            total += val
            output += ' [ ' + str(val) + ' ] '

        # Now print out the total.
        output += '\n**Total: ' + str(total) + '**';

        # Send message.
        await context.send(output)

    @interactions.extension_command(
        name="reassure",
        description="Send a random reassuring message to another user or yourself",
        scope=[730804290595061873,503593039541960704],
        options=[
            interactions.Option(
                name="who",
                description="Who do you want to reassure?",
                type=interactions.OptionType.USER,
                required=False
            )
        ]
    )
    async def _reassure(self, context: interactions.CommandContext, who: str = None):
        """
        Send a reassuring message to someone
        :param context:
        :param who:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('reassure'):
            return await context.send('Your guild has disabled this command')

        # If no name passed through, default to the author of the command.
        if who is None:
            mention = context.author.mention
        else:
            mention = who.mention

        messages = self.helper.get_asset('reassure')
        max = len(messages) - 1
        quote = messages[random.randrange(max)]

        return await context.send(mention + ', ' + format(quote))



def setup(client):
    Fun(client)