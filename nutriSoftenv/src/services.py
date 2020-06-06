from flask import Flask, request, jsonify, make_response
from models import Usuario, Dieta, Comida, ComidaTieneAlimento, Alimento, Cita, Mensaje, Paciente
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '/De>$QCR/47p:kFM.2ua]r,J4D<>qbs:'


def token_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        token = None

        if 'authorization' in request.headers:
            token = request.headers["authorization"].split(" ")[1]
        if not token:
            return jsonify({"codigo": 200, "mensaje": "Falta token"}), 401

        try:
            datos = jwt.decode(
                token, app.config['SECRET_KEY'], algorithm='HS256')
            usuario = Usuario.get(Usuario.username == datos["usuario"])
        except:
            return jsonify({"codigo": 301, "mensaje": "token inválido"}), 400

        return f(usuario, *args, **kwargs)

    return decorada


@app.route("/login", methods=['POST'])
def login():
    resultado = None
    if request.form:
        usuario_existe = Usuario.get_or_none(
            Usuario.username == request.form["username"])
        if usuario_existe:
            if usuario_existe.password == request.form["password"]:
                token = jwt.encode(
                    {"usuario": request.form["username"]}, app.config['SECRET_KEY'], algorithm='HS256')
                return jsonify({"codigo": 100, "mensaje": "Inicio de sesión exitoso", "respuesta": token.decode("UTF-8")})
            else:
                resultado = make_response(
                    {"codigo": 202, "mensaje": "Contraseña incorrecta"}, 401)
        else:
            resultado = make_response(
                {"codigo": 201, "mensaje": "Usuario no existe"}, 401)
    else:
        resultado = make_response(
            {"codigo": 200, "mensaje": "Faltan parámetros"}, 400)

    return resultado


@app.route("/mensaje", methods=["GET"])
@token_requerido
def recuperar_mensajes(usuario_actual):
    mensajes_respuesta = []
    mensajes = Mensaje.select().where((Mensaje.destinatario_id == usuario_actual.id)
                                      | (Mensaje.remitente_id == usuario_actual.id)).order_by(Mensaje.fecha)

    for mensaje in mensajes:
        tipo = 1 if mensaje.remitente_id == usuario_actual.id else 2

        mensajes_respuesta.append({
            "tipo": tipo,
            "asunto": mensaje.asunto,
            "mensaje": mensaje.mensaje,
            "fecha": mensaje.fecha
        })

    return jsonify({"estado": 100, "mensaje": "Mensajes del ususario", "cuerpo": mensajes_respuesta})


@app.route("/mensaje/<idDestino>", methods=["POST"])
@token_requerido
def enviar_mensaje(usuario_actual, idDestino):
    if request.form:
        mensaje = Mensaje()
        mensaje.destinatario_id = idDestino
        mensaje.remitente = usuario_actual
        mensaje.asunto = request.form["asunto"]
        mensaje.mensaje = request.form["mensaje"]
        mensaje.fecha = datetime.datetime.now()
        mensaje.save()
        return jsonify({"estado": 100, "mensaje": "mensaje enviado"})
    else:
        return jsonify({"estado": 200, "mensaje": "Falta información necesaria"}), 400


@app.route("/perfil", methods=["GET"])
@token_requerido
def recuperar_perfil(usuario_actual):
    paciente = Paciente.get_or_none(Paciente.usuarioId_id == usuario_actual.id)

    if not paciente:
        return jsonify({
            "mensaje": "El usuario no existe",
            "estado": 302
        }), 404

    return jsonify({
        "estado": 100,
        "mensaje": "Información usuario",
        "cuerpo": {
            "nombre": usuario_actual.nombre,
            "apellido_paterno": usuario_actual.apellidoPaterno,
            "apellido_materno": usuario_actual.apellidoMaterno,
            "correo_electronico": usuario_actual.correoElectronico,
            "username": usuario_actual.username,
            "fecha_nacimiento": paciente.fechaNacimiento,
            "fotoPerfil": paciente.fotoPerfil
        }
    })

