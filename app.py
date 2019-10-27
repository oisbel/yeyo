# encoding: utf-8

#import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
from flask import abort, g

# For database
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from database import Base, User, Tiro, Play, Status

# For anti-forgery
from flask import session as login_session
import random
import string

# to fix IO Error Broken Pipe
#from signal import signal, SIGPIPE, SIG_DFL
#signal(SIGPIPE,SIG_DFL) # no funciono porque en ves de darme el error apaga el servidor, al menos el local

# For auth token and password
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

APPLICATION_NAME = "Yeyo"

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///yeyo.db')
# engine = create_engine('postgresql://yeyo:Vryyo_18@localhost/yeyo')
Base.metadata.bind = engine
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

@app.route('/')
def showMain():
       return redirect('/showtiros/30')

@app.route('/showtiros/<int:count>')
def showTiros(count):
       """ Muestra los ultimos count tiros ordenados por el mayor id"""
       session = Session()
       tiros = session.query(Tiro).order_by(Tiro.id.desc())[:count]
       session.close()
       return render_template(
              'tiros.html', tiros = tiros)

@app.route('/showlast/<int:count>')
def showLastTiros(count):
       """ Muestra los ultimos count tiros ordenados por el menor id"""
       session = Session()
       tiros = session.query(Tiro).order_by(-Tiro.id.desc())[-count:]
       session.close()
	   return render_template(
              'tiros.html', tiros = tiros)

@app.route('/showtiros/all')
def showAllTiros():
       """ Muestra todos tiros ordenados por el menor id"""
       session = Session()
       tiros = session.query(Tiro).all()
       session.close()
       return render_template(
              'tiros.html', tiros = tiros)
			  
@auth.verify_password
def verify_password(username_or_token, password):
       """ Usado por HTTPBasicAuth para verificar
        que sea un usuario el que accede a las funciones con el decorador @auth.verify_password
        Se ha agregado un token para no tener que transmitir por la web el usuario y password """
       session = Session()
	   # Try to see if it's a token first
       user_id = User.verify_auth_token(username_or_token)
       if user_id:
              user = session.query(User).filter_by(id = user_id).one()			  
              session.close()
       else: # No es un token sino credenciales de usuario(siempre el email y password)
              try:
                     user = session.query(User).filter_by(email = username_or_token).one()
                     session.close()
                     if not user or not user.verify_password(password):
                            return False
              except: #Era un token invalido
                     return False
       g.user = user
       return True

@app.route('/token')
@auth.login_required
def get_auth_token():
       """ Genera un token para el usuario dado en los parametros"""
       token = g.user.generate_auth_token()
       return jsonify({'token': token.decode('ascii')})

@app.route('/adduser', methods = ['POST'])
def new_user():
       """ Crea un usuario"""
       session = Session()
       nombre = request.json.get('nombre')
       email = request.json.get('email') # username es el email
       email_usa = request.json.get('email_usa', '')
       
       password = request.json.get('password')

       if email is None or password is None or nombre is None:
              # print "missing arguments"
              abort(400)
       if session.query(User).filter_by(email = email).first() is not None:
              # print "existing user"
              return jsonify({'message':'user already exists'})#, 200

       user = User(nombre = nombre, email = email, email_usa = email_usa)
       user.hash_password(password)
       session.add(user)
       session.commit()
       return jsonify({ 'email': user.email , 'id': user.id})#, 201 # 201 mean resource created

@app.route('/edituser/<int:user_id>', methods = ['POST'])
@auth.login_required
def edit_user(user_id):
       session = Session()
       try:
              user = session.query(User).filter_by(id=user_id).one()
       except:
              return jsonify({'message':'user not exists'})#, 200

       if user.id != g.user.id:
              return jsonify({'message':'different user'})#, 200

       email_usa = request.json.get('email_usa')
       if email_usa is not None:
              user.email_usa = email_usa
       session.add(user)
       session.commit()
       return jsonify({ 'user': user.id })#, 201 # 201 mean resource created	

@app.route('/addplay', methods = ['POST'])
@auth.login_required
def new_play():
       """Agrega una jugada para el usuario logeado"""
       session = Session()       
       fecha = request.json.get('fecha', '')
       fijos = request.json.get('fijos', '')
       corridos = request.json.get('corridos', '')
       parles = request.json.get('parles', '')
       candados = request.json.get('candados', '')
       nota = request.json.get('nota', '')
   
       play = Play(
              fecha = fecha,
              fijos = fijos,
              corridos = corridos,
              parles = parles,
              candados = candados,
			  nota = nota,
              user = g.user)
       session.add(play)
       session.commit()
       return jsonify({ 'play': play.id })#, 201 # 201 mean resource created

