from models.database import Database

class Guild:

    def __init__(self, guild_id):
        self.__db = Database.instance()
        self.id = str(guild_id)
        self.settings = None
        self.disabled = None

    def get_id(self):
        """
        Get the discord ID for the guild
        :return:
        """
        return self.id

    def get_settings(self):
        """
        Get the settings stored for this guild
        :return:
        """

        # If the settings property is None, then load it up first
        if self.settings is None:
            self.load_settings()

        return self.settings

    def get_setting(self, setting):
        """
        Get a specific setting for this guild
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
        Load the settings for this guild from the database
        :return:
        """

        # Get the user_settings records
        records = self.__db.get_all('guild_settings', {'guild': self.id})

        # Reset the stats property
        self.settings = {}

        # Loop through the results and add to the stats property
        for row in records:
            self.settings[row['setting']] = row['value']

    def update_setting(self, setting, value):

        # If the user already has a value for this setting, we want to update
        user_setting = self.get_setting(setting)

        if user_setting:
            return self.__db.update('guild_settings', {'value': value}, {'guild': self.id, 'setting': setting})

        # Otherwise, we want to insert a new one
        else:
            return self.__db.insert('guild_settings', {'guild': self.id, 'setting': setting, 'value': value})

    def load_disabled(self):
        """
        Load list of which commands this guild has disabled
        :return:
        """
        raw = self.get_setting('disabled')
        if raw == None:
            self.disabled = set()
        else:
            self.disabled = set(raw.split(','))

    def disable_enable_command(self, command, disable: bool):
        """
        Disable or enable a command.
        """
        if self.disabled == None:
            self.load_disabled()
        if disable:
            self.disabled.add(command)
        else:
            self.disabled.discard(command)
        self.update_setting('disabled', ','.join(self.disabled))

    def is_command_enabled(self, command):
        """
        Check is a command is enabled for this server.
        """
        if self.disabled == None:
            self.load_disabled()
        return not (command in self.disabled)
