"""
This module allows to load and store values using a simple sqlite database
in a distributed fashion.
"""

# Authors: Arnaud Joly
#
# License: BSD 3 clause

import os
import sqlite3
import pickle

__all__ = [
    "sqlite3_loads",
    "sqlite3_dumps",
]


# sqlite3 ---------------------------------------------------------------------

def sqlite3_loads(fname, key, timeout=7200.0):
    """Load value with key from sqlite3 stored at fname

    In order to improve improve performance, it's advised to
    query the database using a list of keys.

    Note if there is no sqlite3 database at fname, then None is return for
    each key.

    Parameters
    ----------
    fname : str
        Path to the sqlite database

    key : str or list of str

    Returns
    -------
    value : object or list of object
        Return the object or list of objects associated to each key.
        None is return if the key is missing.

    """
    if isinstance(key, str):
        key = [key]

    if os.path.exists(fname):
        with sqlite3.connect(fname, timeout=timeout) as connection:
            cursor = connection.cursor()
            out = []
            for k in key:
                cursor.execute("SELECT value FROM dict where key = ?", (k,))
                value = cursor.fetchone() # key is the primary key
                if value is None:
                    out.append(value)
                else:
                    out.append(value[0]) # ravel one length tuple
            cursor.close()

        out = [None if value is None else pickle.loads(bytes(value))
               for value in out]
    else:
        # There is no sqlite database yet.
        out = [None] * len(key)


    # Ravel if needed
    if len(key) == 1:
        out = out[0]

    return out


def sqlite3_dumps(fname, key, value, timeout=7200.0):
    """Dumps value with key in the sqlite3 database

    Parameters
    ----------
    fname : str
        path to the sqlite database

    key : str
        Key to the object.  If the key is already present in the database, it
        will raise an exception

    value : object
        Object to stored

    """
    value = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

    connection = sqlite3.connect(fname, timeout=timeout)
    with connection:
        # Create table if needed
        connection.execute("""CREATE TABLE IF NOT EXISTS dict
                              (key TEXT PRIMARY KEY, value BLOB)""")

        # Add a new key
        connection.execute("INSERT INTO dict(key, value) VALUES (?, ?)",
                           (key, sqlite3.Binary(value)))
