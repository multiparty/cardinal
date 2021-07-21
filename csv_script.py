import sys
import os
import pandas as pd 
import mysql.connector
from dotenv import load_dotenv


class DB:
    def __init__(self):
        # load config for database
        load_dotenv()

        try:

            # initialize mysql client
            self.conn = mysql.connector.connect(
                host=os.environ.get('MYSQL_HOST'),
                port=int(os.environ.get('MYSQL_PORT')),
                user=os.environ.get('MYSQL_USER'),
                password=os.environ.get('MYSQL_PASSWORD'),
                database=os.environ.get('MYSQL_DB'),
            )

            self.database_name = os.environ.get('MYSQL_DB')
            self.db_schema = {}
            self.get_tables_columns()
            self.type_2_identifier = {
                'varchar': "%s",
                'int':"%d",
                'tinyint':"%d"
            }

        except Exception as e:
            print(e)


    def get_tables_columns(self):
        
        # get table names
        query = 'SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = "BASE TABLE" AND TABLE_SCHEMA="' + self.database_name + '";'
        cursor = self.conn.cursor()
        cursor.execute(query)
        table_names = [tbl[0] for tbl in list(cursor.fetchall())]
        
        # get column names
        for table in table_names:
            query = 'SELECT COLUMN_NAME,DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA="' + self.database_name + '" AND TABLE_NAME = "' + table + '";'
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.db_schema[table] = list(cursor.fetchall())
        
        cursor.close()

    def read_file(self,path):
        if path.endswith('.csv'):
            df = pd.read_csv(path)
        elif path.endswith('.xlsx'):
            df = pd.read_excel(path)
        else:
            raise Exception('File format not supported')
            

        table_name = ""
        # match column names
        for table,columns in self.db_schema.items():
            
            column_names = [tpl[0] for tpl in columns]
            matches = [True if col_name in column_names else False for col_name in df.columns]
            if all(matches):
                table_name = table 
                break 

        return df,table_name

    def insert_csv(self,path):

        df,table_name = self.read_file(path)
        records = [tuple(x) for x in df.to_records(index=False)]

        columns_str = '(' + ','.join(df.columns) + ')'
        identifiers_str = '(' + ','.join([self.type_2_identifier[col[1]] for col in self.db_schema[table_name]]) + ')'
        query = 'INSERT IGNORE INTO ' + self.database_name + '.' + table_name + ' ' + columns_str + ' VALUES ' + identifiers_str 


        cursor = self.conn.cursor()
        cursor.executemany(query,records)
        self.conn.commit()
        cursor.close()
        print('INSERTED SUCCESSFULLY!')


        


if __name__ == "__main__":

    db = DB()
    db.insert_csv(sys.argv[1])
