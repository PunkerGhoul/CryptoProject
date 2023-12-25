from db_controller import conectar
from PwdGenerator import generate_secure_password as gsp
from typing import Annotated, Optional
from fastapi import FastAPI, Path, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import starlette.status as status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from DiffieHellman import DiffieHellman
import bcrypt

from pydantic import BaseModel
from fastapi import HTTPException, FastAPI, Response, Depends
from uuid import UUID, uuid4

from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters


# La clase `SessionData` tiene un solo atributo `usuario_id` de tipo string.
class SessionData(BaseModel):
    usuario_id: str


# El objeto CookieParameters es una subclase de CookieParameters que contiene los parámetros de la cookie.
cookie_params = CookieParameters()

# El objeto SessionCookie es una subclase de SessionFrontend que utiliza cookies para almacenar
# los datos de la sesión. El objeto SessionCookie recibe los siguientes parámetros:
# - cookie_name: nombre de la cookie
# - identifier: identificador del verificador de sesión
# - auto_error: si es True, el objeto SessionCookie lanzará una excepción HTTPException si no se
#   encuentra la cookie o si la cookie no es válida
# - secret_key: clave secreta para firmar la cookie
# - cookie_params: parámetros de la cookie
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=False,
    secret_key=gsp(16),
    cookie_params=cookie_params,
)

# El objeto InMemoryBackend es una subclase de Backend que almacena los datos de la sesión en
# memoria.
backend = InMemoryBackend[UUID, SessionData]()


# La clase BasicVerifier es una subclase de SessionVerifier que verifica los datos de la sesión
# utilizando UUID como clave.
class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


# En verifier se está creando una instancia de la clase BasicVerifier con el identificador
# "general_verifier", configurando el indicador auto_error en False y proporcionando un backend y un
# objeto HTTPException para manejar los errores de autenticación. El objeto HTTPException especifica
# un código de estado 403, un mensaje detallado de "sesión no válida" y una ubicación de redirección a
# "/login".
verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=False,
    backend=backend,
    auth_http_exception=HTTPException(
        status_code=403, detail="invalid session", headers={"Location": "/login"}),
)


app = FastAPI()
 
# Se está montando un directorio llamado "estático" como un directorio de archivos
# estáticos para la aplicación FastAPI. Esto significa que la aplicación puede acceder a cualquier
# archivo en el directorio "estático" a través de la ruta URL "/static".
app.mount("/static", StaticFiles(directory="static"), name="static")

# Se importa la clase Jinja2Templates de la biblioteca Jinja2 y crea una instancia con
# el parámetro de directorio establecido en "plantillas". Es probable que se esté utilizando en una
# aplicación web para representar plantillas HTML mediante el motor de plantillas Jinja2.
templates = Jinja2Templates(directory="templates")


