import json, math, pprint, pytz
from config import LOG_DIR, APP_DIR
from datetime import datetime, timezone, timedelta, time
from dateutil import relativedelta
from models.singleton import Singleton
from os import path

@Singleton
class Helper:
    """
    Class of generic helper functions
    """

    def log(self, text):
        """
        Write to the bot.log log file
        :param text:
        :return:
        """
        time = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
        file = open(LOG_DIR + '/bot.log', 'a')
        file.write('[' + str(time) + '] ' + str(text) + '\n')
        file.close()

    def dump(self, obj):
        """
        Dump an object
        :param obj:
        :return:
        """
        time = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
        with open(LOG_DIR + '/bot.log', 'a') as file:
            file.write('[' + str(time) + ']\n')
            pprint.pprint(obj, file)
            file.close()

    def error(self, txt):
        """
        Print an error to the bot log
        :param txt:
        :return:
        """
        self.log('[ERROR] ' + str(txt))

    def is_number(self, value):
        """
        Check if a variable is a number (int or can be converted to int)
        :param value:
        :return:
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            return False

    def get(self, file, as_object=True):
        """
        Load a JSON file and return the contents
        :param file:
        :param as_object:
        :return:
        """
        with open(file, 'r') as data:
            if as_object:
                return json.load(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            else:
                return json.load(data)

    def get_asset(self, name: str):
        """
        Get an asset from the assets directory
        :param name:
        :param type:
        :return:
        """

        file = APP_DIR + '/assets/json/' + name + '.json'

        # Try and get the file
        try:
            if path.exists(file):
                return self.get(file, False)
        except FileNotFoundError:
            return False

    def get_midnight_utc(self, timezone, type):
        """
        Given a timezone name, get the UTC timestamp for midnight at the next (day, week, month, year).
        Used in things like goal resets, so that they reset at midnight in the user's timezone.
        :param timezone:
        :param type: daily, weekly, monthly or yearly
        :return:
        """

        tz = pytz.timezone(timezone)
        today = datetime.now(tz)
        relative = 0

        if type == "daily":
            # Today plus 1 day, at midnight.
            relative = relativedelta.relativedelta(days=1, hour=0, minute=0, second=0)
        elif type == "weekly":
            # Next Monday, at midnight.
            relative = relativedelta.relativedelta(days=-today.weekday(), weeks=1, hour=0, minute=0, second=0)
        elif type == "monthly":
            # First of next month, at midnight.
            relative = relativedelta.relativedelta(months=1, day=1, hour=0, minute=0, second=0)
        elif type == "yearly":
            # First of next year, at midnight.
            relative = relativedelta.relativedelta(years=1, month=1, day=1, hour=0, minute=0, second=0)

        next = today + relative
        next_utc = next.astimezone(pytz.utc)

        return int(next_utc.timestamp())

    def is_valid_timezone(self, timezone):
        """
        Check if the timezone string is valid
        :param timezone:
        :return:
        """
        if not timezone:
            return False

        timezones = [x.lower() for x in pytz.all_timezones]
        return timezone.lower() in timezones

    def get_timezone(self, timezone: str):
        """
        Return a pytz timezone from a string
        :param timezone:
        :return:
        """
        return pytz.timezone(timezone) if self.is_valid_timezone(timezone) else None

    def secs_to_mins(self, seconds):
        """
        Convert a number of seconds, into minutes and seconds
        E.g. 65 seconds -> 1 minute 5 seconds
        :param seconds:
        :return: dict
        """
        result = {'m': 0, 's': 0}

        if seconds < 60:
            result['s'] = seconds
        else:
            result['m'] = math.floor(seconds / 60)
            result['s'] = math.ceil(seconds % 60)

        return result

    def secs_to_days(self, seconds):
        """
        Convert a number of seconds, into days, hours, minutes and seconds
        E.g. 65 seconds -> 0 days, 1 minute 5 seconds
        :param seconds:
        :return: dict
        """
        tdelta = timedelta(seconds=seconds)
        d = {"days": tdelta.days}
        d["hours"], rem = divmod(tdelta.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        return d

    def format_secs_to_days(self, seconds):
        """
        Convert a number of seconds into days, hours, minutes & seconds, and return a formatted string
        {
          "days": 3,
          "hours": 2,
          "minutes": 30,
          "seconds": 20
        } -> results in "3 day(s), 2 hour(s), 30 minute(s), 20 second(s)"
        :param seconds:
        :return: string
        """
        dictionary = self.secs_to_days(seconds)
        format = ""
        format += "{days} day(s), " if dictionary['days'] > 0 else ""
        format += "{hours} hour(s), " if dictionary['hours'] > 0 else ""
        format += "{minutes} min(s), " if dictionary['minutes'] > 0 else ""
        format += "{seconds} sec(s), " if dictionary['seconds'] > 0 else ""
        format = format.rsplit(', ', 1)[0]
        return format.format(**dictionary)

    def get_previous_date(self, timezone, type):
        """
        Get the previous date of a given type, e.g. previous day, or previous week, etc...
        :param type:
        :return:
        """
        tz = pytz.timezone(timezone)
        today = datetime.now(tz)

        if type == "daily":
            previous = today - relativedelta.relativedelta(days=1)
            format = '%d %b %Y'
            date = datetime.strftime(previous, format)
        elif type == "weekly":
            previous = today - relativedelta.relativedelta(weeks=1)
            format = '%d %b %Y'
            date = datetime.strftime(previous, format) + ' - ' + datetime.strftime(today, format)
        elif type == "monthly":
            previous = today - relativedelta.relativedelta(months=1)
            format = '%b %Y'
            date = datetime.strftime(previous, format)
        elif type == "yearly":
            previous = today - relativedelta.relativedelta(years=1)
            format = '%Y'
            date = datetime.strftime(previous, format)

        return date