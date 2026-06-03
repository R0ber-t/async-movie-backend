from quart import Blueprint, jsonify, request, Quart
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database import engine
import uuid
import hashlib
from decimal import Decimal

api_bp = Blueprint('api', __name__)

Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')

"""FUNCIONES AUXILIARES"""

async def get_user_from_token():
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
    
    user = await fetch_one("SELECT * FROM users WHERE userid = :user_id", {"user_id": user_id})
    
    if not user:
        return None, (jsonify({"error": "Usuario del token no encontrado"}), 404)
    
    return user, None

async def fetch_all(query: str, params: dict = None):
    async with engine.connect() as conn:
        result = await conn.execute(text(query), params or {})
        rows = result.fetchall()
        if not rows:
            return []
        return [dict(row._mapping) for row in rows]

async def fetch_one(query: str, params: dict = None):
    async with engine.connect() as conn:
        result = await conn.execute(text(query), params or {})
        row = result.fetchone()
        if not row:
            return None
        return dict(row._mapping)

async def execute_query(query: str, params: dict = None, fetch_last_id: bool = False):
    async with engine.connect() as conn:
        async with conn.begin():
            result = await conn.execute(text(query), params or {})
            if fetch_last_id:
                row = result.fetchone()
                return row[0] if row else None
            return result.rowcount

"""Endpoints peliculas"""

