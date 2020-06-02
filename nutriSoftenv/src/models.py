from peewee import *

#db = SqliteDatabase('nutriapp.db')
db = MySQLDatabase("nutrisoft", host="localhost",
 port = 3306, user = "nutriologo", passwd = "NutriSoft@123")


class Rol(Model):
    rol = CharField(max_length=45, null=False)

    class Meta:
        database = db


class Usuario(Model):
    username = CharField(max_length=45, unique=True, null=False)
    password = CharField(max_length=256, null=False)
    nombre = CharField(max_length=45, null=False)
    apellidoPaterno = CharField(max_length=45, null=False)
    apellidoMaterno = CharField(max_length=45)
    correoElectronico = CharField(max_length=100, null=False)
    status = BooleanField(null=False, default=True)
    idRol = ForeignKeyField(Rol, on_delete='CASCADE')

    class Meta:
        database = db


class Paciente(Model):
    fechaNacimiento = DateField(null=False, formats=['%d-%m-%Y'])
    usuarioId = ForeignKeyField(Usuario, on_delete='CASCADE')
    fotoPerfil = CharField(null=True)

    class Meta:
        database = db


class Nutriologo(Model):
    usuarioId = ForeignKeyField(Usuario, on_delete='CASCADE')

    class Meta:
        database = db


class Mensaje(Model):
    asunto = CharField(max_length=45, null=False)
    mensaje = CharField(max_length=300, null=False)
    fecha = DateTimeField(null=False, formats=['%d-%m-%Y %H:%M:%S'])
    destinatario = ForeignKeyField(
        Usuario, on_delete='CASCADE', backref='mensajesDestinatario')
    remitente = ForeignKeyField(
        Usuario, on_delete='CASCADE', backref='mensajesRemitente')

    class Meta:
        database = db


class CatalogoStatus(Model):
    status = CharField(max_length=45, null=False)

    class Meta:
        database = db


class Medidas(Model):
    peso = FloatField(null=False)
    estatura = FloatField(null=False)
    cadera = FloatField(null=False)
    cintura = FloatField(null=False)
    pectoral = FloatField(null=False)

    class Meta:
        database = db


class Cita(Model):
    status = ForeignKeyField(CatalogoStatus, null=False, backref='statusCita')
    fecha = DateTimeField(null=False, formats=['%d-%m-%Y %H:%M:%S'])
    nutriologo = ForeignKeyField(
        Nutriologo, null=False, backref="citasNutriologo")
    comentarios = CharField(max_length=300)
    medidasId = ForeignKeyField(Medidas, on_delete='CASCADE')
    paciente = ForeignKeyField(Paciente, null=False, backref="citasPaciente")

    class Meta:
        database = db


class Dieta(Model):
    citaId = ForeignKeyField(Cita, null=False)

    class Meta:
        database = db


class Comida(Model):
    dietaId = ForeignKeyField(Dieta, null=False, backref="comidas")
    horario = CharField(null=False)

    class Meta:
        database = db


class Alimento(Model):
    nombreAlimento = CharField(null=False)
    calorias = IntegerField(null=False)

    class Meta:
        database = db


class ComidaTieneAlimento(Model):
    comidaId = ForeignKeyField(Comida, null=False, backref="alimentosComida")
    alimentoId = ForeignKeyField(Alimento, null=False)
    cantidad = IntegerField(null=False)

    class Meta:
        database = db


class Respueta:
    def __init__(self, codigo="", mensaje="", cuerpo=""):
        self.codigo = codigo
        self.mensaje = mensaje
        self.cuerpo = cuerpo


if __name__ == "__main__":
    db.connect()
    db.create_tables([Rol, Usuario, Paciente, Nutriologo, Mensaje, CatalogoStatus,
                      Medidas, Cita, Dieta, Comida, Alimento, ComidaTieneAlimento])