@app.post("/api/logout")
async def logout(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("login-signup/signup.html", {"request": request})


@app.post("/api/register")
async def register(nombres: Annotated[str, Form()], apellidos: Annotated[str, Form()], correo: Annotated[str, Form()], password: Annotated[str, Form()], confirm_password: Annotated[str, Form()]):
    if password != confirm_password:
        # return {"message": "Las contraseñas no coinciden. Inténtelo de nuevo."}
        return RedirectResponse(url="/register", status_code=status.HTTP_302_FOUND)

    try:
        cn = conectar()
        cursor = cn.cursor()
        # Verificar si el usuario ya existe en la base de datos
        cursor.execute(
            "SELECT correo FROM usuarios WHERE correo = %s;", (correo,))
        result = cursor.fetchone()

        if result:
            return {"message": "El registro no fue exitoso."}
        # Genera un salt aleatorio
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        # Si el usuario no existe, insertarlo en la base de datos
        cursor.execute(
            "INSERT INTO usuarios (nombres, apellidos, correo, contrasena) VALUES (%s, %s, %s, %s);", (nombres, apellidos, correo, hashed_password))
        cn.commit()
        cn.close()
    except Exception as e:
        # return {"message": "Error al conectar a la base de datos", "error": e}
        return RedirectResponse(url="/register", status_code=status.HTTP_302_FOUND)
    # return {"message": "Usuario registrado con éxito"}
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login-signup/login.html", {"request": request})


@app.post("/api/login")
async def login(request: Request, response: Response, correo: Annotated[str, Form()], password: Annotated[str, Form()]):
    error_message = "El correo o la contraseña son incorrectos."
    try:
        cn = conectar()
        cursor = cn.cursor()
        cursor.execute(
            "SELECT id_usuario, correo, contrasena FROM usuarios WHERE correo = %s;", (correo,))
        result = cursor.fetchone()

        if not result:
            return templates.TemplateResponse("login-signup/login.html", {"request": request, "error_message": error_message}, status_code=403)

        id_usuario, correo_db, hashed_password = result
        if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

        cn.close()
        session = uuid4()
        data = SessionData(usuario_id=id_usuario)

        await backend.create(session, data)
        cookie.attach_to_response(response, session)
        response.headers["Location"] = f"/dashboard/{id_usuario}"
        response.status_code = status.HTTP_302_FOUND
        return response

    except Exception as e:
        print(e)
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


def get_usuarios():
    """
    Esta función recupera una lista de usuarios de una base de datos y la devuelve como una lista de
    diccionarios que contienen su ID, nombre y apellido.
    :return: una lista de diccionarios, donde cada diccionario representa un usuario con su id, nombre y
    apellido. Si hay un error al conectarse a la base de datos, la función devuelve un diccionario con
    un mensaje que indica el error.
    """
    try:
        cn = conectar()
        cursor = cn.cursor()
        cursor.execute("SELECT id_usuario, nombres, apellidos FROM usuarios;")
        rows = cursor.fetchall()
        usuarios = [
            {"id_usuario": row[0], "nombres": row[1], "apellidos": row[2]}
            for row in rows
        ]
        cn.close()
        return usuarios
    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}


def get_mensajes(id_conversacion: int, id_usuario: int):
    # El código anterior está seleccionando todos los mensajes de una conversación donde la ID de
    # usuario no es igual a una ID de usuario determinada. Luego devuelve una lista de diccionarios
    # que contienen el ID del mensaje, el ID de la conversación y el ID del usuario para cada mensaje.
    # Si hay un error al conectarse a la base de datos, devuelve un diccionario con un mensaje de
    # error.
    try:
        cn = conectar()
        cursor = cn.cursor()
        cursor.execute(
            "SELECT id_mensaje, id_conversacion, id_usuario FROM mensajes WHERE id_conversacion = %s AND id_usuario != %s;",
            (id_conversacion, id_usuario,)
        )
        rows = cursor.fetchall()
        mensajes = [
            {"id_mensaje": row[0], "id_conversacion": row[1],
                "id_usuario": row[2]}
            for row in rows
        ]
        cn.close()
        return mensajes
    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}


@ app.get("/dashboard/{id_usuario}", response_class=HTMLResponse, dependencies=[Depends(cookie)])
async def dashboard(request: Request, id_usuario: int = 0, nombre_usuario: str = "Usuario", usuarios: list = get_usuarios(), session_data: SessionData = Depends(verifier)):
    if session_data is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    try:
        cn = conectar()
        cursor = cn.cursor()

        cursor.execute(
            "SELECT id_usuario, nombres, apellidos FROM usuarios WHERE id_usuario = %s;", (
                id_usuario,)
        )
        result = cursor.fetchone()

        if result:
            id_usuario, nombres, apellidos = result
            nombre_usuario = nombres + " " + apellidos

        cn.close()

    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}
    return templates.TemplateResponse("dashboard/index.html", {"request": request, "id_usuario": id_usuario, "nombre_usuario": nombre_usuario, "usuarios": usuarios})


