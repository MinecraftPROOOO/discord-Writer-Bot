import interactions, logging, os
from interactions.ext.autosharder import ShardedClient
from interactions.ext.tasks import IntervalTrigger, create_task
from models.database import Database
from models.helper import Helper
from models.task import Task
from config import TOKEN, APP_DIR

bot = ShardedClient(token=TOKEN)
helper = Helper.instance()
db = Database.instance()

logging.basicConfig(format='%(asctime)s - %(message)s')

def load_commands(bot):
    """
    Load all of the commands in the exts/ directory.
    :param bot:
    :return:
    """
    for file in os.listdir(APP_DIR + '/exts'):
        if not file.startswith('_'):
            ext = file.replace('.py', '')
            bot.load(f"exts.{ext}")
            helper.log(f"[BOT] Loaded command extension {ext}")

helper.log("[BOT] Beginning boot process")

db.install()
helper.log("[BOT] Database tables installed")

load_commands(bot)
helper.log("[BOT] Commands loaded")

Task.setup(bot)
helper.log("[BOT] Tasks loaded")

Task.all.start(bot)

bot.start()