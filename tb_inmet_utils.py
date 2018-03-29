#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np

def load_csv(fname, header_row=0, first_data_row=None, types=None, **kwargs):
    """Load a CSV file into a dictionary.

    The strings from the header row are used as dictionary keys.

    **Arguments:**

    - *fname*: Path and name of the file

    - *header_row*: Row that contains the keys (uses zero-based indexing)

    - *first_data_row*: First row of data (uses zero-based indexing)

         If *first_data_row* is not provided, then it is assumed that the data
         starts just after the header row.

    - *types*: List of data types for each column

         :class:`int` and :class:`float` data types will be cast into a
         :class:`numpy.array`.  If *types* is not provided, attempts will be
         made to cast each column into :class:`int`, :class:`float`, and
         :class:`str` (in that order).

    - *\*\*kwargs*: Additional arguments for :meth:`csv.reader`

    **Example:**

    >>> from modelicares import *
    >>> data = load_csv("examples/load-csv.csv", header_row=2)
    >>> print("The keys are: %s" % data.keys())
    The keys are: ['Price', 'Description', 'Make', 'Model', 'Year']
    """
    import csv

    try:
        reader = csv.reader(open(fname), delimiter=';', **kwargs)
    except IOError:
        print('Unable to load "%s".  Check that it exists.' % fname)
        return

    # Read the header row and create the dictionary from it.
    for i in range(header_row):
        reader.next()
    keys = reader.next()
    data = dict.fromkeys(keys)
    #print("The keys are: ")
    #print(keys)

    # Read the data.
    if first_data_row:
        for row in range(first_data_row - header_row - 1):
            reader.next()
    if types:
        for i, (key, column, t) in enumerate(zip(keys, zip(*reader), types)):
            # zip(*reader) groups the data by columns.
            try:
                if isinstance(t, basestring):
                    data[key] = column
                elif isinstance(t, (float, int)):
                    data[key] = np.array(map(t, column))
                else:
                    data[key] = map(t, column)
            except ValueError:
                print("Could not cast column %i into %i." % (i, t))
                return
    else:
        for key, column in zip(keys, zip(*reader)):
            try:
                data[key] = np.array(map(int, column))
            except:
                try:
                    data[key] = np.array(map(float, column))
                except:
                    data[key] = map(str, column)

    return data