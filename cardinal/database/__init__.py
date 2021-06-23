from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#
# class Database:
#     def __init__(self,  app):
#         app = Flask(__name__)
#         app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://://root:password@10.100.0.3:3306/Cardinal'
#         self.db = SQLAlchemy(app)
#
#         self.db.create_all()
#         self.db.session.commit()
