import pytz, time
from models.database import Database
from models.helper import Helper
from models.user import User

class Goal:

    # How many seconds between each check for goal resets. (30 mins).
    TASK_RESET_LOOP_TIME = 1800

    def __init__(self):
        """
        Instantiate the object
        """
        self.__db = Database.instance()
        self.__helper = Helper.instance()

    async def task_reset(self, bot):
        """
        The scheduled task to reset user goals at midnight
        :param bot:
        :return:
        """
        # Find all the user_goal records which are due a reset
        now = int(time.time())

        records = self.__db.get_all_sql('SELECT * FROM user_goals WHERE reset <= %s', [now])
        completed = 0
        for record in records:

            # Calculate the next reset time for the goal, depending on its type.
            user = User(record['user'], 0)
            try:
                user.reset_goal(record)
                completed += 1
            except pytz.exceptions.UnknownTimeZoneError:
                self.__helper.error('Invalid timezone (' + user.get_setting('timezone') + ') for user ' + str(record['user']))

        self.__helper.log(f"[TASK] Ran Goal.task_reset for {completed}/{len(records)} records")

        return True

    @staticmethod
    def setup_tasks():
        """
        Setup the task records
        :return:
        """
        # Delete task records and re-create, in case they got stuck somehow.
        db = Database.instance()
        db.delete('tasks', {'object': 'goal', 'type': 'reset'})
        db.insert('tasks', {'object': 'goal', 'time': 0, 'type': 'reset', 'recurring': 1, 'runeveryseconds': Goal.TASK_RESET_LOOP_TIME})
