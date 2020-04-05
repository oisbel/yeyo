	# encoding: utf-8

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# for generate password hash
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	nombre = Column(String(250), nullable = False)
	email = Column(String(250), nullable = False)
	email_usa = Column(String(250), default = '')
	password_hash = Column(String(250))

	def hash_password(self, password):
		""" Crea y almacena el password encriptado"""
		self.password_hash = pwd_context.encrypt(password)

	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)

	def generate_auth_token(self, expiration=3600):
		s = Serializer(secret_key, expires_in = expiration)
		return s.dumps({'id': self.id })

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(secret_key)
		try:
			data = s.loads(token)
		except SignatureExpired:
			#Valid Token, but expired
			return None
		except BadSignature:
			#Invalid Token
			return None
		user_id = data['id']
		return user_id

	@property
	def serialize(self):
		"""Return user data in easily serializeable format"""
		return {
			'id': self.id,
			'nombre': self.nombre,
			'email': self.email,
			'email_usa': self.email_usa,
			'password': self.password_hash,
		}

class Tiro(Base):
	__tablename__ = "tiro"

	id = Column(Integer, primary_key = True) # posicion del tiro
	fecha = Column(String(50), default = '') # Formato : 04/07/1991
	hora = Column(String(10), default = '') # Formato : N
	tiro = Column(String(50), default = '') # Formato : 905-02-30

	@property
	def serialize(self):
		"""Return tiro data in easily serializeable format"""
		return {
			'id': self.id,
			'fecha': self.fecha,
			'hora': self.hora,
			'tiro': self.tiro
		}

class Play(Base):
	"""Jugadas del usuario"""
	__tablename__ = "play"

	id = Column(Integer, primary_key = True)
	fecha = Column(String(50),default = '')
	# Formato : 04/07/1991/N
	fijos = Column(String(250),default = '')
	corridos = Column(String(250),default = '')
	# Formato de las jugadas fijas y corridas(al 00->1 coin): 00:1,87:50,...,45:2
	parles = Column(String(250),default = '')
	# Formato de las jugadas parle(00 para el 87->1 coin): 00-87:1,87-45:50,...,45-25:2
	candados = Column(String(250),default = '')
	# Formato de las jugadas candado: 00-87-45-25:50,...,34-87-23-65-34-56-78-00:120
	nota = Column(String(250),default = '')
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User) # El que creo la jugada

	@property
	def serialize(self):
		"""Return Play data in easily serializeable format"""
		return {
			'user_id': self.user_id,
			'id': self.id,
			'fecha': self.fecha,
			'fijos': self.fijos,
			'corridos': self.corridos,
			'parles': self.parles,
			'candados': self.candados,
			'nota': self.nota
		}

engine = create_engine('sqlite:///yeyo.db')
# engine = create_engine('postgresql://yeyo:Vryyo_18@localhost/yeyo')

Base.metadata.create_all(engine)
