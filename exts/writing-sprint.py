import interactions, time
from datetime import datetime
from models.database import Database
from models.guild import Guild
from models.helper import Helper
from models.project import Project
from models.sprint import Sprint
from models.task import Task
from models.user import User

class SprintCommand(interactions.ext.autosharder.ShardedExtension):

    DEFAULT_LENGTH = 20
    DEFAULT_DELAY = 2
    MAX_LENGTH = 60
    MAX_DELAY = 60*24
    WPM_CHECK = 150

    def __init__(self, client: interactions.Client):
        self.bot: interactions.Client = client
        self.db = Database.instance()
        self.helper = Helper.instance()

    @interactions.extension_command(
        name="sprint",
        description="Start and interact with writing sprints",
        options=[
            interactions.Option(
                name="for",
                description="Start a new writing sprint",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="length",
                        description="How long (in minutes) should the sprint last for? (Min: 1, Max: 60)",
                        type=interactions.OptionType.INTEGER,
                        required=True
                    ),
                    interactions.Option(
                        name="in",
                        description="Start a sprint in (mins) time from now",
                        type=interactions.OptionType.INTEGER,
                        required=False
                    ),
                    interactions.Option(
                        name="at",
                        description="Start a sprint at (min) past the hour",
                        type=interactions.OptionType.INTEGER,
                        required=False
                    )
                ]
            ),
            interactions.Option(
                name="cancel",
                description="Cancel the current sprint",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="end",
                description="Force the sprint to end and ask for word counts",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="leave",
                description="Leave the current sprint",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="time",
                description="Check how long is left in the current sprint",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="status",
                description="Get your status in the current sprint",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="pb",
                description="Check your sprint personal best WPM",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="notify",
                description="Set whether or not you want to be notified of new sprints on this server",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="notify",
                        description="Whether or not to notify",
                        required=True,
                        type=interactions.OptionType.INTEGER,
                        choices=[
                            interactions.Choice(name="Yes", value=1),
                            interactions.Choice(name="No", value=0)
                        ]
                    )
                ]
            ),
            interactions.Option(
                name="purge",
                description="Purge any users who asked for notifications but aren't in the server any more",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="project",
                description="Set which of your projects you are sprinting in",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Project shortname",
                        type=interactions.OptionType.STRING,
                        required=True
                    )
                ]
            ),
            interactions.Option(
                name="join",
                description="Join the current sprint",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="initial",
                        description="Initial word count to start from",
                        type=interactions.OptionType.INTEGER,
                        required=False
                    ),
                    interactions.Option(
                        name="project",
                        description="Project shortname to sprint in",
                        type=interactions.OptionType.STRING,
                        required=False
                    )
                ]
            ),
            interactions.Option(
                name="join-no-wc",
                description="Join the current sprint as an editing user with no word count",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="project",
                        description="Project shortname to sprint in",
                        type=interactions.OptionType.STRING,
                        required=False
                    )
                ]
            ),
            interactions.Option(
                name="join-same",
                description="Join the current sprint starting from where you left off in the last sprint (word count and project)",
                type=interactions.OptionType.SUB_COMMAND
            ),
            interactions.Option(
                name="wc",
                description="Declare total word count for the sprint",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="amount",
                        description="How many words have you written (including your initial word count)",
                        type=interactions.OptionType.INTEGER,
                        required=True
                    )
                ]
            ),
            interactions.Option(
                name="wrote",
                description="Add/Subtract words from your sprint word count",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="amount",
                        description="How many words do you want to add to your word count (use negative to subtract)",
                        type=interactions.OptionType.INTEGER,
                        required=True
                    )
                ]
            ),
        ]
    )
    async def _sprint(self, context: interactions.CommandContext, sub_command: str, **kwargs):
        """
        Run the sprint commands.
        :param context:
        :param sub_command:
        :param length:
        :param wait:
        :param at:
        :return:
        """
        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer()

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('sprint'):
            return await context.send('Your guild has disabled this command')

        user = User(context.author.id, context.guild_id, context)

        # Get values from options. We use kwargs here because 'in' is a keyword in python and can't be used as a param name.
        length = kwargs.get('length')
        in_mins = kwargs.get('in') or None
        at_mins = kwargs.get('at') or None

        sprint = Sprint(context.guild_id)

        # Start a sprint
        if sub_command == 'for':

            if in_mins is not None:
                type = 'in'
                value = in_mins
            elif at_mins is not None:
                type = 'at'
                value = at_mins
            else:
                type = None
                value = None

            return await self.sprint_start(context, sprint, user, length, type, value)

        elif sub_command == 'cancel':
            return await self.sprint_cancel(context, sprint, user)

        elif sub_command == 'leave':
            return await self.sprint_leave(context, sprint, user)

        elif sub_command == 'time':
            return await self.sprint_time(context, sprint, user)

        elif sub_command == 'status':
            return await self.sprint_status(context, sprint, user)

        elif sub_command == 'pb':
            return await self.sprint_pb(context, sprint, user)

        elif sub_command == 'notify':
            value = kwargs.get('notify')
            return await self.sprint_notify(context, user, value)

        elif sub_command == 'project':
            shortname = kwargs.get('shortname')
            return await self.sprint_project(context, sprint, user, shortname)

        elif sub_command == 'join':
            initial = kwargs.get('initial')
            shortname = kwargs.get('project')
            return await self.sprint_join(context, sprint, user, initial, shortname)

        elif sub_command == 'join-no-wc':
            shortname = kwargs.get('project')
            return await self.sprint_join(context, sprint, user, None, shortname, Sprint.TYPE_NO_WORDCOUNT)

        elif sub_command == 'join-same':
            return await self.sprint_join_same(context, sprint, user)

        elif sub_command == 'wc':
            amount = kwargs.get('amount')
            return await self.sprint_wc(context, sprint, user, amount)

        elif sub_command == 'wrote':
            amount = kwargs.get('amount')
            return await self.sprint_wrote(context, sprint, user, amount)

        elif sub_command == 'purge':
            return await self.sprint_purge(context, user)

        elif sub_command == 'end':
            return await self.sprint_end(context, sprint, user)

    async def sprint_common_checks(self, context, sprint, user):
        """
        Run common checks before various sprint commands
        :param user:
        :param context:
        :param sprint:
        :return:
        """
        # If there is no active sprint, show an error.
        if not sprint.exists():
            await context.send(f"{user.get_mention()}, there is no sprint running on this server. Maybe you should start one? `/sprint for`")
            return False

        # All okay.
        return True

    async def sprint_common_start_check(self, context, sprint, user):
        """
        Run common check to see if sprint has started yet and display error if not
        :param context:
        :param sprint:
        :param user:
        :return:
        """
        if not sprint.has_started():
            await context.send(f"{user.get_mention()}, the sprint hasn't started yet.")
            return False

        return True

    async def sprint_common_is_sprinting_check(self, context, sprint, user):
        """
        Run common check to see if the user is in the current sprint
        :param context:
        :param sprint:
        :param user:
        :return:
        """
        # If the user is not sprinting, then again, just display that error
        if not sprint.is_user_sprinting(user.id):
            await context.send(f"{user.get_mention()}, you are not currently sprinting. Use `sprint join` to join.")
            return False

        return True

    async def set_word_count(self, context, sprint, user, user_sprint, amount: int):
        """
        Set the user's word count for the sprint
        :param context:
        :param sprint:
        :param user:
        :param amount:
        :return:
        """
        # Before we actually update it, if the WPM is huge and most likely an error, just check with them if they meant to put that many words.
        written = amount - int(user_sprint['starting_wc'])
        seconds = int(sprint.end_reference) - user_sprint['timejoined']
        wpm = Sprint.calculate_wpm(written, seconds)

        # Does the user have a configured setting for max wpm to check?
        max_wpm = user.get_setting('maxwpm')
        if not max_wpm:
            max_wpm = self.WPM_CHECK

        # Exceeded the max WPM, so show a warning.
        if wpm > int(max_wpm):
            return await context.send(f"{user.get_mention()}, did you really mean to submit **{written}** words? That would be **{wpm}** wpm. If you did, please increase this warning threshold by running `/mysetting maxwpm <wpm>` and then redeclare your word count.", ephemeral=True)

        # Update the user's sprint record.
        if sprint.is_finished():
            sprint.update_user(user.id, ending=amount)
        else:
            sprint.update_user(user.id, current=amount)

        # Reload the object.
        user_sprint = sprint.get_user_sprint(user.id)

        # Which value are we displaying?
        wordcount = user_sprint['ending_wc'] if sprint.is_finished() else user_sprint['current_wc']
        written = int(wordcount) - int(user_sprint['starting_wc'])

        await context.send(f"{user.get_mention()}, you updated your word count to: **{wordcount}**. Total words written in this sprint: **{written}**.")
        context.deferred = False

        if sprint.is_finished() and sprint.is_declaration_finished():
            Task.cancel('sprint', sprint.id)
            await sprint.complete_sprint(context=context)

    async def sprint_purge(self, context, user):
        """
        Purge old users from sprint notifications
        :param context:
        :param user:
        :return:
        """
        if not context.author.permissions & interactions.Permissions.MANAGE_MESSAGES:
            return await context.send(f"{user.get_mention()}, you do not have permission to do this")

        purged = await Sprint.purge_notifications(context)
        return await context.send(f"{user.get_mention()}, purged {purged} old users from sprint notifications")

    async def sprint_wrote(self, context, sprint, user, amount: int):
        """
        Add/Remove words to/from the word count for the sprint
        :param context:
        :param sprint:
        :param user:
        :param amount:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        # If the user is not sprinting, then again, just display that error
        if not await self.sprint_common_is_sprinting_check(context, sprint, user):
            return

        # If the sprint hasn't started yet, display that generic error.
        if not await self.sprint_common_start_check(context, sprint, user):
            return

        # Get the user's sprint info
        user_sprint = sprint.get_user_sprint(user.id)

        if user_sprint['sprint_type'] == Sprint.TYPE_NO_WORDCOUNT:
            return await context.send(f"{user.get_mention()}, you joined the sprint as a non-wordcount user. You cannot declare a word count.")

        new_amount = int(user_sprint['current_wc']) + amount
        return await self.set_word_count(context, sprint, user, user_sprint, new_amount)


    async def sprint_wc(self, context, sprint, user, amount: int):
        """
        Declare the word count for the sprint
        :param context:
        :param sprint:
        :param user:
        :param amount:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        # If the user is not sprinting, then again, just display that error
        if not await self.sprint_common_is_sprinting_check(context, sprint, user):
            return

        # If the sprint hasn't started yet, display that generic error.
        if not await self.sprint_common_start_check(context, sprint, user):
            return

        # Get the user's sprint info
        user_sprint = sprint.get_user_sprint(user.id)

        if user_sprint['sprint_type'] == Sprint.TYPE_NO_WORDCOUNT:
            return await context.send(f"{user.get_mention()}, you joined the sprint as a non-wordcount user. You cannot declare a word count.")

        # If they declared less than they started with, that is an error.
        if amount < int(user_sprint['starting_wc']):
            diff = int(user_sprint['current_wc']) - amount
            return await context.send(f"{user.get_mention()}, word count **{amount}** is less than the word count you started with (**{user_sprint['starting_wc']}**)!\nIf you joined with a starting word count, make sure to declare your new TOTAL word count, not just the amount you wrote in this sprint.\nIf you really are trying to lower your word count for this sprint, please run: `sprint wrote -{diff}` instead, to decrement your current word count")

        return await self.set_word_count(context, sprint, user, user_sprint, amount)


    async def sprint_join_same(self, context, sprint, user):
        """
        Join the sprint using settings from previous sprint
        :param context:
        :param sprint:
        :param user:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        # Okay, check for their most recent sprint record.
        most_recent = user.get_most_recent_sprint(sprint.id)
        if not most_recent:
            # If they have never joined a sprint before and try this, just join normally.
            return await self.sprint_join(context, sprint, user, 0)

        # If there was a project, get the shortname to pass through to sprint_join().
        initial = most_recent['ending_wc']
        shortname = None
        type = most_recent['sprint_type']

        if most_recent['project'] is not None:
            project = Project(most_recent['project'])
            if project:
                shortname = project.shortname

        return await self.sprint_join(context, sprint, user, initial=initial, shortname=shortname, type=type)


    async def sprint_join(self, context, sprint, user, initial: int = 0, shortname: str = None, type: str = None):
        """
        Join the sprint
        :param context:
        :param sprint:
        :param user:
        :param initial:
        :param shortname:
        :param type:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        message = ""
        project_id = None
        project = None
        if initial is None:
            initial = 0

        # Check for project.
        if shortname is not None:
            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})")
            project_id = project.id

        # If they are already in the sprint, update their record.
        if sprint.is_user_sprinting(user.id):

            # Normal sprint.
            if type is None:
                sprint.update_user(user.id, start = initial, current = initial, type = type, project_id = project_id, force_type_update = True)
                message = f"your starting word count has been set to **{initial}**."

            elif type == Sprint.TYPE_NO_WORDCOUNT:
                sprint.update_user(user.id, start=0, current=0, type=type, project_id=project_id)
                message = f"you are now sprinting without a word count. You will not be included in the final tallies."

        else:

            # Normal sprint.
            if type is None:
                sprint.join(user.id, start = initial, type = type, project_id = project_id)
                message = f"you have joined the sprint with **{initial}** words."

            elif type == Sprint.TYPE_NO_WORDCOUNT:
                sprint.join(user.id, start = 0, type = type, project_id = project_id)
                message = f"you are now sprinting without a word count. You will not be included in the final tallies."

        # If they chose a project, add that to the message.
        if project:
            message += f" You are sprinting in your project **{project.name}**."

        return await context.send(f"{user.get_mention()}, {message}")


    async def sprint_project(self, context, sprint, user, shortname):
        """
        Set the project the user is sprinting in.
        :param context:
        :param sprint:
        :param user:
        :param shortname:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        # If the user is not sprinting, then again, just display that error
        if not await self.sprint_common_is_sprinting_check(context, sprint, user):
            return

        # Get the project.
        project = Project.get(user.id, shortname)
        if not project:
            return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})")

        sprint.set_project(user.id, project.id)
        return await context.send(f"{user.get_mention()}, you are now sprinting in your project **{project.name}**.")

    async def sprint_notify(self, context, user, value):
        """
        Change notify setting for the user
        :param value:
        :param context:
        :param user:
        :return: 
        """
        user.set_guild_setting(context.guild_id, 'sprint_notify', str(value))
        message = "You will be notified of any new sprints which are scheduled on this server." if value == 1 \
            else "You will no longer be notified of any new sprints which are scheduled on this server."

        await context.send(f"{user.get_mention()}, {message}")

    async def sprint_pb(self, context, sprint, user):
        """
        Check the user's personal best WPM from sprints
        :param context:
        :param sprint:
        :param user:
        :return:
        """
        record = user.get_record('wpm')
        if record is None:
            return await context.send(f"{user.get_mention()}, you do not yet have a wpm personal best. Get sprinting, if you want one!")
        else:
            return await context.send(f"{user.get_mention()}, your personal best is **{record}** wpm.")

    async def sprint_status(self, context, sprint, user):
        """
        Get the user's sprint status
        :param context:
        :param sprint:
        :param user:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        # If the user is not sprinting, then again, just display that error
        if not await self.sprint_common_is_sprinting_check(context, sprint, user):
            return

        # If the sprint hasn't started yet, display that generic error.
        if not await self.sprint_common_start_check(context, sprint, user):
            return

        # If they are sprinting, then display their current status.
        user_sprint = sprint.get_user_sprint(user.id)

        # Build the variables to be passed into the status string
        now = int(time.time())
        current = user_sprint['current_wc']
        written = current - user_sprint['starting_wc']
        seconds = now - user_sprint['timejoined']
        elapsed = round(seconds / 60, 1)
        wpm = Sprint.calculate_wpm(written, seconds)
        left = round((sprint.end - now) / 60, 1)

        return await context.send(f"{user.get_mention()}, your current word count is: {current} ({written} written in this sprint). You have been sprinting for {elapsed} minutes, averaging a WPM of **{wpm}**. There are {left} minutes left until this sprint ends.")

    async def sprint_time(self, context, sprint, user):
        """
        Check how long is left
        :param context:
        :param sprint:
        :param user:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        now = int(time.time())

        # If the sprint has not yet started, display the time until it starts.
        if not sprint.has_started():
            left = self.helper.secs_to_mins(sprint.start - now)
            return await context.send(f"{user.get_mention()}, sprint begins in {left['m']} minutes, {left['s']} seconds")

        # If it's currently still running, display how long is left.
        elif not sprint.is_finished():
            left = self.helper.secs_to_mins(sprint.end - now)
            return await context.send(f"{user.get_mention()}, {left['m']} minutes, {left['s']} seconds remaining")

        # If it's finished but not yet marked as completed, we must be waiting for word counts.
        elif sprint.is_finished():
            return await context.send(f"{user.get_mention()}, waiting for final word counts. If the results haven't been posted after everyone has declared, try forcing the sprint to end with `sprint end`")


    async def sprint_leave(self, context, sprint, user):
        """
        Leave the current sprint
        :param context:
        :param sprint:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        sprint.leave(user.id)
        await context.send(f"{user.get_mention()}, you have left the sprint")

        # If there any no users left, cancel the sprint.
        if len(sprint.get_users()) == 0:

            # Cancel the sprint
            sprint.cancel(context)

            # Decrement sprints_started stat for whoever started this one
            creator = User(sprint.createdby, sprint.guild)
            creator.add_stat('sprints_started', -1)

            # Display a message letting users know
            context.deferred = False
            return await context.send("**Sprint has been cancelled**\nEverybody left and I'm not doing this alone.")

    async def sprint_end(self, context, sprint, user):
        """
        Force the sprint to end
        :param context:
        :param sprint:
        :param user:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        # If they do not have permission to end this sprint, display an error.
        if int(sprint.createdby) != int(user.id) and not (context.author.permissions & interactions.Permissions.MANAGE_MESSAGES):
            return await context.send(f"{user.get_mention()}, you do not have permission to end this sprint")

        # If the sprint hasn't started yet, display that generic error.
        if not await self.sprint_common_start_check(context, sprint, user):
            return

        # Change the end reference time to now, instead of the original time that was set.
        sprint.update({'end_reference': int(time.time())})

        # Since we are forcing the end, we should cancel any pending tasks for this sprint
        Task.cancel('sprint', sprint.id)

        # Pass the bot into the sprint object.
        sprint.set_bot(self.bot)

        return await sprint.end_sprint(context)

    async def sprint_cancel(self, context, sprint, user):
        """
        Cancel the current sprint
        :param user:
        :param context:
        :param sprint:
        :return:
        """
        if not await self.sprint_common_checks(context, sprint, user):
            return

        # If they do not have permission to cancel this sprint, display an error.
        if int(sprint.createdby) != int(user.id) and not (context.author.permissions & interactions.Permissions.MANAGE_MESSAGES):
            return await context.send(f"{user.get_mention()}, you do not have permission to cancel this sprint")

        # Get the users sprinting and create an array of mentions
        users = sprint.get_users()
        notify = sprint.get_notifications(users)

        # Cancel the sprint
        sprint.cancel(context)

        # Display the cancellation message
        return await context.send('**Sprint has been cancelled**: ' + ', '.join(notify))


    async def sprint_start(self, context, sprint, user, length: int, type: str = None, value: int = None):
        """
        Start a sprint
        :param user:
        :param context:
        :param sprint:
        :param value:
        :param type:
        :param length:
        :return:
        """
        # Check if sprint is finished but not yet marked as completed.
        if sprint.is_finished() and sprint.is_declaration_finished():
            # Mark the sprint as complete
            await sprint.complete()
            # Reload the sprint object, as now there shouldn't be a pending one.
            sprint.reload()

        # If sprint is currently running, cannot start a new one.
        if sprint.exists():
            return await context.send(f"{user.get_mention()}, there is already a sprint running here. Please wait until it has finished before creating a new one.")

        # Make sure the length and other values are okay.

        # If length is invalid, just use the default value.
        if length < 1 or length > self.MAX_LENGTH:
            length = self.DEFAULT_LENGTH

        # Work out when it should start.
        delay = 0

        if type == 'in':
            if value < 0 or value > self.MAX_DELAY:
                delay = self.DEFAULT_DELAY
            else:
                delay = value

        elif type == 'at':
            # Make sure the user has set their timezone, otherwise we can't calculate it.
            timezone = user.get_setting('timezone')
            user_timezone = self.helper.get_timezone(timezone)
            if not user_timezone:
                return await context.send(f"{user.get_mention()}, you need to set a valid timezone in order to do this. Please see `help mysetting`")

            if value < 0 or value > 59:
                return await context.send(f"{user.get_mention()}, value must be a valid minute between 0 and 59")

            # Now using their timezone and the minute they requested, calculate when that should be.
            delay = (60 + value - datetime.now(user_timezone).minute) % 60

        # Calculate the start and end times based on the current timestamp.
        now = int(time.time())
        start_time = now + (delay * 60)
        end_time = start_time + (length * 60)

        # Create the sprint.
        sprint = Sprint.create(
            guild=str(context.guild_id),
            channel=str(context.channel_id),
            start=start_time,
            end=end_time,
            end_reference=end_time,
            length=length,
            createdby=user.id,
            created=now
        )

        # Join the sprint.
        sprint.join(user.id)

        # Increment the user's stat for sprints created.
        user.add_stat('sprints_started', 1)

        # Are we starting immediately?
        if delay == 0:
            Task.schedule('end', end_time, 'sprint', sprint.id)
            return await sprint.post_start(context=context, immediate=True)
        else:
            Task.schedule('start', start_time, 'sprint', sprint.id)
            return await sprint.post_delayed_start(context)



def setup(client):
    SprintCommand(client)