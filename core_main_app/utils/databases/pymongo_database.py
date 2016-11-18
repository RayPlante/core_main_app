"""
    The Database pymongo tool contains the available function relative to database operation (connection)
"""
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from pymongo import TEXT
from core_main_app.commons import exceptions
from core_main_app.settings import MONGODB_URI, DB_NAME
import re


class Database(object):
    """ Represent Database
    """
    def __init__(self):
        self.client = None

    def connect(self, db_uri, db_name, doc_class=dict):
        """ Connect to the database from settings.py

        Args:
            db_uri:
            db_name:
            doc_class:

        Returns:

        """
        # create a connection
        self.client = MongoClient(db_uri, document_class=doc_class)
        db = self.client[db_name]    # connect to the database
        if db is not None:
            return db           # return db connection
        else:                   # or raise an exception
            raise exceptions.CoreError("Database connection error")

    def close_connection(self):
        """
            Close the client connection
        """
        self.client.close()

    @staticmethod
    def get_collection(db, collection_name):
        """ Return cursor of collection name in parameters

        Args:
            db:
            collection_name:

        Returns:

        """
        try:
            data_list = db[collection_name]  # get the data collection
            return data_list  # return collection
        except:  # or raise an exception
            raise exceptions.CoreError("Collection in database does not exist")

    @staticmethod
    def clean_database(db):
        """ Clean the database

        Args:
            db:

        Returns:

        """
        # clear all collections
        for collection in db.collection_names():
            try:
                if collection != 'system.indexes':
                    db.drop_collection(collection)
            except OperationFailure:
                pass


def init_text_index(table_name):
    """ Create index for full text search
    """
    database = Database()
    db = database.connect(MONGODB_URI, DB_NAME)
    data_list = Database.get_collection(db, table_name)
    # create the full text index
    data_list.create_index([('$**', TEXT)], default_language="en", language_override="en")
    database.close_connection()


def get_full_text_query(text):
    """

    Args:
        text: List of keywords

    Returns: The corresponding query

    """
    full_text_query = {}
    word_list = re.sub("[^\w]", " ", text).split()
    word_list = ['"{0}"'.format(x) for x in word_list]
    word_list = ' '.join(word_list)
    if len(word_list) > 0:
        full_text_query = {'$text': {'$search': word_list}}

    return full_text_query