@ app.get("/api/gen_conversation_keys")
async def gen_conversation_keys(id_usuario_remitente, id_usuario_destinatario, num_keys: Optional[Annotated[int, Path(title="Cantidad de claves a generar", gt=0, lt=3)]] = None,):
    # def gen_conversation_keys(num_keys: int = 2):
    if id_usuario_remitente == id_usuario_destinatario:
        return {"message": "No es posible generar llaves para una conversación con el mismo usuario"}
    keys = {}
    if num_keys is None:
        num_keys = 2
    try:
        cn = conectar()
        cursor = cn.cursor()
        cursor.execute(
            "SELECT id_conversacion FROM conversaciones WHERE (id_usuario1 = %(remitente)s OR id_usuario1 = %(destinatario)s) AND (id_usuario2 = %(remitente)s OR id_usuario2 = %(destinatario)s);",
            {"remitente": id_usuario_remitente,
                "destinatario": id_usuario_destinatario}
        )
        result = cursor.fetchone()
        if result:
            return {"message": "Ya existen llaves para esta conversación"}
        dh = DiffieHellman()
        if num_keys == 1:
            return {"key": dh.generate_prime_number()}
        elif num_keys == 2:
            keys["p"] = dh.generate_prime_number()
            keys["k"] = dh.generate_prime_number()
            while keys["k"] > keys["p"]:
                keys["k"] = dh.generate_prime_number()
        print(keys)
        cursor.execute(
            "INSERT INTO conversaciones (p, k, id_usuario1, id_usuario2) VALUES (%(p)s, %(k)s, %(id_usuario1)s, %(id_usuario2)s);",
            {"p": keys["p"], "k": keys["k"], "id_usuario1": id_usuario_remitente,
                "id_usuario2": id_usuario_destinatario}
        )
        cn.commit()
        if cursor.rowcount != 1:
            return {"message": "No fue posible crear la conversación"}
        cn.close()
    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}
    return keys


@ app.get("/api/set_pubkey")
async def set_pubkey(id_usuario_remitente, id_usuario_destinatario, pub_key):
    if id_usuario_remitente == id_usuario_destinatario:
        return {"message": "No es posible establecer una conversación con el mismo usuario"}
    if not pub_key:
        return {"message": "No se ha recibido la llave pública"}
    try:
        cn = conectar()
        cursor = cn.cursor()

        cursor.execute(
            "SELECT id_conversacion, id_usuario1, id_usuario2 FROM conversaciones WHERE (id_usuario1 = %(remitente)s OR id_usuario2 = %(remitente)s) AND (id_usuario1 = %(destinatario)s OR id_usuario2 = %(destinatario)s);",
            {"remitente": id_usuario_remitente,
                "destinatario": id_usuario_destinatario}
        )
        result = cursor.fetchone()

        if result:
            id_conversacion, id_usuario1, id_usuario2 = result
            if int(id_usuario_remitente) == int(id_usuario1) and int(id_usuario_destinatario) == int(id_usuario2):
                cursor.execute(
                    "UPDATE conversaciones SET A = %(pub_key)s WHERE id_conversacion = %(conversacion)s;",
                    {"pub_key": pub_key, "conversacion": id_conversacion}
                )
            else:
                cursor.execute(
                    "UPDATE conversaciones SET B = %(pub_key)s WHERE id_conversacion = %(conversacion)s;",
                    {"pub_key": pub_key, "conversacion": id_conversacion}
                )
            cn.commit()
            cn.close()
            return {"message": "Llave pública establecida correctamente"}
        cn.close()
        return {"message": "No fue posible establecer la llave pública"}

    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}


