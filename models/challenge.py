class Challenge:

    DIFFICULTIES = {
        'easy': 'Easy',
        'normal': 'Normal',
        'hard': 'Hard',
        'hardcore': 'Hardcore',
        'insane': 'Insane'
    }

    WPM = {
        'min': 5,
        'max': 30
    }

    TIME = {
        'min': 5,
        'max': 120
    }

    @staticmethod
    def calculate_xp(wpm: int):
        """
        Calculate how much XP to give for the challenge, depending on WPM
        :param wpm:
        :return:
        """
        if wpm <= 5:
            return 20
        elif wpm <= 15:
            return 40
        elif wpm <= 30:
            return 75
        elif wpm <= 45:
            return 100
        elif wpm > 45:
            return 150