@app.route('/editplay/<int:play_id>', methods = ['POST'])
@auth.login_required
def edit_play(play_id):
       session = Session()
       try:
              play = session.query(Play).filter_by(id=play_id).one()
       except:
              return jsonify({'message':'play not exists'})#, 200

       if play.user_id != g.user.id:
              return jsonify({'message':'The play belong to another user'})#, 200

       nota = request.json.get('nota')
       if nota is not None:
              play.nota = nota
       try:
              session.add(play)
              session.commit()
       except:
              session.close()
			  return jsonify({'message':'Error in characters'})
       return jsonify({ 'play': play.id })#, 201 # 201 mean resource created

# JSON api to get all tiros for the user who provides credentials
@app.route('/tiros/all', methods = ['GET'])
@auth.login_required
def getAllTirosJSON():
       session = Session()
       result={'status':'ok'}
       try:
              tiros = session.query(Tiro).all()
              tiro_list = []
              for tiro in tiros:
                     tiro_list.append(tiro.serialize)
              temp = {'list':tiro_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(Tiros=result)
# JSON api to get the last tiros a partir de position, devuelve desde position + 1 to the last one
@app.route('/tiros/<int:position>', methods = ['GET'])
@auth.login_required
def getLastTirosJSON(position):
       session = Session()
       result={'status':'ok'}
       tiro_list = []
       
       totalTiros = session.query(Status).first().countTiros
       if position >= totalTiros:
              temp = {'list':tiro_list}
              result.update(temp)
              return jsonify(Tiros=result)
       
       count = totalTiros - position;
	   
       try:
              tiros = session.query(Tiro).order_by(Tiro.id.desc()).limit(count).all()[::-1]              
              for tiro in tiros:
                     tiro_list.append(tiro.serialize)
              temp = {'list':tiro_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(Tiros=result)

# JSON api to get the 60 last tiros
@app.route('/tiros', methods = ['GET'])
def getTirosJSON():
       count = 60
       session = Session()
       result={'status':'ok'}
       try:
              tiros = session.query(Tiro).order_by(Tiro.id.desc())[:count]
              tiro_list = []
              for tiro in tiros:
                     tiro_list.append(tiro.serialize)
              temp = {'list':tiro_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(Tiros=result)

@app.route('/addtiros', methods = ['POST'])
@auth.login_required
def new_tiros():
       """ Agrega un tiro"""
       session = Session()
       pin = request.json.get('pin','')
       tiros = request.json.get('tiros',[]) # "tiros":[ "04/07/1991/N-905-02-30", , , "27/04/2019/N-728-46-98" ]

       if g.user.email != "oisbelsimpv@gmail.com" or pin != 9229:
              return jsonify({'message':'No autorizado para agregar tiros'})#, 200
       
       status = session.query(Status).first()
       totalTiros = status.countTiros + len(tiros);
       for line in tiros:
              tiro = Tiro(fecha=line[:10], hora=line[11:12], tiro=line[13:])
              session.add(tiro)
              session.commit()
       
       status.countTiros = totalTiros
       session.add(status)
       session.commit()
       return jsonify({ 'totalTiros': totalTiros})

# JSON api to get plays for the user who provides credentials
@app.route('/plays', methods = ['GET'])
@auth.login_required
def getPlaysJSON():
       session = Session()
       result={'status':'ok'}
       user_id = g.user.id
       try:
              user = session.query(User).filter_by(id=user_id).one()
              plays = session.query(Play).filter_by(user_id=user.id).order_by(Play.id.desc())[:24]
              play_list = []
              for play in plays:
                     play_list.append(play.serialize)
              temp = {'list':play_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(Plays=result)

# JSON api to get the play base in the play id (/play?play_id=a)
@app.route('/play', methods = ['GET'])
@auth.login_required
def getPlayJSON():
       session = Session()
       result={'status':'ok'}
       play_id = request.args.get('play_id')
       try:
              play = session.query(Play).filter_by(id=play_id).one()
              if play.user_id != g.user.id:
                     return jsonify({'message':'The play belong to another user'})#, 200
              result.update(play.serialize)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(Play=result)

# JSON api to get the user information base in the email, para logearse
@app.route('/getuser')
@auth.login_required
def getUserDataJSON():
       session = Session()
       result={'status':'ok'}
       email = g.user.email
       try:
              user = session.query(User).filter_by(email = email).first()
              result.update(user.serialize)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(result)

if __name__ == '__main__':
    app.secret_key = '88040422507vryyo'
    app.debug = True
    app.run(host='0.0.0.0', port=8000) # app.run(threaded=True) tampoco sirvio para arreglar broken Pipe