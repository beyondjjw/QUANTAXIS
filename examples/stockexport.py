# encoding:utf-8
import pymongo
import csv
import codecs
import pandas as pd
from pymongo import MongoClient

def _connect_mongo(host, port, username, password, db):
    """ A util for making a connection to mongo """
    if username and password:
        mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, db)
        conn = MongoClient(mongo_uri)
    else:
        conn = MongoClient(host, port)
    return conn[db]


def read_mongo(db, collection, query={}, host='localhost', port=27017, username=None, password=None, no_id=True):
    """ Read from Mongo and Store into DataFrame """
    db = _connect_mongo(host=host, port=port, username=username, password=password, db=db)
    cursor = db[collection].find(query)
    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))

    if no_id:
        del df['_id']

    return df
 
FILE = "/home/jiangjw/code/QUANTAXIS/examples/data/test.csv"

settings = {
    "db_name" : "quantaxis",    #数据库名字
    "collection_name" : "stock_list"   #集合名字
}

df = read_mongo(settings['db_name'], settings['collection_name'])
print(df.head(10))

print('+' * 80)

import QUANTAXIS as QA
from QUANTAXIS.QAFetch.Fetcher import QA_quotation_adv
from QUANTAXIS.QAUtil.QAParameter import (DATABASE_TABLE, DATASOURCE,
                                          FREQUENCE, MARKET_TYPE,
                                          OUTPUT_FORMAT)
 
df = QA_quotation_adv('000011', '2019-12-01', '2022-07-01', frequence=FREQUENCE.DAY,
                           market=MARKET_TYPE.STOCK_CN, source=DATASOURCE.AUTO, output=OUTPUT_FORMAT.DATAFRAME)

print(df.tail(20))
df.to_csv('path.csv',index=True)