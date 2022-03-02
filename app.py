from ast import Return
from os import environ
from re import I, U
from flask import Flask, render_template, request, url_for, redirect, abort, flash, session, jsonify, g
from itsdangerous import json
from mysql.connector import connection
from werkzeug.wrappers.response import ResponseStream
import sys
from itertools import cycle
from io import BytesIO
import mysql.connector

class User:
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

    def __repr__(self):
        return f'{self.id}'

app = Flask(__name__)

midb = mysql.connector.connect(
    host="localhost",
    user='root',
    password='1234',
    database='1ta_agenda',
)
app.secret_key = 'my secret key'

cursor = midb.cursor(dictionary=True)


@app.before_request
def before_request():
    g.user = None
     
    users = []
    cursor.execute("SELECT * FROM personal")
    personas = cursor.fetchall()
    for p in personas:
        users.append(User(id=p['id'], email=p['email'], password=p['password']))
    
    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']]
        g.user = user


#--------------- HOME -----------------
@app.route('/')
def index():
    session.pop('user_id', None)
    cursor.execute("SELECT * FROM agenda")
    agenda = cursor.fetchall()
    return render_template('agenda.html', data=agenda)

#--------------- ALERTA FORMULARIO INICIO SESION -----------------
@app.route('/alerta_iniciar_sesion')
def login():
    flash('Formulario de inicio')
    return redirect(url_for('index'))

#--------------- LOGIN -----------------
@app.route('/iniciar_sesion', methods=['POST','GET'])
def iniciar_sesion():
    if request.method == 'POST':
        session.pop('user_id', None)

        users = []
        cursor.execute("SELECT * FROM personal")
        personas = cursor.fetchall()
        for p in personas:
            users.append(User(id=p['id'], email=p['email'], password=p['password']))

        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM personal WHERE email = '%s'" %email)
        persona = cursor.fetchone()
        
        if persona == None:
            flash('Los datos ingresados no son correctos')
            # return redirect(url_for('index'))
            return jsonify('Los datos ingresados no son correctos')
        elif persona['password'] != password:
            flash('Los datos ingresados no son correctos')
            # return redirect(url_for('index'))
            return jsonify('Los datos ingresados no son correctos')
        elif persona['password'] == password:
            user = [x for x in users if x.email == email][0]
            session['user_id'] = user.id
            return jsonify(persona)
            # return redirect(url_for('agenda'))

    else:
        session.pop('user_id', None)
        return render_template('agenda.html')

#--------------- ALERTA CERRAR SESION -----------------
@app.route('/alerta_cerrar_sesion', methods=['POST','GET'])
def logout():
    flash("¿Seguro que desea cerrar sesion?")
    return render_template('agenda_logeado.html')

#--------------- LOGOUT -----------------
@app.route('/cerrar_sesion', methods=['POST','GET'])
def cerrar_sesion():
    if request.method == 'POST':
        return redirect(url_for('index'))


#-------------------------------------------------------
@app.route('/agenda', methods=['POST', 'GET'])
def agenda():
    if not g.user:
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM agenda")
    agenda = cursor.fetchall()
    return render_template('agenda_logeado.html', data=agenda)    

#----------------- ALERTA ELIMINAR ACTIVIDAD -------------------------------
@app.route('/alerta_eliminar/<int:id>')
def alerta_eliminar(id):
    cursor.execute("SELECT * FROM agenda WHERE id = {0}".format(id))
    agenda = cursor.fetchone()
    actividad = agenda['actividad']
    flash("%s" %id)
    return render_template("agenda_logeado.html", actividad=actividad)

#----------------- ELIMINAR ACTIVIDAD -------------------------------

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    if request.method == 'POST':
        cursor.execute("DELETE  FROM agenda WHERE id = {0}".format(id))
        midb.commit()
        return redirect(url_for('agenda'))


#----------------- ALERTA EDITAR ACTIVIDAD -------------------------------
# @app.route('/editartarea/<int:id>')




@app.route('/formulario', methods=['POST','GET'])
def formulario():
    if not g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        cursor.execute("SELECT * FROM agenda")
        agenda = cursor.fetchall()

        mayor = 0

        for age in agenda:
            if mayor == 0:
                mayor = age['id']
            else:
                mayor = age['id'] if age['id'] > mayor else mayor

        id = mayor + 1
        estado = "REALIZADA"
        fechaentrada = str(request.form['fechaentrada'])
        horainico = request.form['hora_incio']
        horatermino = request.form['hora_termino']
        cargo = request.form['cargo']
        nombre = request.form['nombre']
        actividad = request.form['actividad']
        lugar = request.form['lugar']

        participantes = request.form['participantes']

        detalles = request.form['detalle']
        hora = horainico + " - " + horatermino


        sql = "INSERT INTO agenda (id, estado, fecha, cargo, nombre, actividad, lugar, participantes, detalles, hora) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        values = (id, estado, fechaentrada, cargo, nombre, actividad, lugar, participantes, detalles, hora)
        cursor.execute(sql,values)
        midb.commit()
        flash("¡Agenda actualizada con exito!")
        return render_template("formulario.html")
    
    elif request.method == 'GET':
        return render_template('formulario.html')

@app.route('/filtro_oviedo', methods=['POST', 'GET'])
def filtro_oviedo():
    if request.method == 'POST':
        nombre = "Mauricio Oviedo"
        opcion = request.form.get('opcion', type=str)
        cursor.execute("SELECT * FROM agenda WHERE nombre = '%s'" %nombre)
        agenda = cursor.fetchall()
        actividades = []
        for ag in agenda:
            if ag['fecha'][5:7] == opcion:
                actividades.append(ag)

        return jsonify(actividades)

@app.route('/filtro_alvarez', methods=['POST', 'GET'])
def filtro_alvarez():
    if request.method == 'POST':
        nombre = "Sandra Alvarez"
        opcion = request.form.get('opcion', type=str)
        cursor.execute("SELECT * FROM agenda WHERE nombre = '%s'" %nombre)
        agenda = cursor.fetchall()
        actividades = []
        for ag in agenda:
            if ag['fecha'][5:7] == opcion:
                actividades.append(ag)

        return jsonify(actividades)



if __name__ == '__main__':
    app.run(port = 8000, debug = True)