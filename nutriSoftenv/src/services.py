import os
from flask import Flask, request, jsonify, make_response
from models import Usuario, Dieta, Comida, ComidaTieneAlimento, Alimento, Cita, Mensaje, Paciente
import jwt
import datetime
from functools import wraps
from werkzeug.utils import secure_filename
import base64
from pathlib import Path

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')


app = Flask(__name__)
app.config['SECRET_KEY'] = '/De>$QCR/47p:kFM.2ua]r,J4D<>qbs:'
app.config['SERVER_NAME'] = None

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
                return jsonify({"codigo": 100, "mensaje": "Inicio de sesión exitoso", "cuerpo": token.decode("UTF-8")})
            else:
                resultado = make_response(
                    {"codigo": 202, "mensaje": "Contraseña incorrecta"})
        else:
            resultado = make_response(
                {"codigo": 201, "mensaje": "Usuario no existe"})
    else:
        resultado = make_response(
            {"codigo": 200, "mensaje": "Faltan parámetros"})

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

    return jsonify({"codigo": 100, "mensaje": "Mensajes del ususario", "cuerpo": mensajes_respuesta})


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
        return jsonify({"codigo": 100, "mensaje": "mensaje enviado"})
    else:
        return jsonify({"codigo": 200, "mensaje": "Falta información necesaria"}), 400


@app.route("/perfil", methods=["GET"])
@token_requerido
def recuperar_perfil(usuario_actual):
    paciente = Paciente.get_or_none(Paciente.usuarioId_id == usuario_actual.id)
    #foto = get('https://api.ipify.org').text + "/" + (Path("./images/users") / paciente.fotoPerfil).absolute().as_uri() if paciente.fotoPerfil != "" and paciente.fotoPerfil != None else ""
    if not paciente:
        return jsonify({
            "mensaje": "El usuario no existe",
            "codigo": 302
        }), 404


    return jsonify({
        "codigo": 100,
        "mensaje": "Información usuario",
        "cuerpo": {
            "nombre": usuario_actual.nombre,
            "apellido_paterno": usuario_actual.apellidoPaterno,
            "apellido_materno": usuario_actual.apellidoMaterno,
            "correo_electronico": usuario_actual.correoElectronico,
            "username": usuario_actual.username,
            "fecha_nacimiento": paciente.fechaNacimiento.strftime("%d %b %Y"),
	    "fechaFormato": paciente.fechaNacimiento.strftime("%d-%m-%Y"),
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
            "fecha": cita.fecha.strftime("%d %b %Y"),
	    "fechaFormato": cita.fecha.strftime("%d-%m-%Y"),
            "comentarios": cita.comentarios
        })
    return jsonify({"codigo": 100, "mensaje": "Citas del paciente", "cuerpo": citas_recuperadas})


# Servicio para recuperar las medidas del paciente.

@app.route("/progreso", methods=["GET"])
@token_requerido
def recuperarProgreso(usuario_actual):
    paciente = Paciente.get_or_none(Paciente.usuarioId_id == usuario_actual.id)
    medidas_recuperadas = []
    medidas = Cita.select().where(Cita.paciente == paciente.id)

    for cita in medidas:

        medidas_recuperadas.append({
	    "fecha": cita.fecha.strftime("%d-%m-%Y"),
            "peso": cita.medidasId.peso,
            "estatura": cita.medidasId.estatura,
            "cadera": cita.medidasId.cadera,
            "pectoral": cita.medidasId.pectoral
        })
    return jsonify({"codigo": 100, "mensaje": "Últimas medidas", "cuerpo": medidas_recuperadas})

# Servicio para actualizar la información personal del paciente, excepto nombre de usuario
# y contraseña.

def guardar_imagen(imagen64, username):
    info_imagen = base64.b64decode(imagen64)
    ruta_imagenes = Path("./images/users")
    archivo = ruta_imagenes / f"{username}_profile.jpg"
    with open(archivo, 'wb') as imagen:
        imagen.write(info_imagen)
        return f"{username}_profile.jpg"
    return None

@app.route("/actualizarPerfil", methods=["POST"])
@token_requerido
def actualizarPerfil(usuario_actual):
    if request.form:
        paciente = Paciente.get_or_none(
            Paciente.usuarioId_id == usuario_actual.id)
        usuario_actual.nombre = request.form["nombre"]
        usuario_actual.apellidoPaterno = request.form["apellidoPaterno"]
        usuario_actual.apellidoMaterno = request.form["apellidoMaterno"]
        usuario_actual.correoElectronico = request.form["correoElectronico"]
        paciente.fechaNacimiento = request.form["fechaNacimiento"]
        paciente.fotoPerfil = guardar_imagen(request.form["fotoPerfil"], usuario_actual.username)
        paciente.save()
        usuario_actual.save()
        return jsonify({"codigo": 100, "mensaje": "Usuario actualizado exitosamente"})
    else:
        return jsonify({"codigo": 200, "mensaje": "Falta información necesaria"}), 400

# Servicio para reportar la comida ingerida, correspondiente al horario en que le tocaba
# ingerir los alimentos.


@app.route("/reportarComida/<idComida>/<idAlimento>", methods=["POST"])
@token_requerido
def reportarComida(usuario_actual, idComida, idAlimento):
    comida = ComidaTieneAlimento.get_or_none(
            ComidaTieneAlimento.comidaId == idComida, ComidaTieneAlimento.alimentoId == idAlimento)
    comida.ingerido = True
    comida.save()
    return jsonify({"codigo": 100, "mensaje": "Alimento reportado exitosamente"})


# Servicio para recuperar los alimentos de cada comida de la dieta.


@app.route("/comidaTieneAlimento/<idComida>", methods=["GET"])
@token_requerido
def recuperarComidas(usuario_actual, idComida):
    comida_recuperada = []
    comidas = ComidaTieneAlimento.select().where(
        ComidaTieneAlimento.comidaId == idComida)

    for comida in comidas:

        comida_recuperada.append({
            "horario": comida.comidaId.horarioId.horario,
            "alimento": comida.alimentoId.nombreAlimento,
            "cantidad": comida.cantidad,
            "fotoAlimento": comida.alimentoId.fotoAlimento.decode('utf-8'),
            "ingerido": comida.ingerido
        })
    return jsonify({"codigo": 100, "mensaje": "Últimas medidas", "cuerpo": comida_recuperada})


@app.route("/alimentos", methods=["GET"])
@token_requerido
def alimentos_dia(usuario_actual):
    dia_semana = datetime.datetime.today().isoweekday()  # lunes 1.. domingo 7
    paciente = Paciente.get_or_none(Paciente.usuarioId_id == usuario_actual.id)
    ultima_cita = Cita.select().where(
        Cita.paciente == paciente.id).order_by(Cita.fecha.desc()).get()

    dieta = Dieta.get(Dieta.citaId == ultima_cita.id)
    arreglo_final = []

    for comida in dieta.comidas:
        alimentos = []
        if comida.dia == dia_semana:
            for relacion in comida.alimentosComida:
                alimentos.append({
                    "id_alimento": relacion.alimentoId.id,
                    "nombre": relacion.alimentoId.nombreAlimento,
		            "calorias": relacion.alimentoId.calorias,
		            "cantidad": relacion.cantidad,
                    "ingerido": relacion.ingerido,
                    "imagen": relacion.alimentoId.fotoAlimento
                })
            arreglo_final.append({
                "alimentos": alimentos,
		"id_comida": comida.id,
                "horario": comida.horarioId.horario,
                "dia": comida.dia
            })

    return jsonify({"contenido": arreglo_final, "codigo": 100})
