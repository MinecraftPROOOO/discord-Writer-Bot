import dotenv, os

dotenv.load_dotenv()

global TOKEN, VERSION, SUPPORT_SERVER, DB_HOST, DB_USER, DB_PASS, DB_NAME, APP_DIR, LOG_DIR, INVITE_URL, WIKI_URL

TOKEN = os.getenv("TOKEN")
VERSION = os.getenv("VERSION")
SUPPORT_SERVER = os.getenv("SUPPORT_SERVER")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
INVITE_URL = os.getenv("INVITE_URL")
WIKI_URL = os.getenv("WIKI_URL")
APP_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = APP_DIR + '/logs'