# Servicio para recuperar todas las citas del paciente y el estatus de la cita. 

@app.route("/citas", methods=["GET"])
@token_requerido
def recuperarCita(usuario_actual):
    paciente = Paciente.get_or_none(Paciente.usuarioId_id == usuario_actual.id)
    citas_recuperadas = []
    citas = Cita.select().where(Cita.paciente == paciente.id)

    for cita in citas:

        citas_recuperadas.append({
            "status": cita.status.status,
            "fecha": cita.fecha,
            "comentarios": cita.comentarios
        })
    return jsonify({"estado": 100, "mensaje": "Citas del paciente", "cuerpo": citas_recuperadas})


# Servicio para recuperar las medidas del paciente. 

@app.route("/progreso", methods=["GET"])
@token_requerido
def recuperarProgreso(usuario_actual):
    paciente = Paciente.get_or_none(Paciente.usuarioId_id == usuario_actual.id)
    medidas_recuperadas = []
    medidas = Cita.select().where(Cita.paciente == paciente.id)

    for cita in medidas:

        medidas_recuperadas.append({
            "peso": cita.medidasId.peso,
            "estatura": cita.medidasId.estatura,
            "cadera": cita.medidasId.cadera,
            "pectoral": cita.medidasId.pectoral
        })
    return jsonify({"estado": 100, "mensaje": "Últimas medidas", "cuerpo": medidas_recuperadas})

# Servicio para actualizar la información personal del paciente, excepto nombre de usuario
# y contraseña. 

@app.route("/actualizarPerfil", methods=["POST"])
@token_requerido
def actualizarPerfil(usuario_actual):
    if request.form:
        paciente = Paciente.get_or_none(Paciente.usuarioId_id == usuario_actual.id)
        usuario_actual.nombre = request.form["nombre"]
        usuario_actual.apellidoPaterno = request.form["apellidoPaterno"]
        usuario_actual.apellidoMaterno = request.form["apellidoMaterno"]
        usuario_actual.correoElectronico = request.form["correoElectronico"]
        paciente.fechaNacimiento = request.form["fechaNacimiento"]
        paciente.fotoPerfil = request.form["fotoPerfil"]
        paciente.save()
        usuario_actual.save()
        return jsonify({"estado": 100, "mensaje": "Usuario actualizado exitosamente"})
    else:
        return jsonify({"estado": 200, "mensaje": "Falta información necesaria"}), 400

# Servicio para reportar la comida ingerida, correspondiente al horario en que le tocaba
# ingerir los alimentos. 

@app.route("/reportarComida/<idAlimento>", methods=["POST"])
@token_requerido
def reportarComida(usuario_actual, idAlimento):
    if request.form:
        comida = ComidaTieneAlimento.get_or_none(ComidaTieneAlimento.alimentoId == idAlimento)
        comida.ingerido = request.form["ingerido"]
        comida.save()
        return jsonify({"estado": 100, "mensaje": "Alimento reportado exitosamente"})
    else:
        return jsonify({"estado": 200, "mensaje": "Falta información necesaria"}), 400

# Servicio para recuperar los alimentos de cada comida de la dieta. 

@app.route("/comidaTieneAlimento", methods=["GET"])
@token_requerido
def recuperarComidas(usuario_actual):
    paciente = Paciente.get_or_none(Paciente.usuarioId_id == usuario_actual.id)
    comida_recuperada = []
    comidas = ComidaTieneAlimento.select().where(ComidaTieneAlimento.comidaId == 1)

    for comida in comidas:

        comida_recuperada.append({
            "horario": comida.comidaId.horario,
            "alimento": comida.alimentoId.nombreAlimento,
            "cantidad": comida.cantidad,
            "ingerido": comida.ingerido
        })
    return jsonify({"estado": 100, "mensaje": "Últimas medidas", "cuerpo": comida_recuperada})

@app.route("/prueba/<id>", methods=['GET'])
@token_requerido
def prueba(usuario_actual, id):
    return jsonify({"usuario": usuario_actual.nombre, "id": id})