@app.get("/api/get_conv_p_pub_key")
async def get_conv_p_pub_key(id_usuario_remitente=Annotated[int, Form()], id_usuario_destinatario=Annotated[int, Form()]):
    if id_usuario_remitente == id_usuario_destinatario:
        return {"message": "No es posible enviar un mensaje al mismo usuario"}

    try:
        cn = conectar()
        cursor = cn.cursor()
        cursor.execute(
            "SELECT id_conversacion, id_usuario1, id_usuario2 FROM conversaciones WHERE (id_usuario1 = %(remitente)s OR id_usuario2 = %(remitente)s) AND (id_usuario1 = %(destinatario)s OR id_usuario2 = %(destinatario)s);",
            {"remitente": id_usuario_remitente,
                "destinatario": id_usuario_destinatario}
        )
        result = cursor.fetchone()

        if result:
            id_conversacion, id_usuario1, id_usuario2 = result
            if int(id_usuario_remitente) == int(id_usuario1) and int(id_usuario_destinatario) == int(id_usuario2):
                cursor.execute(
                    "SELECT id_conversacion, p, k, B FROM conversaciones WHERE id_usuario1 = %(remitente)s AND id_usuario2 = %(destinatario)s;",
                    {"remitente": id_usuario_remitente,
                     "destinatario": id_usuario_destinatario}
                )
            else:
                cursor.execute(
                    "SELECT id_conversacion, p, k, A FROM conversaciones WHERE id_usuario1 = %(destinatario)s AND id_usuario2 = %(remitente)s;",
                    {"remitente": id_usuario_remitente,
                     "destinatario": id_usuario_destinatario}
                )

        result = cursor.fetchone()
        cn.close()

        if result:
            id_conversacion, p, k, pub_key = result
            return {"id_conversacion": id_conversacion, "p": p, "k": k, "pub_key": pub_key}

        return {"message": "No se pudieron obtener los datos"}

    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}


@app.get("/api/get_messages")
async def get_messages(id_usuario_remitente=Annotated[int, Form()], id_usuario_destinatario=Annotated[int, Form()]):
    if id_usuario_remitente == id_usuario_destinatario:
        return {"message": "No es posible obtener mensajes de enviados desde el mismo usuario"}

    try:
        cn = conectar()
        cursor = cn.cursor()
        cursor.execute(
            "SELECT id_conversacion FROM conversaciones WHERE (id_usuario1 = %(remitente)s OR id_usuario2 = %(remitente)s) AND (id_usuario1 = %(destinatario)s OR id_usuario2 = %(destinatario)s);",
            {"remitente": id_usuario_remitente,
                "destinatario": id_usuario_destinatario}
        )
        result = cursor.fetchone()
        if result:
            id_conversacion = result[0]
            cursor.execute(
                "SELECT id_mensaje, id_conversacion, mensaje, id_usuario FROM mensajes WHERE id_conversacion = %(conversacion)s AND id_usuario != %(destinatario)s ORDER BY id_mensaje DESC;",
                {"conversacion": id_conversacion,
                    "destinatario": id_usuario_destinatario}
            )
        result = cursor.fetchall()
        cn.close()

        if result:
            messages = []
            for id_mensaje, id_conversacion, mensaje, id_usuario in result:
                messages.append({"id_mensaje": id_mensaje, "id_conversacion": id_conversacion,
                                "id_usuario_remitente": id_usuario, "mensaje_enc": mensaje})
            return {"messages": messages}

    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}

    return {"message": "No se pudieron obtener los datos"}


