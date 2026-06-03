from quart import jsonify, request, Blueprint, Quart
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database import async_session
from models import Usuario
import uuid
import hashlib
import bcrypt

user_bp = Blueprint('user', __name__)

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')

def hash_password(password: str) -> str:
    """Convierte una contraseña normal en un hash seguro para guardarlo"""

    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_bytes.decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """Comprueba si la contraseña que introduce el usuario coincide con el hash guardado"""

    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_token(user_id: int) -> str:
    """Crea un ticket (token) simple para que el usuario demuestre quién es"""

    user_id_str = str(user_id)
    token_hash = hashlib.sha1((user_id_str + str(Secret_uuid)).encode()).hexdigest()
    return f"{user_id_str}.{token_hash}"

async def get_user_from_token_orm():
    """
    Revisa la cabecera Authorization de la peticin, comprueba si el token es valido
    y devuelve los datos del usuario si todo esta bien
    """

    header = request.headers.get("Authorization")
    if not header or not header.startswith("Bearer "):
        return None, (jsonify({"error": "Falta token o formato incorrecto"}), 401)
    
    token_recibido = header.split(" ")[1]

    try:
        uid_str, token_hash = token_recibido.split('.')
        user_id = int(uid_str)
    except (IndexError, ValueError):
        return None, (jsonify({"error": "Token inválido"}), 401)

    expected_hash = hashlib.sha1((uid_str + str(Secret_uuid)).encode()).hexdigest()

    if token_hash != expected_hash:
        return None, (jsonify({"error": "Token inválido"}), 401)

    async with async_session() as session:
        user = await session.get(Usuario, user_id)
    
    if not user:
        return None, (jsonify({"error": "Usuario del token no encontrado"}), 404)
    
    return user, None

@user_bp.put("/user")
async def registrarUsuario():
    """Endpoint para crear un nuevo usuario registrarse en la base de datos"""

    try:
        datos = await request.get_json()
        if not datos or 'name' not in datos or 'password' not in datos:
            return jsonify({"error": "Faltan 'name' o 'password'"}), 400
        
        name = datos["name"]
        password = datos["password"]

        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(Usuario).where(Usuario.username == name)
                )
                existing_user = result.scalars().first()

                if existing_user:
                    return jsonify({"error": f"El usuario {name} ya existe"}), 400

                password_hash = hash_password(password)
                
                new_user = Usuario(
                    username=name,
                    password_hash=password_hash,
                    userrole='user', 
                    balance=0.00
                )

                session.add(new_user)


                await session.flush()
                
                user_id = new_user.userid
                token = generate_token(user_id)
                
                return jsonify({"message": f"Usuario {name} creado", "uid": user_id, "username": name, "token": token}), 200

    except SQLAlchemyError as e:
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


@user_bp.get("/user")
async def loginUsuario():
    """Endpoint para iniciar sesión. Comprueba usuario/contraseña y devuelve un token."""

    try:
        datos = await request.get_json()
        if not datos or 'name' not in datos or 'password' not in datos:
            return jsonify({"error": "Faltan 'name' o 'password'"}), 400

        name = datos["name"]
        password = datos["password"]
        
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(Usuario).where(Usuario.username == name)
                )
                user = result.scalars().first()

                if not user or not check_password(password, user.password_hash):
                    return jsonify({"error": "Usuario o contraseña incorrectos"}), 401
                
                user_id = user.userid
                token = generate_token(user_id)
                
                return jsonify({"message": f"Usuario {name} iniciado sesion", "uid": user_id, "token": token}), 200

    except SQLAlchemyError as e:
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

@user_bp.delete("/user/<int:user_id>")
async def delete_user(user_id):
    """Endpoint para borrar un usuario. Solo un admin puede hacerlo"""

    try:
        admin_user, error = await get_user_from_token_orm()
        if error:
            return error
        
        if admin_user.userrole != 'admin':
            return jsonify({"error": "Acceso denegado: Se requiere rol de administrador"}), 403

        async with async_session() as session:
            async with session.begin():
                user_to_delete = await session.get(Usuario, user_id)
                
                if not user_to_delete:
                    return jsonify({"error": "Usuario no encontrado"}), 404
                
                await session.delete(user_to_delete)
                
                return jsonify({"message": f"Usuario con UID {user_id} eliminado"}), 200

    except SQLAlchemyError as e:
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


app = Quart(__name__)
app.register_blueprint(user_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
