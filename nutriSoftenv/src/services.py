from flask import Flask, request, jsonify, abort, session
from models import Usuario, Respueta, Dieta, Comida, ComidaTieneAlimento, Alimento, Cita
import json
from playhouse.shortcuts import model_to_dict, dict_to_model

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


@app.route("/login", methods=['POST'])
def login():
    respuesta = Respueta()
    resultado = None
    if request.form:
        usuario_existe = Usuario.get_or_none(
            Usuario.username == request.form["username"])
        if usuario_existe:
            if usuario_existe.password == request.form["password"]:
                session["username"] = request.form["username"]
                resultado = jsonify("c:")
            else:
                respuesta.codigo = 15
                resultado = abort(401, json.dumps(respuesta.__dict__))
        else:
            respuesta.codigo = 25
            resultado = abort(401, json.dumps(respuesta.__dict__))
    else:
        respuesta.codigo = 3
        abort(400, json.dumps(respuesta.__dict__))

    return resultado


@ app.route("/dieta/<idCita>", methods=['GET'])
def recuperarDieta(idCita):
    comidasRecuperadas = []
    if 'username' in session:
        comidas = Dieta.get_or_none(Dieta.id == idCita).comidas
        for comida in comidas:
            for alimento in comida.alimentosComida:
                comidasRecuperadas.append(model_to_dict(alimento))
        return jsonify(comidasRecuperadas)
    else:
        return jsonify("No logueado")