@app.post("/api/send_message")
async def send_message(id_usuario_remitente: Annotated[int, Form()], id_usuario_destinatario: Annotated[int, Form()], mensaje_enc: Annotated[str, Form()]):
    if id_usuario_remitente == id_usuario_destinatario:
        return {"message": "No es posible enviar un mensaje al mismo usuario"}

    try:
        cn = conectar()
        cursor = cn.cursor()

        # Consultar el id_conversacion
        cursor.execute(
            "SELECT id_conversacion FROM conversaciones WHERE (id_usuario1 = %(remitente)s AND id_usuario2 = %(destinatario)s) OR (id_usuario1 = %(destinatario)s AND id_usuario2 = %(remitente)s);",
            {"remitente": str(id_usuario_remitente),
             "destinatario": str(id_usuario_destinatario)}
        )
        id_conversacion = cursor.fetchone()

        if id_conversacion:
            id_conversacion = id_conversacion[0]

            # Insertar el mensaje en la tabla mensajes
            cursor.execute(
                "INSERT INTO mensajes (mensaje, id_conversacion, id_usuario) VALUES (%s, %s, %s);",
                (mensaje_enc,
                 id_conversacion,
                 id_usuario_remitente)
            )
            cn.commit()
        else:
            return {"message": "No se pudo enviar el mensaje"}

    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}

    finally:
        cursor.close()
        cn.close()

    return {"message": "Mensaje enviado correctamente"}


@app.get("/dashboard/{id_usuario}/cifrado", dependencies=[Depends(cookie)])
async def cifrado(request: Request, id_usuario: int = 0, nombre_usuario: str = "Usuario", usuarios: list = get_usuarios(), session_data: dict = Depends(verifier)):
    if session_data is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    try:
        cn = conectar()
        cursor = cn.cursor()

        cursor.execute(
            "SELECT nombres, apellidos FROM usuarios WHERE id_usuario = %s;",
            (id_usuario,)
        )
        nombres, apellidos = cursor.fetchone() or (
            nombre_usuario.split()[0], nombre_usuario.split()[1])

        cn.close()

    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}

    return templates.TemplateResponse("dashboard/cifrado.html", {"request": request, "id_usuario": id_usuario, "nombre_usuario": nombres + " " + apellidos, "usuarios": usuarios})


@app.get("/dashboard/{id_usuario}/Bentrada", dependencies=[Depends(cookie)])
async def bentrada(request: Request, id_usuario: int = 0, nombre_usuario: str = "Usuario", usuarios: list = get_usuarios(), mensajes: list = None, session_data: dict = Depends(verifier)):
    if session_data is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    if mensajes is None:
        mensajes = []
    try:
        cn = conectar()
        cursor = cn.cursor()

        cursor.execute(
            "SELECT nombres, apellidos FROM usuarios WHERE id_usuario = %s;", (
                id_usuario,)
        )
        result = cursor.fetchone()

        if result:
            nombres, apellidos = result
            nombre_usuario = nombres + " " + apellidos

            cursor.execute(
                "SELECT id_conversacion FROM conversaciones WHERE id_usuario1 = %(remitente)s OR id_usuario2 = %(remitente)s;",
                {"remitente": id_usuario}
            )
            result = cursor.fetchall()

            for id_conversacion in result:
                mensajes.append(get_mensajes(id_conversacion[0], id_usuario))

        cn.close()

    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}

    return templates.TemplateResponse("dashboard/Bentrada.html", {"request": request, "id_usuario": id_usuario, "nombre_usuario": nombre_usuario, "usuarios": usuarios, "mensajes": mensajes})


@app.get("/dashboard/{id_usuario}/Benviados", dependencies=[Depends(cookie)])
async def benviados(request: Request, id_usuario: int = 0, nombre_usuario: str = "Usuario", usuarios: list = get_usuarios(), session_data=Depends(verifier)):
    if session_data is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    try:
        cn = conectar()
        cursor = cn.cursor()

        cursor.execute(
            "SELECT nombres, apellidos FROM usuarios WHERE id_usuario = %s;", (
                id_usuario,)
        )
        result = cursor.fetchone()

        if result:
            nombres, apellidos = result
            nombre_usuario = nombres + " " + apellidos

        cn.close()

    except Exception as e:
        print(e)
        return {"message": "Error al conectar a la base de datos"}

    return templates.TemplateResponse("dashboard/Benviados.html", {"request": request, "id_usuario": id_usuario, "nombre_usuario": nombre_usuario, "usuarios": usuarios})

# Iniciar la aplicación FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
