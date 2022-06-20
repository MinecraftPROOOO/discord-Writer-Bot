import interactions, math, numpy, time
from operator import itemgetter
from models.database import Database
from models.experience import Experience
from models.guild import Guild
from models.helper import Helper
from models.project import Project
from models.task import Task
from models.user import User

class Sprint:

    TYPE_NO_WORDCOUNT = 'no_wordcount'
    DEFAULT_POST_DELAY = 2
    WINNING_POSITION = 1

    def __init__(self, guild_id: int, bot = None):
        """
        Instantiate the object
        """
        self.__db = Database.instance()
        self.__helper = Helper.instance()
        self.__bot = bot

        # TODO: Threads

        self.id = None
        self.guild = str(guild_id)

        self.load()

    def is_valid(self):
        """
        Check if the Sprint object is valid
        :return:
        """
        return self.id is not None

    def exists(self):
        """
        Check if a sprint exists on this server
        :return:
        """
        return self.is_valid()

    def set_bot(self, bot):
        """
        Set the discord bot object into the sprint to be used for sending messages in the cron
        :param bot:
        :return:
        """
        self.__bot = bot

    def is_finished(self):
        """
        Check if a sprint is finished based on the end time.
        This is different from checking if it is completed, which is based on the completed field
        :return: bool
        """
        now = int(time.time())
        return self.exists() and now > self.end

    def is_complete(self):
        """
        Check if the sprint is marked as completed in the database
        :return:
        """
        return self.completed > 0

    def is_declaration_finished(self):
        """
        Check if everyone sprinting has declared their final word counts
        :return: bool
        """
        results = self.__db.get_all_sql(
            'SELECT * FROM sprint_users WHERE sprint = %s AND ending_wc = 0 AND (sprint_type IS NULL OR sprint_type != %s)',
            [self.id, Sprint.TYPE_NO_WORDCOUNT])
        return len(results) == 0

    def has_started(self):
        """
        Check if the sprint has started yet
        :return:
        """
        now = int(time.time())
        return self.start <= now

    def load(self, by: str = 'guild'):
        """
        Try to load the sprint out of the database for the given guild_id
        :return: bool
        """
        if by == 'id':
            params = {'id': self.id, 'completed': 0}
        else:
            params = {'guild': self.guild, 'completed': 0}

        result = self.__db.get('sprints', params)
        if result:
            self.id = result['id']
            self.guild = result['guild']
            self.channel = result['channel']
            self.start = result['start']
            self.end = result['end']
            self.end_reference = result['end_reference']
            self.length = result['length']
            self.createdby = result['createdby']
            self.created = result['created']
            self.completed = result['completed']
            return True
        else:
            self.id = None
            self.guild = None
            self.channel = None
            self.start = None
            self.end = None
            self.end_reference = None
            self.length = None
            self.createdby = None
            self.created = None
            self.completed = None
            return False

    def reload(self):
        """
        Reload the sprint object
        :return:
        """
        return self.load()

    def join(self, user_id, start: int = 0, type: str = None, project_id: int = None):
        """
        Add a user to a sprint with an optional starting word count number
        :param user_id:
        :param starting_wc:
        :param sprint_type:
        :return: void
        """
        # Get the current timestamp
        now = int(time.time())

        # If the sprint hasn't started yet, set the user's start time to the sprint start time, so calculations will work correctly.
        if not self.has_started():
            now = self.start

        # Insert the sprint_users record
        self.__db.insert('sprint_users',
                         {
                             'sprint': self.id,
                             'user': user_id,
                             'starting_wc': start,
                             'current_wc': start,
                             'ending_wc': 0,
                             'timejoined': now,
                             'sprint_type': type,
                             'project': project_id
                         }
         )

    def get_users(self):
        """
        Get an array of all the sprint_users records for users taking part in this sprint
        :bool exclude_non_wordcount_sprinters:
        :return:
        """
        users = self.__db.get_all('sprint_users', {'sprint': self.id})
        return [int(row['user']) for row in users]

    def get_notify_users(self):
        """
        Get an array of all the users who want to be notified about new sprints on this server
        :return:
        """
        notify = self.__db.get_all('user_settings', {'guild': self.guild, 'setting': 'sprint_notify', 'value': 1})
        notify_ids = [int(row['user']) for row in notify]

        # We don't need to notify users who are already in the sprint, so we can exclude those
        users_ids = self.get_users()
        return numpy.setdiff1d(notify_ids, users_ids).tolist()

    def get_notifications(self, users):
        """
        Get an array of user mentions for each person in the supplied array of userids
        :return:
        """
        notify = []
        for user_id in users:
            usr = User(user_id, self.guild)
            notify.append(usr.get_mention())
        return notify

    def cancel(self, context):
        """
        Cancel the sprint and notify the users who were taking part
        :return:
        """
        # Load current user
        user = User(context.author.id, context.guild_id, context)

        # Delete sprints and sprint_users records
        self.__db.delete('sprint_users', {'sprint': self.id})
        self.__db.delete('sprints', {'id': self.id})

        # Delete pending scheduled tasks
        Task.cancel('sprint', self.id)

        # If the user created this, decrement their created stat
        if user.id == self.createdby:
            user.add_stat('sprints_started', -1)

    def update(self, params):
        """
        Update the sprint object with the specified params
        :param params:
        :return:
        """
        self.__db.update('sprints', params, {'id': self.id})

    def leave(self, user_id):
        """
        Remove a user from the sprint
        :param user_id:
        :return:
        """
        self.__db.delete('sprint_users', {'sprint': self.id, 'user': user_id})

    def is_user_sprinting(self, user_id):
        """
        Check if a given user is in the sprint
        :param int user_id:
        :return:
        """
        user_ids = self.get_users()
        return int(user_id) in user_ids

    def get_user_sprint(self, user_id):
        """
        Get a sprint_users record for the given user on this sprint
        :param user_id:
        :return:
        """
        return self.__db.get('sprint_users', {'sprint': self.id, 'user': user_id})

    def set_project(self, user_id, project_id):
        """
        Set the id of the Project being sprinted for
        :param user_id:
        :param project_id:
        :return:
        """
        return self.__db.update('sprint_users', {'project': project_id}, {'sprint': self.id, 'user': user_id})

    def update_user(self, user_id, start = None, current = None, ending = None, type = None, project_id = None, force_type_update = False):
        """
        Update a user's sprint record
        :param user_id:
        :param start:
        :param current:
        :param ending:
        :param sprint_type:
        :return:
        """

        update = {}

        if start is not None:
            update['starting_wc'] = start

        if current is not None:
            update['current_wc'] = current

        if ending is not None:
            update['ending_wc'] = ending

        if type is not None or force_type_update is True:
            update['sprint_type'] = type

        if project_id is not None:
            update['project'] = project_id

        # If the sprint hasn't started yet, set the user's start time to the sprint start time, so calculations will work correctly.
        if not self.has_started():
            update['timejoined'] = self.start

        self.__db.update('sprint_users', update, {'sprint': self.id, 'user': user_id})

    async def post_start(self, context=None, bot=None, immediate=False):
        """
        Post the sprint start message
        :param immediate:
        :param context: This is passed through when posting start immediately. Otherwise if its in a cron job, it will be None and we will use the bot object.
        :param bot:
        :return:
        """
        # Build the message to display
        message = f"**Sprint has started**\nGet writing, you have {self.length} minute(s).\n"

        # Add mention for anyone who has joined the sprint.
        notify_joined = ', '.join(self.get_notifications(self.get_users()))
        message += f":wave: {notify_joined}"

        # Add mention for any user who wants to be notified of starting sprints.
        # If we had a delayed start, these notifications would have been done there. So only show them here, if it's an immediate start.
        if immediate:
            notify_users = self.get_notifications(self.get_notify_users())
            if notify_users:
                notify_asked = ', '.join(notify_users)
                message += f"\n:bell: {notify_asked}"

        return await self.say(message, context, bot)

    async def post_delayed_start(self, context):
        """
        Post the message displaying when the sprint will start
        :param context:
        :return:
        """
        now = int(time.time())

        # Add a few seconds in case its slow to post the message. Then it will display the higher minute instead of lower.
        delay = self.__helper.secs_to_mins((self.start + 5) - now)

        # Build the message to display
        message = f"**A new sprint has been scheduled**\nSprint will start in approx {delay['m']} minutes and will run for {self.length} minute(s). Use `/sprint join` to join this sprint."

        # Add mentions for any user who wants to be notified
        notify_users = self.get_notifications(self.get_notify_users())
        if notify_users:
            notify_asked = ', '.join(notify_users)
            message += f"\n:bell: {notify_asked}"

        return await context.send(message)

    async def end_sprint(self, context=None, bot=None):
        """
        Mark the sprint as finished and ask for final word counts
        :param context:
        :param bot:
        :return:
        """
        # Mark sprint as ended in the DB.
        self.update({'end': 0})

        # If we didn't pass the bot through in the command, get it from the sprint object.
        if bot is None:
            bot = self.__bot

        # Get the sprinting users to notify.
        notify = self.get_notifications(self.get_users())

        guild = Guild(self.guild)
        delay = guild.get_setting('sprint_delay_end')
        if delay is None:
            delay = self.DEFAULT_POST_DELAY

        # Post the ending message, asking for word counts.
        message = f"**Time is up**\nPens down. Use `/sprint wc <amount>` to submit your final word counts, you have {delay} minute(s).\n"
        message = message + ', '.join(notify)
        await self.say(message, context, bot)

        # If there are only non-wc sprinters and not-one who needs to submit a word count, just complete immediately.
        if self.is_declaration_finished():
            return await self.complete_sprint(context, bot)

        # Convert the minutes to seconds.
        delay = int(delay) * 60
        task_time = int(time.time()) + delay

        # Schedule the task to complete the sprint and wrap everything up.
        Task.schedule('complete', task_time, 'sprint', self.id)

    async def complete_sprint(self, context = None, bot = None):
        """
        Complete the sprint. Work out the XP, leaderboard, do the goal updating, etc...
        :param context:
        :param bot:
        :return:
        """
        # If the sprint has already completed, stop.
        if self.completed != 0:
            return

        # Print the "Results coming shortly" message.
        await self.say(f"The word counts are in. Results coming up shortly...", context, bot)

        # Create array to use for storing the results.
        results = []

        # Mark the sprint as completed in the DB.
        now = int(time.time())
        self.update({'completed': now})

        # Get all the users taking part.
        users = self.get_users()

        # Loop through them and get their full sprint info.
        for user_id in users:

            user = User(user_id, self.guild, context=context, bot=bot, channel=self.channel)
            user_sprint = self.get_user_sprint(user_id)

            # If it's a non-word count sprint, we don't need to do anything with word counts.
            if user_sprint['sprint_type'] == Sprint.TYPE_NO_WORDCOUNT:

                # Just give them the completed sprint stat and XP.
                await user.add_xp(Experience.XP_COMPLETE_SPRINT)
                user.add_stat('sprints_completed', 1)

                # Push user to results.
                results.append({
                    'user': user,
                    'wordcount': 0,
                    'xp': Experience.XP_COMPLETE_SPRINT,
                    'type': user_sprint['sprint_type']
                })

            else:

                # If they didn't submit an ending word count, use their current one and update the DB row with it.
                if user_sprint['ending_wc'] == 0:
                    user_sprint['ending_wc'] = user_sprint['current_wc']
                    self.update_user(user_id, ending=user_sprint['ending_wc'])

                # Now we only process their result if they have declared something and it's different to their starting word count.
                user_sprint['starting_wc'] = int(user_sprint['starting_wc'])
                user_sprint['current_wc'] = int(user_sprint['current_wc'])
                user_sprint['ending_wc'] = int(user_sprint['ending_wc'])
                user_sprint['timejoined'] = int(user_sprint['timejoined'])

                if user_sprint['ending_wc'] > 0 and user_sprint['ending_wc'] != user_sprint['starting_wc']:

                    wordcount = user_sprint['ending_wc'] - user_sprint['starting_wc']
                    time_sprinted = self.end_reference - user_sprint['timejoined']

                    # If for some reason the timejoined or sprint.end_reference are 0, then use the defined sprint length instead.
                    if user_sprint['timejoined'] <= 0 or self.end_reference == 0:
                        time_sprinted = self.length

                    # Calculate the WPM from their time sprinted
                    wpm = Sprint.calculate_wpm(wordcount, time_sprinted)

                    # See if it's a new record for the user
                    user_record = user.get_record('wpm')
                    wpm_record = True if user_record is None or wpm > int(user_record) else False

                    # If it is a record, update their record in the database
                    if wpm_record:
                        user.update_record('wpm', wpm)

                    # Give them XP for finishing the sprint
                    await user.add_xp(Experience.XP_COMPLETE_SPRINT)

                    # Increment their stats
                    user.add_stat('sprints_completed', 1)
                    user.add_stat('sprints_words_written', wordcount)
                    user.add_stat('total_words_written', wordcount)

                    # Increment their words towards their goal
                    await user.add_to_goals(wordcount)

                    # If they were writing in a Project, update its word count.
                    if user_sprint['project'] is not None:
                        project = Project(user_sprint['project'])
                        project.words += wordcount
                        project.save()

                    # Push user to results
                    results.append({
                        'user': user,
                        'wordcount': wordcount,
                        'wpm': wpm,
                        'wpm_record': wpm_record,
                        'xp': Experience.XP_COMPLETE_SPRINT,
                        'type': user_sprint['sprint_type']
                    })

        # Sort the results.
        results = sorted(results, key=itemgetter('wordcount'), reverse=True)

        # Now loop through them again and apply extra XP, depending on their position in the results.
        position = 1
        highest_word_count = 0

        for result in results:

            if result['wordcount'] > highest_word_count:
                highest_word_count = result['wordcount']

            # If the user finished in the top 5 and they weren't the only one sprinting, earn extra XP.
            is_sprint_winner = result['wordcount'] == highest_word_count
            if position <= 5 and len(results) > 1:
                extra_xp = math.ceil(
                    Experience.XP_WIN_SPRINT / (self.WINNING_POSITION if is_sprint_winner else position)
                )
                result['xp'] += extra_xp
                await result['user'].add_xp(extra_xp)

            # If they actually won the sprint, increase their stat by 1
            # Since the results are in order, the highest word count will be set first
            # which means that any subsequent users with the same word count have tied for 1st place
            if position == 1 or result['wordcount'] == highest_word_count:
                result['user'].add_stat('sprints_won', 1)

            position += 1

        # Post the final message with the results
        if len(results) > 0:

            position = 1
            message = ":trophy: **Sprint Results** :trophy:\nCongratulations to everyone.\n"
            for result in results:

                if result['type'] == Sprint.TYPE_NO_WORDCOUNT:
                    message = message + f"{result['user'].get_mention()}         +{result['xp']} xp"
                else:
                    message = message + f"`{position}`. {result['user'].get_mention()} - **{result['wordcount']} words** ({result['wpm']} wpm)          +{result['xp']} xp"
                    # If it's a new PB, append that string as well
                    if result['wpm_record'] is True:
                        message = message + "          :champagne: **NEW PB**"

                message = message + '\n'
                position += 1

        else:
            message = "No-one submitted their word counts... I guess I'll just cancel the sprint... :frowning:"

        # Send the message, either via the context or directly to the channel.
        await self.say(message, context, bot)

    async def say(self, message, context = None, bot = None):
        """
        Send a message to the channel, via context if supplied, or direct otherwise
        :param bot:
        :param message:
        :param context:
        :return:
        """
        if context is not None:
            await context.send(message)
            context.deferred = False
            return
        elif bot is not None:
            channel = await bot._http.get_channel(self.channel)
            channel = interactions.Channel(**channel, _client=bot._http)
            return await channel.send(message)

    async def task_start(self, bot) -> bool:
        """
        Scheduled task to start the sprint after a delay
        :param bot:
        :return: bool
        """
        # If the sprint has already finished, we don't need to do anything so we can return True and just have the task deleted.
        if self.is_finished() or self.is_complete():
            return True

        # Post the starting message.
        await self.post_start(bot=bot)

        # Schedule the end task.
        self.__helper.log(f"[TASK] Ran Sprint.task_start for sprint {self.id}")
        Task.schedule('end', self.end, 'sprint', self.id)
        return True

    async def task_end(self, bot) -> bool:
        """
        Scheduled task to end the sprint and ask for final word counts.
        :param bot:
        :return:
        """
        # If the task has already completed fully due to all the users submitting their word counts, we don't need to do this.
        if self.is_complete():
            return True

        # Otherwise, run the end method. This will in turn schedule the complete task.
        self.__helper.log(f"[TASK] Ran Sprint.task_end for sprint {self.id}")
        await self.end_sprint(bot=bot)
        return True

    async def task_complete(self, bot) -> bool:
        """
        Scheduled task to complete the sprint and post the results
        :param bot:
        :return:
        """
         # If the task has already completed fully due to all the users submitting their word counts, we don't need to do this.
        if self.is_complete():
            return True

        # Otherwise, run the complete method. This will in turn schedule the complete task.
        self.__helper.log(f"[TASK] Ran Sprint.task_complete for sprint {self.id}")
        await self.complete_sprint(bot=bot)
        return True

    @staticmethod
    def create(guild, channel, start, end, end_reference, length, createdby, created):
        """
        Create a new sprint
        :param guild:
        :param channel:
        :param start:
        :param end:
        :param end_reference:
        :param length:
        :param createdby:
        :param created:
        :return:
        """
        # Insert the record into the database
        db = Database.instance()
        db.insert('sprints',
                  {
                      'guild': guild,
                      'channel': channel,
                      'start': start,
                      'end': end,
                      'end_reference': end_reference,
                      'length': length,
                      'createdby': createdby,
                      'created': created
                  }
        )

        # Return the new object using this guild id.
        return Sprint(guild)

    @staticmethod
    def calculate_wpm(amount: int, seconds: int) -> float:
        """
        Calculate words per minute, from words written and seconds
        :param amount:
        :param seconds:
        :return:
        """
        mins = seconds / 60
        return round(amount / mins, 1)

    @staticmethod
    async def purge_notifications(context):
        """
        Purge notify notifications of any users who aren't in ths server any more.
        :param context:
        :return:
        """
        # Get a list of the members in this guild.
        guild = await context.get_guild()
        members = await guild.get_all_members()
        guild_members = []
        for member in members:
            guild_members.append(int(member.id))

        # Now go through those asking for notifications and see if they are in the list.
        db = Database.instance()
        count = 0
        notify = db.get_all('user_settings', {'guild': int(context.guild_id), 'setting': 'sprint_notify', 'value': 1})
        notify_ids = [int(row['user']) for row in notify]
        if notify_ids:

            # Go through the users who want notifications and delete any which aren't in the server now.
            for row in notify:
                user_id = int(row['user'])
                if user_id not in guild_members:
                    db.delete('user_settings', {'id': row['id']})
                    count += 1

        return count

    @staticmethod
    def get(id):
        """
        Get a sprint object by its id
        :return: Sprint
        """
        db = Database.instance()
        record = db.get('sprints', {'id': id})
        if record is not None:
            sprint = Sprint(None)
            sprint.id = id
            sprint.load('id')
            return sprint
        else:
            return None