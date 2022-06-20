import math, time
from models.database import Database
from models.helper import Helper
from models.experience import Experience

class User:

    def __init__(self, id, guild_id, context=None, bot=None, channel=None):

        self.__db = Database.instance()
        self.__context = context
        self.__bot = bot
        self.__channel = channel
        self.__helper = Helper.instance()

        self.id = str(id)
        self.guild_id = str(guild_id)
        self.settings = None
        self.stats = None
        self.xp = None
        self.records = None

    def get_mention(self):
        """
        Get the mention string for this user
        :return:
        """
        return f'<@{self.id}>'

    async def say(self, message):
        """
        Send a message to the channel, via context if supplied, or direct otherwise
        :param message:
        :param context:
        :return:
        """
        if self.__context is not None:
            await self.__context.send(message)
            self.__context.deferred = False
            return
        elif self.__bot is not None:
            channel = await self.__bot._http.get_channel(self.channel)
            channel = interactions.Channel(**channel, _client=self.__bot._http)
            return await channel.send(message)

    def get_settings(self):
        """
        Get all of the users settings
        :return:
        """

        # If the settings property is None, then load it up first
        if self.settings is None:
            self.load_settings()

        return self.settings

    def get_setting(self, setting):
        """
        Get a specific setting for this user
        :param setting:
        :return:
        """

        # If the settings property is None, then load it up first
        if self.settings is None:
            self.load_settings()

        # Now check if the key exists in the dictionary
        if setting in self.settings:
            return self.settings[setting]
        else:
            return None

    def load_settings(self):
        """
        Load all of the user's settings from the database
        :return:
        """

        # Get the user_settings records
        records = self.__db.get_all('user_settings', {'user': self.id})

        # Reset the stats property
        self.settings = {}

        # Loop through the results and add to the stats property
        for row in records:
            self.settings[row['setting']] = row['value']

    def update_setting(self, setting, value):
        """
        Update the value of a setting for this user
        :param setting:
        :param value:
        :return:
        """

        # If the user already has a value for this setting, we want to update
        user_setting = self.get_setting(setting)

        # Update the value in the array
        self.settings[setting] = value

        if user_setting:
            return self.__db.update('user_settings', {'value': value}, {'user': self.id, 'setting': setting})

        # Otherwise, we want to insert a new one
        else:
            return self.__db.insert('user_settings', {'user': self.id, 'setting': setting, 'value': value})

    def get_guild_setting(self, guild, setting):
        """
        Get a user setting on a specific guild.
        This is mostly just used for things like sprint notifications. It's not settings they can manually set with the !myset command
        This is used more rarely, so we won't bother loading the settings into an array, we'll just go fetch it
        :param guild:
        :param int setting:
        :return:
        """
        return self.__db.get('user_settings', {'user': self.id, 'setting': setting, 'guild': str(guild)})

    def set_guild_setting(self, guild, setting, value):
        """
        Set a user's setting for a specific guild
        :param guild:
        :param str setting:
        :param str value:
        :return: Result of update or insert query
        """
        result = self.get_guild_setting(guild, setting)
        if result:
            return self.__db.update('user_settings', {'value': value}, {'id': result['id']})
        else:
            return self.__db.insert('user_settings',
                                    {'user': self.id, 'guild': str(guild), 'setting': setting, 'value': value})

    def get_stat(self, name):
        """
        Get a specific statistic for this user
        :param name:
        :return:
        """

        # If the stats property is None, then load it up first
        if self.stats is None:
            self.load_stats()

        # Now check if the key exists in the dictionary
        if name in self.stats:
            return self.stats[name]
        else:
            return 0

    def load_stats(self):
        """
        Load all the user's stats from the database
        :return:
        """

        # Get the user_stats records
        records = self.__db.get_all('user_stats', {'user': self.id})

        # Reset the stats property
        self.stats = {}

        # Loop through the results and add to the stats property
        for row in records:
            self.stats[row['name']] = row['value']

    def update_stat(self, name, amount):
        """
        Update a specific stat for the user
        :param name:
        :param amount:
        :return:
        """

        # If the user already has a value for this stat, we want to update
        user_stat = self.get_stat(name)

        # Update the value in the array
        self.stats[name] = amount

        if user_stat:
            return self.__db.update('user_stats', {'value': amount}, {'user': self.id, 'name': name})

        # Otherwise, we want to insert a new one
        else:
            return self.__db.insert('user_stats', {'user': self.id, 'name': name, 'value': amount})

    def add_stat(self, name, amount):
        """
        Increment a specific stat for the user
        :param name:
        :param amount:
        :return:
        """

        # If the user already has a value for this stat, we want to get their current amount so we can increment it
        user_stat = self.get_stat(name)

        if user_stat:
            amount = int(amount) + int(user_stat)

        # Now return the update_stat with the new amount (if incremented)
        return self.update_stat(name, amount)

    def get_xp(self):
        """
        Get the XP this user has
        :return:
        """
        # If xp is None then we have't got the record yet, so try and get it.
        if self.xp is None:
            self.load_xp()

        return self.xp

    def load_xp(self):
        """
        Load the user's XP from the database.
        :return:
        """
        xp = self.__db.get('user_xp', {'user': self.id})
        if xp:
            experience = Experience(xp['xp'])
            self.xp = {'id': xp['id'], 'xp': xp['xp'], 'lvl': experience.get_level(),
                        'next': experience.get_next_level_xp()}

    def get_xp_bar(self):
        """
        Get the XP bar for the user
        :return:
        """
        xp = self.get_xp()

        if xp is not None:
            goal = xp['xp'] + xp['next']
            return f"**Level {xp['lvl']}** ({xp['xp']}/{goal})"
        else:
            return '-'

    def add_xp(self, amount):
        """
        Add XP to the user
        :param amount:
        :return:
        """
        user_xp = self.get_xp()
        if user_xp:
            amount += int(user_xp['xp'])

        return self.update_xp(amount)

    async def update_xp(self, amount):
        """
        Update the user's XP to a specific amount
        :param amount:
        :return:
        """
        user_xp = self.get_xp()

        # If they already have an XP record, update it
        if user_xp:
            current_level = user_xp['lvl']
            result = self.__db.update('user_xp', {'xp': amount}, {'id': user_xp['id']})
        else:
            # Otherwise, insert a new one
            current_level = 1
            result = self.__db.insert('user_xp', {'user': self.id, 'xp': amount})

        # Reload the XP onto the user object and into the user_xp variable
        self.load_xp()
        user_xp = self.get_xp()

        # If the level now is higher than it was, print the level up message
        if user_xp['lvl'] > current_level:
            await self.say(f":tada: Congratulations {self.get_mention()}, you are now **Level {user_xp['lvl']}**")

        return result

    def get_challenge(self):
        """
        Get user's current challenge
        :return:
        """
        return self.__db.get('user_challenges', {'user': self.id, 'completed': 0})

    def set_challenge(self, challenge, xp):
        """
        Set a challenge for the user
        :param challenge:
        :param xp:
        :return:
        """
        current_challenge = self.get_challenge()
        if not current_challenge:
            return self.__db.insert('user_challenges', {'user': self.id, 'challenge': challenge, 'xp': xp})
        else:
            return False

    def delete_challenge(self):
        """
        Delete current challenge for user
        :return:
        """
        return self.__db.delete('user_challenges', {'user': self.id})

    def complete_challenge(self, id):
        """
        Mark current challenge as completed for user
        :param id:
        :return:
        """
        now = int(time.time())
        return self.__db.update('user_challenges', {'completed': now}, {'id': id})

    def get_record(self, name):
        """
        Get a specific user record for this user
        :param name:
        :return:
        """

        # If the records property is None, then load it up first
        if self.records is None:
            self.load_records()

        # Now check if the key exists in the dictionary
        if name in self.records:
            return self.records[name]
        else:
            return None

    def load_records(self):
        """
        Load the user's records
        :return:
        """

        # Get the user_settings records
        records = self.__db.get_all('user_records', {'user': self.id})

        # Reset the stats property
        self.records = {}

        # Loop through the results and add to the stats property
        for row in records:
            self.records[row['record']] = row['value']

    def update_record(self, name, value):
        """
        Update a user record for this user
        :param name:
        :param value:
        :return:
        """

        # If the user already has a value for this record, we want to update
        user_record = self.get_record(name)

        # Update the value in the array
        self.records[name] = value

        if user_record:
            return self.__db.update('user_records', {'value': value}, {'user': self.id, 'record': name})

        # Otherwise, we want to insert a new one
        else:
            return self.__db.insert('user_records', {'user': self.id, 'record': name, 'value': value})

    def reset_projects(self):
        """
        Delete all the user's projects
        :return:
        """
        self.__db.delete('projects', {'user': self.id})

    def reset(self):
        """
        Reset the entire user's stats, records, xp, etc...
        :return:
        """
        self.__db.delete('user_challenges', {'user': self.id})
        self.__db.delete('user_goals', {'user': self.id})
        self.__db.delete('user_records', {'user': self.id})
        self.__db.delete('user_stats', {'user': self.id})
        self.__db.delete('user_xp', {'user': self.id})
        self.__db.delete('projects', {'user': self.id})

    def calculate_user_reset_time(self, type):
        """
        Calculate the next reset time for this type of user goal, based on their timezone.
        @param type:
        @return:
        """

        timezone = self.get_setting('timezone') or 'UTC'
        return self.__helper.get_midnight_utc(timezone, type)

    def get_goal(self, type):
        """
        Get the user_goal record for this user and type
        :param type:
        :return:
        """
        return self.__db.get('user_goals', {'user': self.id, 'type': type})

    def get_goal_progress(self, type):
        """
        Get the user's goal progress
        :param type:
        :return:
        """
        progress = {
            'percent': 0,
            'done': 0,
            'left': 0,
            'goal': 0,
            'current': 0,
            'str': ''
        }

        user_goal = self.get_goal(type)
        if user_goal is not None:
            percent = math.floor((user_goal['current'] / user_goal['goal']) * 100)
            progress['done'] = math.floor(percent / 10)
            progress['left'] = 10 - progress['done']

            progress['percent'] = percent
            progress['goal'] = user_goal['goal']
            progress['current'] = user_goal['current']
            progress['str'] = '[' + ('-' * progress['done']) + ('  ' * progress['left']) + ']'

        # Can't be more than 10 or less than 0
        if progress['done'] > 10:
            progress['done'] = 10

        if progress['left'] < 0:
            progress['left'] = 0

        return progress

    def set_goal(self, type, value):
        """
        Set a goal for the user
        :param type:
        :param value:
        :return:
        """

        user_goal = self.get_goal(type)
        next_reset = self.calculate_user_reset_time(type)

        if user_goal:
            return self.__db.update('user_goals', {'goal': value, 'reset': next_reset}, {'id': user_goal['id']})
        else:
            return self.__db.insert('user_goals',
                                    {'type': type, 'goal': value, 'user': self.id, 'current': 0, 'completed': 0,
                                     'reset': next_reset})

    def delete_goal(self, type):
        """
        Delete a user's goal
        :param type:
        :return:
        """
        return self.__db.delete('user_goals', {'user': self.id, 'type': type})

    async def add_to_goals(self, amount):
        """
        Add word written to all goals the user is running
        :param amount:
        :return:
        """
        for goal in ['daily', 'weekly', 'monthly', 'yearly']:
            await self.add_to_goal(goal, amount)

    async def add_to_goal(self, type, amount):
        """
        Add words written to a goal for the user
        :param type:
        :param amount:
        :return:
        """

        user_goal = self.get_goal(type)
        if user_goal:

            value = int(amount) + int(user_goal['current'])
            if value < 0:
                value = 0

            # Is the goal completed now?
            already_completed = user_goal['completed']
            completed = user_goal['completed']
            if value >= user_goal['goal'] and not already_completed:
                completed = 1

            self.__db.update('user_goals', {'current': value, 'completed': completed}, {'id': user_goal['id']})

            # If we just met the goal, increment the XP and print out a message
            if completed and not already_completed:
                # Increment stat of goals completed
                self.add_stat(type + '_goals_completed', 1)

                # Increment XP
                await self.add_xp(Experience.XP_COMPLETE_GOAL[type])

                # Print message
                await self.say(f"{self.get_mention()} has met their {type} goal of {user_goal['goal']} words!       +{Experience.XP_COMPLETE_GOAL[type]}xp!")

    def update_goal(self, type, amount):
        """
        Just update the value of a goal, without changing anything else
        @param type:
        @param amount:
        @return:
        """
        user_goal = self.get_goal(type)
        if user_goal:
            return self.__db.update('user_goals', {'current': amount}, {'id': user_goal['id']})
        else:
            return False

    def get_goal_history(self, type):
        """
        Get the user's goal history for the specified goal type
        :param type:
        :return:
        """

        # Daily goals we want to get a maximum of 14 records.
        if type == 'daily':
            max = 14

        # Weekly goals we want to get a maximum of 4 results.
        elif type == 'weekly':
            max = 4

        # Monthly goals we want to get a maximum of 12 results.
        elif type == 'monthly':
            max = 12

        # Yearly goals we can get as many as we like.
        else:
            max = None

        return self.__db.get_all('user_goals_history', {'type': type, 'user': self.id}, '*', ['id DESC'], max)

    def reset_goal(self, record):
        """
        Reset a user's goal, inserting the current values into the history table and updating their current record.
        :param record:
        :return:
        """
        # Add the current values to a new record in the history table.
        self.__db.insert('user_goals_history', {
            'user': record['user'],
            'type': record['type'],
            'date': self.get_previous_goal_date(record['type']),
            'goal': record['goal'],
            'result': record['current'],
            'completed': record['completed']
        })

        # Calculate the next reset time for this goal.
        next = self.calculate_user_reset_time(record['type'])

        # Update the goal record with the new reset time, resetting the completed and current values to 0.
        self.__db.update('user_goals', {'completed': 0, 'current': 0, 'reset': next}, {'id': record['id']})

    def get_previous_goal_date(self, type):
        """
        Given a type of goal, get the previous goal's date, for the history table.
        E.g. a daily goal would give you yesterday's date. A monthly goal would give you the first of last month.
        :param type:
        :return:
        """
        timezone = self.get_setting('timezone') or 'UTC'
        return self.__helper.get_previous_date(timezone, type)

    def get_most_recent_sprint(self, current_sprint):
        """
        Get the user's most recent sprint record, not including the current one (if they have joined already)
        :return:
        """
        return self.__db.get_sql('SELECT * FROM sprint_users WHERE user = %s AND sprint != %s ORDER BY id DESC LIMIT 1',
                                 [self.id, current_sprint])


