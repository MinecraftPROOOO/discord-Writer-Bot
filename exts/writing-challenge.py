import interactions, random
from models.challenge import Challenge
from models.database import Database
from models.guild import Guild
from models.helper import Helper
from models.user import User

class ChallengeCommand(interactions.ext.autosharder.ShardedExtension):

    def __init__(self, client: interactions.Client):
        self.db = Database.instance()
        self.bot: interactions.Client = client
        self.helper = Helper.instance()

    @interactions.extension_command(
        name="challenge",
        description="Generate writing challenges to complete",
        options=[
            interactions.Option(
                name="start",
                description="Start a new writing challenge",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="difficulty",
                        description="How difficult should the challenge be?",
                        type=interactions.OptionType.STRING,
                        required=False,
                        choices=[
                            interactions.Choice(name=name, value=value) for value, name in Challenge.DIFFICULTIES.items()
                        ]
                    ),
                    interactions.Option(
                        name="length",
                        description="How many minutes should the challenges be for? (Min: 5, Max: 120)",
                        type=interactions.OptionType.INTEGER,
                        required=False
                    )
                ]
            ),
            interactions.Option(
                name="cancel",
                description="Cancel your current writing challenge",
                type=interactions.OptionType.SUB_COMMAND,
            ),
            interactions.Option(
                name="complete",
                description="Mark your current writing challenge as completed",
                type=interactions.OptionType.SUB_COMMAND,
            ),
            interactions.Option(
                name="check",
                description="Check what your current writing challenge is",
                type=interactions.OptionType.SUB_COMMAND,
            )
        ],
    )
    async def _challenge(self, context: interactions.CommandContext, sub_command: str, difficulty: str = None, length: int = None):
        """
        Run the challenge commands.
        :param context:
        :param sub_command:
        :param difficulty:
        :param length:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('challenge'):
            return await context.send('Your guild has disabled this command')

        user = User(context.author.id, context.guild_id, context)
        challenge = user.get_challenge()

        if sub_command == 'start':

            # If they already have a challenge, they can't start a new one until that is finished/cancelled.
            if challenge:
                info = f"**{challenge['challenge']}**"
                return await context.send(f"{user.get_mention()}, you already have an active challenge: {info}")

            # First create a random WPM and time and then adjust if they are actually specified
            wpm = random.randint(Challenge.WPM['min'], Challenge.WPM['max'])
            time = random.randint(Challenge.TIME['min'], Challenge.TIME['max'])

            # If they specified a difficulty, use that instead.
            if difficulty is not None:

                # Convert the flag to the corresponding WPM
                if difficulty == 'easy':
                    wpm = random.randint(3, 5)
                elif difficulty == 'normal':
                    wpm = random.randint(10, 15)
                elif difficulty == 'hard':
                    wpm = random.randint(20, 30)
                elif difficulty == 'hardcore':
                    wpm = random.randint(35, 45)
                elif difficulty == 'insane':
                    wpm = random.randint(50, 60)

            # If they specified a valid length, use that instead.
            if length is not None and length >= Challenge.TIME['min'] and length <= Challenge.TIME['max']:
                time = length

            # Calculate the word goal and xp it will grant.
            goal = wpm * time
            xp = Challenge.calculate_xp(wpm)

            challenge = f"Write at least {goal} words, in {time} minutes ({wpm} wpm)"
            user.set_challenge(challenge, xp)

            return await context.send(f"{user.get_mention()}, your new challenge is: **{challenge}**")

        elif sub_command == 'cancel':

            if challenge:
                user.delete_challenge()
                return await context.send(f"{user.get_mention()}, you have cancelled your writing challenge")
            else:
                return await context.send(f"{user.get_mention()}, you do not have an active writing challenge to cancel")

        elif sub_command == 'complete':

            if challenge:

                user.complete_challenge(challenge['id'])
                await user.add_xp(challenge['xp'])
                user.add_stat('challenges_completed', 1)
                return await context.send(f"{user.get_mention()}, you have completed your writing challenge **{challenge['challenge']}**        +{challenge['xp']}xp")

            else:
                return await context.send(f"{user.get_mention()}, you do not have an active writing challenge to complete")

        elif sub_command == 'check':

            if challenge:
                return await context.send(f"{user.get_mention()}, your current challenge is: **{challenge['challenge']}**")
            else:
                return await context.send(f"{user.get_mention()}, you do not have an active writing challenge to complete")


def setup(client):
    ChallengeCommand(client)