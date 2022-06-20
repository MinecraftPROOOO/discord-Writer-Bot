import random
import re
import string
from models.helper import Helper

class Generator:

    MAX_AMOUNT = 25
    DEFAULT_AMOUNT = 10
    MAX_RETRIES = 10

    SUPPORTED_TYPES = {
        'char': 'Character',
        'place': 'Place',
        'land': 'Land',
        'idea': 'Idea',
        'book': 'Book',
        'book_fantasy': 'Fantasy Book',
        'book_horror': 'Horror Book',
        'book_hp': 'Harry Potter Book',
        'book_mystery': 'Mystery Book',
        'book_rom': 'Romance Book',
        'book_sf': 'Sci-Fi Book',
        'quote': 'Quote',
        'prompt': 'Prompt',
        'face': 'Face',
        'question_char': 'Character-building question',
        'question_world': 'World-building question',
    }

    def __init__(self, type, context):
        self.type = type
        self.context = context
        self.helper = Helper.instance()
        self.last = ''

    def generate(self, amount):

        generated_names = []

        # If the amount if higher than the max, set it to the max
        if amount > self.MAX_AMOUNT:
            amount = self.MAX_AMOUNT

        # If it's less than 1 for any reason, just use the default
        if amount is None or amount < 1:
            amount = self.DEFAULT_AMOUNT

        asset_file = 'gen_' + self.type
        source = self.helper.get_asset(asset_file)
        retry_attempts = 0

        # If we loaded the asset source okay, then let's loop through and generate some responses
        if source:

            # Store all the name choices before we start the loop
            choices = source['names']

            def replace(match):

                match = match.group().replace('$', '')

                if match in choices.keys():

                    # Generate a choice
                    choice = random.choice(choices[match])

                    i = 0

                    # Make sure it's not the same as the last one.
                    # Only try a maximum of self.MAX_RETRIES times though, we don't want a situation where an infinite loop could happen
                    while len(choice) > 2 and choice == self.last and i < self.MAX_RETRIES:
                        i += 1
                        choice = random.choice(choices[match])

                    self.last = choice
                    return choice
                else:
                    self.last = match
                    return match

            # Loop as many times as the amount we requested, and build up a generated name for each
            x = 0
            while x < amount:

                x += 1

                # Get the formats from the source data
                formats = source['formats']

                # Pick a random one to use
                format = random.choice(formats)

                # Variable to store the last chosen element, so we don't have the same thing twice in a row
                self.last = ''

                # Generate a name
                name = re.sub(r"\$([a-z0-9]+)", replace, format)

                # If we've already had this exact one, try again, up to self.MAX_RETRIES times
                if name in generated_names and retry_attempts < self.MAX_RETRIES:
                    x -= 1
                    retry_attempts += 1
                else:
                    # Add it to the return array
                    generated_names.append(name)
                    retry_attempts = 0

        # Sort the results alphabetically
        generated_names.sort()

        # Uppercase the first letter of each word, if it's anything but idea generation or prompt generatio
        if self.type != 'idea' and self.type != 'prompt' and self.type != 'quote':
            generated_names = map(lambda el: string.capwords(el), generated_names)

        # Generate the message
        message = f"Here are your {amount} {self.SUPPORTED_TYPES[self.type]} results:\n\n"

        return {
            'names': generated_names,
            'message': message
        }