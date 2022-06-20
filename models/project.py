import interactions
from models.database import Database

class Project:

    GENRES = {
        'fantasy': {'name': 'Fantasy', 'emote': 'man_mage:'},
        'scifi': {'name': 'Sci-Fi', 'emote': 'ringed_planet:'},
        'romance': {'name': 'Romance', 'emote': 'heart:'},
        'horror': {'name': 'Horror', 'emote': 'skull:'},
        'fiction': {'name': 'Fiction', 'emote': 'blue_book:'},
        'nonfiction': {'name': 'Non-Fiction', 'emote': 'bookmark:'},
        'short': {'name': 'Short Fiction', 'emote': 'shorts:'},
        'mystery': {'name': 'Mystery', 'emote': 'detective:'},
        'thriller': {'name': 'Thriller', 'emote': 'scream:'},
        'crime': {'name': 'Crime', 'emote': 'oncoming_police_car:'},
        'erotic': {'name': 'Erotic', 'emote': 'hot_pepper:'},
        'comic': {'name': 'Comic', 'emote': 'art:'},
        'action': {'name': 'Action', 'emote': 'gun:'},
        'drama': {'name': 'Drama', 'emote': 'performing_arts:'},
        'fanfic': {'name': 'Fan Fiction', 'emote': 'art:'},
        'literary': {'name': 'Literary Fiction', 'emote': 'notebook_with_decorative_cover:'},
        'adventure': {'name': 'Adventure', 'emote': 'mountain_snow:'},
        'suspense': {'name': 'Suspense', 'emote': 'worried:'},
        'ya': {'name': 'Young Adult', 'emote': 'adult:'},
        'kids': {'name': 'Kids', 'emote': 'children_crossing:'},
        'academic': {'name': 'Academic', 'emote': 'books:'},
        'challenge': {'name': 'Challenge', 'emote': 'mountain:'},
    }

    STATUSES = {
        'planning': {'name': 'Planning', 'emote': 'thinking:'},
        'progress': {'name': 'In Progress', 'emote': 'writing_hand:'},
        'editing': {'name': 'Editing', 'emote': 'pencil:'},
        'published': {'name': 'Published', 'emote': 'notebook_with_decorative_cover:'},
        'finished': {'name': 'Finished', 'emote': 'white_check_mark:'},
        'abandoned': {'name': 'Abandoned', 'emote': 'wastebasket:'},
        'submitted': {'name': 'Submitted', 'emote': 'postbox:'},
        'rejected': {'name': 'Rejected', 'emote': 'x:'},
        'hiatus': {'name': 'On Hiatus', 'emote': 'clock4:'},
        'rewriting': {'name': 'Re-writing', 'emote': 'repeat:'},
        'accepted': {'name': 'Accepted', 'emote': 'ballot_box_with_check:'},
    }

    DESCRIPTION_CHAR_LIMIT = 2000

    def __init__(self, id: int):
        """
        Instantiate Project object
        :param id:
        """
        self.__db = Database.instance()

        record = self.__db.get('projects', {'id': id})
        if record:
            self.id = record['id']
            self.user = record['user']
            self.name = record['name']
            self.shortname = record['shortname']
            self.words = record['words']
            self.status = record['status']
            self.genre = record['genre']
            self.description = record['description']
            self.link = record['link']
            self.image = record['image']
            self.completed = record['completed']

    def save(self):
        """
        Save the current state of the project
        :return:
        """
        return self.__db.update('projects', {
            'name': self.name,
            'shortname': self.shortname,
            'words': self.words,
            'status': self.status,
            'genre': self.genre,
            'description': self.description,
            'link': self.link,
            'image': self.image,
            'completed': self.completed
        }, {
            'id' : self.id
        })

    def embed(self, context):
        """
        Get the embed object to send when viewing this individual project
        :param context:
        :return:
        """
        footer = interactions.EmbedFooter(
            text=f"Requested by {context.author.user.username}#{context.author.user.discriminator}",
            icon_url=f"{context.author.user.avatar_url}",
        )

        title = self.name
        description = self.description or "No description yet"
        url = self.link or None
        words = str("{:,}".format(self.words))

        embed = interactions.Embed(
            title=title,
            url=url,
            description=description,
            footer=footer,
        )

        if self.image is not None:
            embed.set_thumbnail(self.image)

        if self.status is not None:
            embed.add_field(name="Status", value=Project.STATUSES[self.status]['name'], inline=True)

        if self.genre is not None:
            embed.add_field(name="Genre", value=Project.GENRES[self.genre]['name'], inline=True)

        embed.add_field(name="Word Count", value=words, inline=True)

        return embed

    def delete(self):
        """
        Delete the project
        :return:
        """
        return self.__db.delete('projects', {'id': self.id})

    @staticmethod
    def validate(user, shortname, title):
        """
        Validate if the shortname and title are ok and not in use by the user already
        :param shortname:
        :param title:
        :return:
        """
        if len(title) > 100:
            return "Title cannot be more than 100 characters long"

        if len(shortname) > 10:
            return "Shortname cannot be more than 10 characters long"

        if Project.get(user.id, shortname) is not None:
            return f"You already have a project with that shortname ({shortname})"

        return True

    @staticmethod
    def get(user_id: int, shortname: str):
        """
        Get a user's project by their ID and the shortname of the project
        :param shortname:
        :return:
        """
        """Try to get a project with a given shortname, for a given user"""
        record = Database.instance().get('projects', {'user': user_id, 'shortname': shortname})
        if record is None:
            return None

        return Project(record['id'])

    @staticmethod
    def all(user_id: int, status: str = None, genre: str = None):
        """
        Get all of the user's projects
        :param user_id:
        :return:
        """
        conditions = {'user': user_id}
        if status is not None:
            conditions['status'] = status
        if genre is not None:
            conditions['genre'] = genre

        records = Database.instance().get_all('projects', conditions, ['id'], ['name', 'shortname', 'words'])
        projects = []
        for record in records:
            projects.append(Project(record['id']))
        return projects

    @staticmethod
    def create(user, title, shortname):
        """
        Create a project for the user
        :param title:
        :param shortname:
        :return:
        """
        return Database.instance().insert('projects', {
            'user': user.id,
            'name': title,
            'shortname': shortname
        })