@api_bp.post("/movies")
async def create_movie():
    datos = await request.get_json()
    if not datos or 'title' not in datos or 'price' not in datos:
        return jsonify({"error": "Faltan 'title' o 'price'"}), 400

    query = """
        INSERT INTO movies (title, moviedescription, movieyear, genre, price, stock)
        VALUES (:title, :description, :year, :genre, :price, :stock)
        RETURNING movieid
    """
    params = {
        "title": datos["title"],
        "description": datos.get("description"),
        "year": datos.get("year"),
        "genre": datos.get("genre"),
        "price": datos["price"],
        "stock": datos.get("stock", 0)
    }
    
    try:
        movie_id = await execute_query(query, params, fetch_last_id=True)
        return jsonify({"message": "Película creada", "movieid": movie_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.get("/movies/<int:movie_id>")
async def get_movie(movie_id):
    query = """
        SELECT movieid, title, moviedescription AS description, 
               movieyear AS year, genre, price, stock 
        FROM movies 
        WHERE movieid = :movie_id
    """
    movie = await fetch_one(query, {"movie_id": movie_id})
    if not movie:
        return jsonify({"error": "Película no encontrada"}), 404
    return jsonify(movie), 200

@api_bp.put("/movies/<int:movie_id>")
async def update_movie(movie_id):
    datos = await request.get_json()
    if not datos:
        return jsonify({"error": "No hay datos para actualizar"}), 400

    fields = []
    params = {"movie_id": movie_id}
    
    allowed_fields = ["title", "description", "year", "genre", "price", "stock"]
    db_field_map = {
        "description": "moviedescription",
        "year": "movieyear",
        "title": "title",
        "genre": "genre",
        "price": "price",
        "stock": "stock"
    }

    for field in allowed_fields:
        if field in datos:
            db_field = db_field_map[field]
            fields.append(f"{db_field} = :{field}")
            params[field] = datos[field]

    if not fields:
        return jsonify({"error": "Ningún campo válido para actualizar"}), 400
    
    query = f"UPDATE movies SET {', '.join(fields)} WHERE movieid = :movie_id"
    
    try:
        rows_affected = await execute_query(query, params)
        if rows_affected == 0:
            return jsonify({"error": "Película no encontrada"}), 404
        return jsonify({"message": "Película actualizada"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.delete("/movies/<int:movie_id>")
async def delete_movie(movie_id):
    query = "DELETE FROM movies WHERE movieid = :movie_id"
    try:
        rows_affected = await execute_query(query, {"movie_id": movie_id})
        if rows_affected == 0:
            return jsonify({"error": "Película no encontrada"}), 404
        return jsonify({"message": "Película eliminada"}), 200
    except IntegrityError:
        return jsonify({"error": "No se puede borrar, la película está en un pedido"}), 409

"""Endpoints actores"""

@api_bp.post("/actors")
async def create_actor():
    datos = await request.get_json()
    if not datos or 'actorname' not in datos:
        return jsonify({"error": "Falta 'actorname'"}), 400

    query = "INSERT INTO actors (actorname) VALUES (:name) RETURNING actorid"
    actor_id = await execute_query(query, {"name": datos["actorname"]}, fetch_last_id=True)
    return jsonify({"message": "Actor creado", "actorid": actor_id}), 201

@api_bp.get("/actors")
async def get_all_actors():
    query = "SELECT * FROM actors ORDER BY actorname"
    actors = await fetch_all(query)
    return jsonify(actors), 200

@api_bp.get("/actors/<int:actor_id>")
async def get_actor(actor_id):
    query = "SELECT * FROM actors WHERE actorid = :actor_id"
    actor = await fetch_one(query, {"actor_id": actor_id})
    if not actor:
        return jsonify({"error": "Actor no encontrado"}), 404
    return jsonify(actor), 200

@api_bp.put("/actors/<int:actor_id>")
async def update_actor(actor_id):
    datos = await request.get_json()
    if not datos or 'actorname' not in datos:
        return jsonify({"error": "Falta 'actorname'"}), 400

    query = "UPDATE actors SET actorname = :name WHERE actorid = :actor_id"
    params = {"name": datos["actorname"], "actor_id": actor_id}
    
    rows_affected = await execute_query(query, params)
    if rows_affected == 0:
        return jsonify({"error": "Actor no encontrado"}), 404
    
    return jsonify({"message": "Actor actualizado"}), 200

@api_bp.delete("/actors/<int:actor_id>")
async def delete_actor(actor_id):
    query = "DELETE FROM actors WHERE actorid = :actor_id"
    try:
        rows_affected = await execute_query(query, {"actor_id": actor_id})
        if rows_affected == 0:
            return jsonify({"error": "Actor no encontrado"}), 404
        return jsonify({"message": "Actor eliminado"}), 200
    except IntegrityError:
        return jsonify({"error": "No se puede eliminar, el actor participa en una película"}), 409

"""Enspoints cliente y carrito"""

@api_bp.get("/client/profile")
async def get_client_profile():
    user, error = await get_user_from_token()
    if error:
        return error
    
    profile = {
        "userid": user["userid"],
        "username": user["username"],
        "userrole": user["userrole"],
        "balance": user["balance"]
    }
    return jsonify(profile), 200

@api_bp.post("/user/credit")
async def add_balance():
    user, error = await get_user_from_token()
    if error:
        return error
    
    datos = await request.get_json()
    try:
        amount = Decimal(datos.get("amount", 0))
    except Exception:
        return jsonify({"error": "Cantidad inválida"}), 400

    if amount <= 0:
        return jsonify({"error": "La cantidad debe ser positiva"}), 400

    query = """
        UPDATE users
        SET balance = balance + :amount
        WHERE userid = :user_id
        RETURNING balance
    """
    params = {"amount": amount, "user_id": user["userid"]}
    
    new_balance = await execute_query(query, params, fetch_last_id=True)
    return jsonify({"message": "Saldo actualizado", "new_credit": new_balance}), 200

@api_bp.get("/cart")
async def get_cart():
    user, error = await get_user_from_token()
    if error:
        return error

    query = """
        SELECT m.movieid, m.title, moviedescription AS description, 
               m.movieyear AS year, m.genre, m.price 
        FROM movies m
        JOIN cart_items c ON m.movieid = c.movieid
        WHERE c.userid = :user_id
    """
    cart_items = await fetch_all(query, {"user_id": user["userid"]})
    return jsonify(cart_items), 200

@api_bp.put("/cart/<int:movie_id>")
async def add_to_cart(movie_id):
    user, error = await get_user_from_token()
    if error:
        return error

    query = """
        INSERT INTO cart_items (userid, movieid)
        VALUES (:user_id, :movie_id)
        ON CONFLICT (userid, movieid) DO NOTHING
    """
    params = {"user_id": user["userid"], "movie_id": movie_id}
    
    try:
        rows_affected = await execute_query(query, params)
        if rows_affected == 0:
            return jsonify({"error": "La película ya está en el carrito"}), 409
        return jsonify({"message": "Película añadida al carrito"}), 200
    except IntegrityError:
        return jsonify({"error": "Película no encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.delete("/cart/<int:movie_id>")
async def remove_from_cart(movie_id):
    user, error = await get_user_from_token()
    if error:
        return error
    
    query = "DELETE FROM cart_items WHERE userid = :user_id AND movieid = :movie_id"
    params = {"user_id": user["userid"], "movie_id": movie_id}
    
    rows_affected = await execute_query(query, params)
    if rows_affected == 0:
        return jsonify({"error": "Película no encontrada en el carrito"}), 404
    
    return jsonify({"message": "Película eliminada del carrito"}), 200

@api_bp.post("/cart/checkout")
async def pay_cart():
    user, error = await get_user_from_token()
    if error:
        return error
    
    user_id = user["userid"]
    
    async with engine.connect() as conn:
        async with conn.begin(): 
            try:
                cart_query = """
                    SELECT movieid, price FROM movies 
                    WHERE movieid IN (SELECT movieid FROM cart_items WHERE userid = :user_id)
                """
                cart_items_result = await conn.execute(text(cart_query), {"user_id": user_id})
                items = cart_items_result.fetchall()
                
                if not items:
                    return jsonify({"error": "El carrito está vacío"}), 400

                total_bruto = sum(Decimal(item.price) for item in items)

                create_order_query = """
                    INSERT INTO orders (userid, total_price, order_date)
                    VALUES (:user_id, :total, current_timestamp)
                    RETURNING orderid
                """
                order_result = await conn.execute(text(create_order_query), {
                    "user_id": user_id, 
                    "total": total_bruto
                })
                
                order_id = order_result.fetchone()[0]
                
                order_items_query = """
                    INSERT INTO order_items (orderid, movieid, price_at_purchase)
                    VALUES (:order_id, :movie_id, :price)
                """
                for item in items:
                    await conn.execute(text(order_items_query), {
                        "order_id": order_id,
                        "movie_id": item.movieid, 
                        "price": Decimal(item.price)
                    })
                
                await conn.execute(text("DELETE FROM cart_items WHERE userid = :user_id"), {"user_id": user_id})
                
                return jsonify({"message": "Compra realizada con éxito", "orderid": order_id}), 200
            
            except Exception as e:
                err_msg = str(e)
                if "Saldo insuficiente" in err_msg:
                    return jsonify({"error": "Saldo insuficiente (Rechazado por BBDD)"}), 402
                return jsonify({"error": f"Error en la transacción: {err_msg}"}), 500

@api_bp.get("/orders/<int:order_id>")
async def get_order(order_id):
    user, error = await get_user_from_token()
    if error:
        return error
    
    order_query = """
        SELECT orderid, total_price, order_date as date FROM orders
        WHERE orderid = :order_id AND userid = :user_id
    """
    order = await fetch_one(order_query, {"order_id": order_id, "user_id": user["userid"]})
    
    if not order:
        return jsonify({"error": "Pedido no encontrado"}), 404

    items_query = """
        SELECT m.movieid, m.title, m.moviedescription AS description, 
               m.movieyear AS year, oi.price_at_purchase as price
        FROM order_items oi
        JOIN movies m ON oi.movieid = m.movieid
        WHERE oi.orderid = :order_id
    """
    items = await fetch_all(items_query, {"order_id": order_id})
    
    order["movies"] = items
    return jsonify(order), 200

"""ENDPOINTS VOTACIONES"""

@api_bp.post("/movies/<int:movie_id>/vote")
async def vote_movie(movie_id):
    user, error = await get_user_from_token()
    if error:
        return error
    
    datos = await request.get_json()
    rating = datos.get("rating")
    
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"error": "La votación debe ser entre 1 y 5"}), 400
    
    query = """
        INSERT INTO movie_votes (userid, movieid, rating)
        VALUES (:user_id, :movie_id, :rating)
        ON CONFLICT (userid, movieid) DO UPDATE
        SET rating = :rating
    """
    params = {"user_id": user["userid"], "movie_id": movie_id, "rating": rating}
    
    await execute_query(query, params)
    return jsonify({"message": "Voto registrado"}), 201

@api_bp.get("/movies/<int:movie_id>/rating")
async def get_movie_rating(movie_id):
    query = """
        SELECT average_rating, 0 as total_votes 
        FROM movies WHERE movieid = :movie_id
    """
    rating_data = await fetch_one(query, {"movie_id": movie_id})
    if not rating_data:
        return jsonify({"average_rating": 0}), 200

    return jsonify(rating_data), 200

@api_bp.get("/movies")
async def get_movies_advanced():
    args = request.args
    query = """
        SELECT m.movieid, m.title, m.moviedescription AS description, 
               m.movieyear AS year, m.genre, m.price, m.stock, 
               m.average_rating
        FROM movies m
    """
    joins = []
    where_clauses = []
    params = {}

    if "actor" in args:
        joins.append("JOIN movie_actors ma ON m.movieid = ma.movieid")
        joins.append("JOIN actors a ON ma.actorid = a.actorid")
        where_clauses.append("a.actorname ILIKE :actor_name")
        params["actor_name"] = f"%{args['actor']}%"

    if "title" in args:
        where_clauses.append("m.title ILIKE :title")
        params["title"] = f"%{args['title']}%"
        
    if "genre" in args:
        where_clauses.append("m.genre = :genre")
        params["genre"] = args["genre"]

    if "year" in args:
        try:
            where_clauses.append("m.movieyear = :year")
            params["year"] = int(args["year"])
        except ValueError:
            pass

    if joins:
        query += " " + " ".join(joins)
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY m.movieid"
    
    if "top_n" in args:
        query += " ORDER BY m.average_rating DESC"
        try:
            params["top_n"] = int(args["top_n"])
            query += " LIMIT :top_n"
        except ValueError:
            pass
    else:
        query += " ORDER BY m.title"
    
    movies = await fetch_all(query, params)
    return jsonify(movies), 200

"""Endpoints nuevos para la práctica"""

@api_bp.get("/estadisticaVentas/<int:year>/<string:country>")
async def estadisticaVentas(year, country):
    query = """
        SELECT o.orderid, o.order_date, o.total_price, u.username, u.nationality
        FROM orders o
        JOIN users u ON o.userid = u.userid
        WHERE u.nationality = :country
        AND EXTRACT(YEAR FROM o.order_date) = :year
    """
    try:
        results = await fetch_all(query, {"country": country, "year": year})
        safe_results = []
        for row in results:
            d = dict(row)
            d['order_date'] = str(d['order_date'])
            safe_results.append(d)

        return jsonify({"year": year, "country": country, "sales": safe_results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.get("/clientesSinPedidos")
async def clientesSinPedidos():
    query = """
        SELECT u.userid, u.username, u.nationality, u.balance
        FROM users u
        LEFT JOIN orders o ON u.userid = o.userid
        WHERE o.orderid IS NULL
    """
    try:
        results = await fetch_all(query)
        return jsonify({"clientes_sin_compras": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

"""Transacciones de borrado de Pais"""

@api_bp.delete("/borraPais/<string:country>")
async def borraPais(country):
    query_get_users = "SELECT userid FROM users WHERE nationality = :country"
    
    async with engine.connect() as conn:
        async with conn.begin(): 
            try:
                result = await conn.execute(text(query_get_users), {"country": country})
                users = result.fetchall()
                
                if not users:
                    return jsonify({"message": "No hay usuarios de ese país"}), 200

                user_ids = [u.userid for u in users]

                q_del_items = """
                    DELETE FROM order_items 
                    WHERE orderid IN (SELECT orderid FROM orders WHERE userid = ANY(:uids))
                """
                await conn.execute(text(q_del_items), {"uids": user_ids})

                await conn.execute(text("DELETE FROM orders WHERE userid = ANY(:uids)"), {"uids": user_ids})

                await conn.execute(text("DELETE FROM cart_items WHERE userid = ANY(:uids)"), {"uids": user_ids})

                await conn.execute(text("DELETE FROM movie_votes WHERE userid = ANY(:uids)"), {"uids": user_ids})

                await conn.execute(text("DELETE FROM users WHERE userid = ANY(:uids)"), {"uids": user_ids})

                return jsonify({"message": f"Usuarios de {country} eliminados correctamente"}), 200
            
            except Exception as e:
                return jsonify({"error": f"Error en transacción: {str(e)}"}), 500

@api_bp.delete("/borraPaisIncorrecto/<string:country>")
async def borraPaisIncorrecto(country):
    async with engine.connect() as conn:
        async with conn.begin(): 
            try:
                q_del_users = "DELETE FROM users WHERE nationality = :country"
                await conn.execute(text(q_del_users), {"country": country})
                return jsonify({"message": "ERROR: Esto no debería ejecutarse"}), 200
            except IntegrityError as e:
                return jsonify({"error": "Borrado fallido, Rollback ejecutado", "detail": str(e)}), 409
            except Exception as e:
                return jsonify({"error": str(e)}), 500

@api_bp.delete("/borraPaisIntermedio/<string:country>")
async def borraPaisIntermedio(country):
    async with engine.connect() as conn:
        try:
            transaccion_a = await conn.begin()
            
            res = await conn.execute(text("SELECT userid FROM users WHERE nationality = :c"), {"c": country})
            users = res.fetchall()
            user_ids = [u.userid for u in users]
            
            if not user_ids:
                 await transaccion_a.rollback()
                 return jsonify({"message": "No users"}), 200

            await conn.execute(text("DELETE FROM cart_items WHERE userid = ANY(:uids)"), {"uids": user_ids})
            await transaccion_a.commit() 
            
            transaccion_b = await conn.begin()
            try:
                await conn.execute(text("DELETE FROM users WHERE userid = ANY(:uids)"), {"uids": user_ids})
                await transaccion_b.commit()
            except IntegrityError:
                await transaccion_b.rollback()
                return jsonify({"message": "Rollback parcial realizado"}), 409
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"message": "Fin"}), 200


app = Quart(__name__)
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051, debug=True)