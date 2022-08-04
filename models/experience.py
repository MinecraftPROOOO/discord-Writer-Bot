import math

class Experience:
    """
    LVL/XP chart is done so each new level is harder than the last.
    Lvl 1: 0-99 XP
    Lvl 2: 100-299 XP
    Lvl 3: 300-599 XP
    Lvl 4: 600-999 XP
    etc...
    """

    XP_COMPLETE_SPRINT = 25
    XP_WIN_SPRINT = 100
    XP_COMPLETE_GOAL = {
        "daily": 100,
        "weekly": 250,
        "monthly": 500,
        "yearly": 2500
    }

    XP_CALC_KEY = 50
    """
    This CALC_KEY is used to calculate the level and xp to the desired numbers
    """

    def __init__(self, xp):
        self.xp = xp

    def get_level(self):
        """
        Given the experience passed into the object, get the current level
        :return: int
        """
        return math.floor( math.floor(self.XP_CALC_KEY + math.sqrt( (self.XP_CALC_KEY * self.XP_CALC_KEY) + (4 * self.XP_CALC_KEY) * self.xp )) / (2 * self.XP_CALC_KEY) )

    def get_xp_boundary(self, lvl):
        """
        Get the required XP for the given level
        :param lvl: int The level to check
        :return: int
        """
        return self.XP_CALC_KEY * lvl * lvl - self.XP_CALC_KEY * lvl

    def get_next_level_xp(self):
        """
        Get how much XP is required to reach the next level
        :return: int
        """
        return self.get_xp_boundary( self.get_level() + 1 ) - self.xp
