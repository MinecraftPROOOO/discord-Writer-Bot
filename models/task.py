import time
from models.database import Database
from models.helper import Helper
from interactions.ext.tasks import IntervalTrigger, create_task

# How many seconds between each call of the task loop.
TASK_LOOP_TIME = 15

class Task:

    def __init__(self, id):
        """
        Load a Task object by its ID
        :param id:
        """
        self.__db = Database.instance()
        self.__helper = Helper.instance()
        self.id = None

        record = self.__db.get('tasks', {'id': id})
        if record:
            self.id = record['id']
            self.type = record['type']
            self.time = record['time']
            self.object = record['object']
            self.object_id = record['objectid']
            self.processing = record['processing']
            self.recurring = record['recurring']
            self.run_every_seconds = record['runeveryseconds']

    def is_valid(self):
        """
        Check if the Task object is valid
        :return:
        """
        return self.id is not None

    def is_recurring(self):
        """
        Check if the task is a recurring one or not
        :return:
        """
        return int(self.recurring) == 1

    def is_processing(self):
        """
        Check if this task is already running
        :return:
        """
        return self.processing == 1

    def start_processing(self, value):
        """
        Mark the task as processing or not
        :param value: 0 or 1
        :return:
        """
        return self.__db.update('tasks', {'processing': value}, {'id': self.id})

    def set_recur(self):
        """
        Set the next time this recurring task should be run
        :return:
        """
        now = int(time.time())
        next = now + int(self.run_every_seconds)
        return self.__db.update('tasks', {'time': next}, {'id': self.id})

    def delete(self):
        """
        Delete the task
        :return:
        """
        return self.__db.delete('tasks', {'id': self.id})

    async def run(self, bot):
        """
        Run the task
        :param bot:
        :return:
        """
        # If the task is already processing, don't go any further.
        if self.is_processing():
            return True

        # Mark the task as processing so other shards don't pick it up.
        self.start_processing(1)

        # Build a variable to store the method name to run
        method = 'task_' + str(self.type)

        # Start off with a False and see if we can successfully run and turn that to True
        result = False

        if self.object == 'goal':

            from models.goal import Goal

            goal = Goal()
            result = await getattr(goal, method)(bot)

        elif self.object == 'sprint':

            from models.sprint import Sprint

            sprint = Sprint.get(self.object_id)
            if sprint.is_valid():
                result = await getattr(sprint, method)(bot)
            else:
                result = True

        else:
            self.__helper.error('Invalid task object: ' + str(self.object))

        # If we finished the task, and it's not a recurring one, delete it.
        if result is True and not self.is_recurring():
            self.delete()
        else:
            self.start_processing(0)

        # If it's a recurring task, set its next run time.
        if self.is_recurring():
            self.set_recur()

        return result

    @staticmethod
    def cancel(object, object_id, type=None):
        """
        Cancel all tasks related to a specific object
        :param object:
        :param object_id:
        :param type:
        :return:
        """
        db = Database.instance()

        params = {'object': object, 'objectid': object_id}
        if type is not None:
            params['type'] = type

        return db.delete('tasks', params)

    @staticmethod
    def get(type, object, object_id):
        """
        Check to see if a task of this type and object_id already exists
        :return:
        """
        db = Database.instance()
        return db.get('tasks', {'type': type, 'object': object, 'objectid': object_id})

    @staticmethod
    def schedule(type, time, object, object_id):
        """
        Schedule the task in the database
        :return:
        """
        db = Database.instance()

        # If this task already exists, just update its time.
        record = Task.get(type, object, object_id)
        if record:
            return db.update('tasks', {'time': time}, {'id': record['id']})
        else:
            # Otherwise, create one.
            return db.insert('tasks', {'type': type, 'time': time, 'object': object, 'objectid': object_id})

    @staticmethod
    def setup(bot):
        """
        Setup the tasks to run in the background
        :param bot:
        :return:
        """
        db = Database.instance()

        # Setup the task records for Goal.
        from models.goal import Goal
        Goal.setup_tasks()

        # Restart all tasks which are marked as processing, in case the bot dropped out during the process.
        db.update('tasks', {'processing': 0})


    @staticmethod
    async def run_all(bot):
        """
        Start running all of the tasks that need running
        :param bot:
        :return:
        """
        now = int(time.time())
        db = Database.instance()

        pending = db.get_all_sql('SELECT id FROM tasks WHERE time <= %s ORDER BY id ASC', [now])
        for row in pending:
            task = Task(row['id'])
            if task.is_valid():
                await task.run(bot)

    @create_task(IntervalTrigger(TASK_LOOP_TIME))
    async def all(bot):
        """
        Start the task loop
        :return:
        """
        helper = Helper.instance()
        helper.log('[TASK] Checking for pending tasks...')

        # Run all of the tasks
        await Task.run_all(bot)

