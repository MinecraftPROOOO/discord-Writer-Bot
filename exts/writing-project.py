import interactions
from models.database import Database
from models.guild import Guild
from models.helper import Helper
from models.project import Project
from models.user import User
from validator_collection import checkers

class ProjectCommand(interactions.ext.autosharder.ShardedExtension):

    MAX_MESSAGES = 2
    MAX_MESSAGE_LENGTH = 2500

    def __init__(self, client: interactions.Client):
        self.bot: interactions.Client = client
        self.db = Database.instance()
        self.helper = Helper.instance()

    @interactions.extension_command(
        name="project",
        description="Project commands",
        options=[
            interactions.Option(
                name="create",
                description="Create a new project",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Project shortname/code",
                        required=True,
                        type=interactions.OptionType.STRING
                    ),
                    interactions.Option(
                        name="title",
                        description="Project title",
                        required=True,
                        type=interactions.OptionType.STRING
                    )
                ]
            ),
            interactions.Option(
                name="list",
                description="List your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="genre",
                        description="List only projects matching this genre",
                        type=interactions.OptionType.STRING,
                        required=False,
                        choices=[
                            interactions.Choice(name=value['name'], value=key) for key, value in Project.GENRES.items()
                        ]
                    ),
                    interactions.Option(
                        name="status",
                        description="List only projects matching this status",
                        type=interactions.OptionType.STRING,
                        required=False,
                        choices=[
                            interactions.Choice(name=value['name'], value=key) for key, value in Project.STATUSES.items()
                        ]
                    )
                ]
            ),
            interactions.Option(
                name="view",
                description="View full information about one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to view?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    )
                ]
            ),
            interactions.Option(
                name="change-shortname",
                description="Change the shortname of one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Old shortname",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                    interactions.Option(
                        name="new_shortname",
                        description="New shortname",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                ]
            ),
            interactions.Option(
                name="change-title",
                description="Change the title of one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to change the title of?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                    interactions.Option(
                        name="title",
                        description="New title",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                ]
            ),
            interactions.Option(
                name="change-description",
                description="Change the description of one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to change the description of?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                    interactions.Option(
                        name="description",
                        description="New description",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                ]
            ),
            interactions.Option(
                name="change-genre",
                description="Change the genre of one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to change the genre of?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                    interactions.Option(
                        name="genre",
                        description="New genre",
                        type=interactions.OptionType.STRING,
                        required=True,
                        choices=[
                            interactions.Choice(name=value['name'], value=key) for key, value in Project.GENRES.items()
                        ]
                    ),
                ]
            ),
            interactions.Option(
                name="change-status",
                description="Change the status of one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to change the status of?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                    interactions.Option(
                        name="status",
                        description="New status",
                        type=interactions.OptionType.STRING,
                        required=True,
                        choices=[
                            interactions.Choice(name=value['name'], value=key) for key, value in Project.STATUSES.items()
                        ]
                    ),
                ]
            ),
            interactions.Option(
                name="change-link",
                description="Change the web link of one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to change the link of?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                    interactions.Option(
                        name="link",
                        description="New link (e.g. Goodreads, Amazon, Personal website, etc...)",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                ]
            ),
            interactions.Option(
                name="change-image",
                description="Change the image URL of one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to change the image of?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                    interactions.Option(
                        name="image",
                        description="New image URL",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                ]
            ),
            interactions.Option(
                name="delete",
                description="Delete one of your projects",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to delete?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    )
                ]
            ),
            interactions.Option(
                name="update",
                description="Update the word count of your project",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="shortname",
                        description="Which project do you want to set the word count of?",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                    interactions.Option(
                        name="amount",
                        description="New word count to set for the project (See `/wrote` for incrementing)",
                        type=interactions.OptionType.INTEGER,
                        required=True,
                    )
                ]
            )
        ],
    )
    async def _project(self, context: interactions.CommandContext, sub_command: str,
                       shortname: str = None, title: str = None, genre: str = None, status: str = None,
                       description: str = None, link: str = None, image: str = None, new_shortname: str = None,
                       amount: int = None):
        """
        Project sub commands
        :param context:
        :param sub_command:
        :param shortname:
        :param title:
        :return:
        """
        ephemeral = sub_command in ['change-shortname', 'change-title', 'change-description', 'change-genre', 'change-status', 'change-link', 'change-image']

        # Send "bot is thinking" message, to avoid failed commands if latency is high.
        await context.defer(ephemeral=ephemeral)

        # Is command enabled for guild?
        if not Guild(context.guild_id).is_command_enabled('project'):
            return await context.send('Your guild has disabled this command', ephemeral=ephemeral)

        user = User(context.author.id, context.guild_id, context)

        if sub_command == 'create':

            validate = Project.validate(user, shortname, title)
            if validate is not True:
                return await context.send(f"{user.get_mention()}, {validate}", ephemeral=ephemeral)

            Project.create(user, title, shortname)
            return await context.send(f"{user.get_mention()}, project created: {title} ({shortname})", ephemeral=ephemeral)

        elif sub_command == 'view':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            return await context.send(embeds=project.embed(context), ephemeral=ephemeral)

        elif sub_command == 'change-shortname':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            # Check they don't already have a project with the new shortname.
            check = Project.get(user.id, new_shortname)
            if check is not None:
                return await context.send(f"{user.get_mention()}, you already have a project with that shortname ({new_shortname})", ephemeral=ephemeral)

            project.shortname = new_shortname
            project.save()
            return await context.send(f"{user.get_mention()}, project renamed from _{project.name}_ ({shortname}), to: _{project.name}_ ({new_shortname})", ephemeral=ephemeral)

        elif sub_command == 'change-title':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            old_title = project.name
            project.name = title
            project.save()
            return await context.send(f"{user.get_mention()}, project renamed from _{old_title}_ ({project.shortname}), to: _{title}_ ({project.shortname})", ephemeral=ephemeral)

        elif sub_command == 'change-description':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            if len(description) > Project.DESCRIPTION_CHAR_LIMIT:
                return await context.send(f"{user.get_mention()}, description cannot be more than 2000 characters", ephemeral=ephemeral)

            project.description = description
            project.save()
            return await context.send(f"{user.get_mention()}, project description updated", ephemeral=ephemeral)

        elif sub_command == 'change-genre':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            project.genre = genre
            project.save()
            return await context.send(f"{user.get_mention()}, project genre updated to: {Project.GENRES[genre]['name']}", ephemeral=ephemeral)

        elif sub_command == 'change-status':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            project.status = status
            project.save()
            return await context.send(f"{user.get_mention()}, project status updated to: {Project.STATUSES[status]['name']}", ephemeral=ephemeral)

        elif sub_command == 'change-link':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            if not checkers.is_url(link):
                return await context.send(f"{user.get_mention()}, link must be a valid URL", ephemeral=ephemeral)

            project.link = link
            project.save()
            return await context.send(f"{user.get_mention()}, project link updated to: {link}", ephemeral=ephemeral)

        elif sub_command == 'change-image':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            if not checkers.is_url(image):
                return await context.send(f"{user.get_mention()}, image link must be a valid URL", ephemeral=ephemeral)

            project.image = image
            project.save()
            return await context.send(f"{user.get_mention()}, project image updated to: {image}", ephemeral=ephemeral)

        elif sub_command == 'delete':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            project.delete()

            return await context.send(f"{user.get_mention()}, project deleted: {project.name} ({project.shortname})", ephemeral=ephemeral)

        elif sub_command == 'update':

            project = Project.get(user.id, shortname)
            if not project:
                return await context.send(f"{user.get_mention()}, you do not have a project with that shortname ({shortname})", ephemeral=ephemeral)

            project.words = amount
            project.save()

            return await context.send(f"{user.get_mention()}, project word count updated to: {amount}", ephemeral=ephemeral)

        elif sub_command == 'list':

            filters = []
            length = 0

            if genre is not None and Project.GENRES.get(genre):
                filters.append(Project.GENRES.get(genre)['name'])
            if status is not None and Project.STATUSES.get(status):
                filters.append(Project.STATUSES.get(status)['name'])

            allfields = []
            fields = []
            projects = Project.all(user.id, status=status, genre=genre)

            # Check they have some projects.
            if len(projects) < 1:
                return await context.send(f"{user.get_mention()}, you do not have any projects", ephemeral=ephemeral)

            for project in projects:

                title = f"{project.name} [{project.shortname}]"
                description = ""

                if project.description is not None:
                    description += "_" + project.description + "_\n"

                if project.genre is not None:
                    if Project.GENRES.get(project.genre):
                        genre = Project.GENRES[project.genre]['name']
                    else:
                        genre = "-"
                    description += f"Genre: {genre}\n"

                if project.status is not None:
                    if Project.STATUSES.get(project.status):
                        status = Project.STATUSES[project.status]['name']
                    else:
                        status = "-"
                    description += f"Status: {status}\n"

                if description == "":
                    description = "No description yet"

                length = length + len(title) + len(description)

                # if we've hit the character limit, send these fields to the allfields array and reset things.
                if length > self.MAX_MESSAGE_LENGTH:

                    allfields.append(fields)
                    fields = []
                    length = 0

                # Append project info to fields array.
                fields.append(interactions.EmbedField(
                    name=title,
                    value=description,
                    inline=False
                ))

            # If we have left over fields which didn't hit the limit, append them to allfields now.
            if len(fields) > 0:
                allfields.append(fields)

            # If they have too many projects and it would send more than 2 messages, make them hidden to other users.
            hidden = False
            if len(allfields) > self.MAX_MESSAGES:
                hidden = True

            # Now go through the fields we split into groups to send all the embedded messages.
            for splitfields in allfields:

                embed = interactions.Embed(
                    title="Your Projects",
                    description=f"Here are your {'/'.join(filters)} projects...",
                    fields=splitfields
                )

                await context.send(embeds=embed, ephemeral=hidden)
                context.deferred = False



def setup(client):
    ProjectCommand(client)