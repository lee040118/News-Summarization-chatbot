import datetime
import pandas as pd

from database.postgreslq import CRUD, Databases

db = CRUD()



df = pd.DataFrame(db.readDB(schema='public',table='news_data',colum='timekey',condition='20220227-14'), columns=["time"])

print(df.head())