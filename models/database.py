import sys, os, pymysql, warnings
from models.singleton import Singleton
from config import DB_HOST, DB_USER, DB_PASS, DB_NAME

@Singleton
class Database:

    def __init__(self):
        """
        Create Database instance and connect to the database
        """

        # Get the current path we are in, e.g. `/app/models`.
        self.__path = os.path.abspath(os.path.dirname(__file__))

        # Connect to the database.
        self.connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASS,
            db=DB_NAME,
            autocommit=True
        )

        # Set the cursor to be used, with DictCursor so we can refer to results by their keys.
        self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)

    def __del__(self):
        """
        Close the connection
        :return:
        """
        self.connection.close()

    def install(self):
        """
        Install all the required tables for the bot
        :return:
        """

        install_path = self.__path + '/../data/install/'

        try:

            for filename in os.listdir(install_path):

                file = open(os.path.join(install_path, filename), 'r')
                sql = file.read()

                # Suppress warnings about the tables already existing
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    self.cursor.execute(sql)

        except:
            self.connection.rollback()
            raise

        else:
            self.connection.commit()
            return True

    def __build_get(self, table, where=None, fields=['*'], sort=None, limit=None):
        """
        Build and run a select SQL query
        :param table:
        :param where:
        :param fields:
        :param sort:
        :param limit:
        :return:
        """

        params = []

        sql = 'SELECT ' + ', '.join(fields) + ' ' \
              'FROM ' + table + ' '

        # Did we specify some WHERE clauses?
        if where is not None:

            sql += 'WHERE '

            for field, value in where.items():
                sql += field + ' = %s AND '
                params.append(value)

            # Remove the last 'AND '
            sql = sql[:-4]

        # Did we specify some sorting?
        if sort is not None:
            sql += ' ORDER BY ' + ', '.join(sort)

        # Is there a limit?
        if limit is not None:
            sql += ' LIMIT ' + str(limit)

        self.cursor.execute(sql, params)

    def __build_insert(self, table, params):
        """
        Build and run an insert SQL query
        :param table:
        :param params:
        :return:
        """
        # Create param placeholders to be used in the query
        placeholders = ['%s'] * len(params.values())

        sql = 'INSERT INTO ' + table + ' '
        sql += '(' + ','.join(params.keys()) + ') '
        sql += 'VALUES '
        sql += '(' + ','.join(placeholders) + ') '

        sql_params = list(params.values())
        self.cursor.execute(sql, sql_params)

    def __build_delete(self, table, params):
        """
        Build and run a delete SQL query
        :param table:
        :param params:
        :return:
        """

        sql_params = []
        sql = 'DELETE FROM ' + table + ' WHERE '

        for field, value in params.items():
            sql += field + ' = %s AND '
            sql_params.append(value)

        # Remove the last 'AND '
        sql = sql[:-4]

        # Execute the query
        self.cursor.execute(sql, sql_params)

    def __build_update(self, table, params, where=None):
        """
        Build an run an update SQL query
        :param table:
        :param params:
        :param where:
        :return:
        """

        sql_params = []
        sql = 'UPDATE ' + table + ' SET '

        # Set values
        for field, value in params.items():
            sql += field + ' = %s, '
            sql_params.append(value)

        # Remove the last ', '
        sql = sql[:-2]

        # Where clauses
        if where is not None:
            sql += ' WHERE '

            for field, value in where.items():
                sql += field + ' = %s AND '
                sql_params.append(value)

            # Remove the last 'AND '
            sql = sql[:-4]

        # Execute the query
        self.cursor.execute(sql, sql_params)

    def get(self, table, where=None, fields=['*'], sort=None):
        """
        Get an individual record
        :param table:
        :param where:
        :param fields:
        :param sort:
        :return:
        """
        self.__build_get(table, where, fields, sort)
        return self.cursor.fetchone()

    def get_sql(self, sql, params):
        """
        Get an individual record using raw SQL
        :param sql:
        :param params:
        :return:
        """
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

    def get_all(self, table, where=None, fields=['*'], sort=None, limit=None):
        """
        Get multiple records
        :param table:
        :param where:
        :param fields:
        :param sort:
        :param limit:
        :return:
        """
        self.__build_get(table, where, fields, sort, limit)
        return self.cursor.fetchall()

    def get_all_sql(self, sql, params):
        """
        Get multiple records using raw SQL
        :param sql:
        :param params:
        :return:
        """
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def insert(self, table, params):
        """
        Insert data into the database
        :param table:
        :param params:
        :return:
        """
        self.__build_insert(table, params)
        return self.cursor.rowcount

    def delete(self, table, params):
        """
        Delete record(s) from the database
        :param table:
        :param params:
        :return:
        """
        self.__build_delete(table, params)
        return self.cursor.rowcount

    def update(self, table, params, where=None):
        """
        Update record(s) in the database
        :param table:
        :param params:
        :param where:
        :return:
        """
        self.__build_update(table, params, where)
        return self.cursor.rowcount

    def execute(self, sql, params):
        """
        Execute some raw SQL
        :param sql:
        :param params:
        :return:
        """
        return self.cursor.execute(sql, params)