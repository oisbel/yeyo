# encoding: utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, User, Tiro, Play

engine = create_engine('sqlite:///yeyo.db')
# engine = create_engine('postgresql://yeyo:Vryyo_18@localhost/yeyo')

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create users
user1 = User(nombre="Oisbel Simpson", email="oisbelsimpv@gmail.com")
user1.hash_password('vryyo18')
session.add(user1)
session.commit()

user2 = User(nombre="Barbara Simpson", email="barbaraimara@gmail.com",
	email_usa="oisbelsimpv@gmail.com")
user2.hash_password('Simbar18')
session.add(user2)
session.commit()

# Un play de prueba
play1 = Play(
    fecha= '07/03/2019/D',
    fijos='25:3,67:10',
	corridos='00:1,67:20',
	parles='00-87:1,87-45:50',
	candados='34-87-23-65-34-56-78-00:120',
	nota='Esta jugada se la hice a mi tio...',
    user=user1)

session.add(play1)
session.commit()

# Agregar las jugadas
filepath='tiros.txt'
with open(filepath) as fp:
	for cnt,line in enumerate(fp):
		# print("Line {}: {}".format(cnt, line))
		tiro=Tiro(fecha=line[:10], hora=line[11:12], tiro=line[13:])
		session.add(tiro)
		session.commit()

status = Status(countTiros=14156, countUsers=2, countPlays=1)

session.add(status)
session.commit()

print "Added Items!"
