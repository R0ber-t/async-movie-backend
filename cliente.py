import requests
from http import HTTPStatus
import json
from datetime import datetime  

USERS = "http://127.0.0.1:5050"
CATALOG = "http://127.0.0.1:5051"


TEST_MOVIE_ID = None
TEST_ACTOR_ID = None

def ok(name, cond):
    status = "OK" if cond else "FAIL"
    print(f"[{status}] {name}")
    return cond

def main():
    global TEST_MOVIE_ID, TEST_ACTOR_ID

    print("# =======================================================")
    print("# Creación y autenticación de usuarios para el test")
    print("# =======================================================")


    r = requests.get(f"{USERS}/user", json={"name": "admin", "password": "admin"})
    if ok("Autenticar usuario administrador predefinido", r.status_code == HTTPStatus.OK):
        data = r.json()
        _, token_admin = data["uid"], data["token"]
    else:
        print("\nPruebas incompletas: Fin del test por error crítico")
        exit(-1)

    headers_admin = {"Authorization": f"Bearer {token_admin}"}


    r = requests.put(f"{USERS}/user", json={"name": "alice", "password": "secret"}, headers=headers_admin)
    if ok("Crear usuario 'alice'", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        uid_alice, _ = data["uid"], data["username"]
    else:
        print("\nPruebas incompletas: Fin del test por error crítico")
        exit(-1)

    r = requests.get(f"{USERS}/user", json={"name": "alice", "password": "secret"})
    if ok("Autenticar usuario 'alice'", r.status_code == HTTPStatus.OK and r.json()["uid"] == uid_alice):
        data = r.json()
        _, token_alice = data["uid"], data["token"]
    else:
        print("\nPruebas incompletas: Fin del test por error crítico")
        exit(-1) 

    headers_alice = {"Authorization": f"Bearer {token_alice}"}
    

    
    print("\n# =======================================================")
    print("# 1. CRUD de Actores y Películas (Extensivo)")
    print("# =======================================================")


    

    r = requests.post(f"{CATALOG}/actors", json={"actorname": "Test Actor Temp"}, headers=headers_admin)
    if ok("CRUD A: Crear actor 'Test Actor Temp'", r.status_code == HTTPStatus.CREATED and r.json()):
        TEST_ACTOR_ID = r.json().get('actorid')
        

    r = requests.get(f"{CATALOG}/actors/{TEST_ACTOR_ID}", headers=headers_alice)
    ok(f"CRUD A: Consultar actor con ID [{TEST_ACTOR_ID}]", r.status_code == HTTPStatus.OK and r.json().get('actorname') == "Test Actor Temp")
    

    r = requests.put(f"{CATALOG}/actors/{TEST_ACTOR_ID}", json={"actorname": "Test Actor Updated"}, headers=headers_admin)
    ok(f"CRUD A: Actualizar actor con nuevo nombre", r.status_code == HTTPStatus.OK)
    

    

    new_movie_data = {
        "title": "Z Test Movie", 
        "description": "Película temporal para pruebas de CRUD.",
        "year": 2025,
        "genre": "Test",
        "price": 1.00,
        "stock": 10 
    }
    r = requests.post(f"{CATALOG}/movies", json=new_movie_data, headers=headers_admin)
    if ok("CRUD M: Crear película 'Z Test Movie'", r.status_code == HTTPStatus.CREATED and r.json()):
        TEST_MOVIE_ID = r.json().get('movieid')
    

    r = requests.put(f"{CATALOG}/movies/{TEST_MOVIE_ID}", json={"price": 5.50, "genre": "Test Updated"}, headers=headers_admin)
    if ok("CRUD M: Actualizar precio y género", r.status_code == HTTPStatus.OK):
        r = requests.get(f"{CATALOG}/movies/{TEST_MOVIE_ID}", headers=headers_alice)
        ok("CRUD M: Verificar precio actualizado (5.5)", r.status_code == HTTPStatus.OK and float(r.json().get('price')) == 5.5)


    
    print("\n# =======================================================")
    print("# 2. Votaciones y Consultas Avanzadas (Top N)")
    print("# =======================================================")



    r = requests.post(f"{CATALOG}/movies/1/vote", json={"rating": 5}, headers=headers_alice)
    ok("Votos: Alice vota 5 a The Matrix (ID 1)", r.status_code == HTTPStatus.CREATED)
    


    r = requests.get(f"{CATALOG}/movies/1/rating", headers=headers_alice)
    if ok("Votos: Consultar media (ID 1)", r.status_code == HTTPStatus.OK and float(r.json().get('average_rating')) == 5.0):
        print(f"\tMedia The Matrix: {r.json().get('average_rating')} ({r.json().get('total_votes')} votos)")


    r = requests.post(f"{CATALOG}/movies/1/vote", json={"rating": 1}, headers=headers_alice)
    ok("Votos: Alice actualiza voto a 1", r.status_code == HTTPStatus.CREATED)
    

    r = requests.get(f"{CATALOG}/movies/1/rating", headers=headers_alice)
    ok("Votos: Verificar actualización de voto (media baja)", r.status_code == HTTPStatus.OK and float(r.json().get('average_rating')) < 5.0)

    
    r = requests.get(f"{CATALOG}/movies", params={"top_n": 3}, headers=headers_alice)
    if ok("Avanzadas: Obtener Top 3 películas más votadas", r.status_code == HTTPStatus.OK and len(r.json()) == 3):
        top_movies = r.json()
        ok(f"Avanzadas: Verificar que la película de prueba (ID {TEST_MOVIE_ID}) NO está en el Top 3", 
           all(movie['movieid'] != TEST_MOVIE_ID for movie in top_movies))

  
    
    print("\n# =======================================================")
    print("# Distintas consultas de alice al catálogo de películas")
    print("# =======================================================")
    

    r = requests.get(f"{CATALOG}/movies", headers=headers_alice)
    if ok("Obtener catálogo de películas completo", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for movie in data:

                print(f"\t- {movie['title']}\n\t  {movie['description']}")
        else:
            print("\tNo hay películas en el catálogo")
    
    
    r = requests.get(f"{CATALOG}/movies", params={"title": "matrix"}, headers=headers_alice)
    if ok("Buscar películas con 'matrix' en el título", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']}")

    r = requests.get(f"{CATALOG}/movies", params={"title": "No debe haber pelis con este título"}, headers=headers_alice)
    ok("Búsqueda fallida de películas por título", r.status_code == HTTPStatus.OK and not r.json())
    
    
    movieids = []
    r = requests.get(f"{CATALOG}/movies", params={"title": "Gladiator", "year": 2000, "genre": "action"}, headers=headers_alice)
    if ok("Buscar películas por varios campos de movie", r.status_code == HTTPStatus.OK):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']}")
                movieids.append(movie['movieid'])
            
            r = requests.get(f"{CATALOG}/movies/{movieids[0]}", headers=headers_alice)
            if ok(f"Obtener detalles de la película con ID [{movieids[0]}]", 
                  r.status_code == HTTPStatus.OK and r.json() and r.json()['movieid'] == movieids[0]):
                data = r.json()
                print(f"\t{data['title']} ({data['year']})")
                print(f"\tGénero: {movie['genre']}")
                print(f"\tDescripción: {movie['description']}")
                print(f"\tPrecio: {movie['price']}")
        else:
            print("\tNo se encontraron películas.")
    
    r = requests.get(f"{CATALOG}/movies/99999999", headers=headers_alice)
    ok(f"Obtener detalles de la película con ID no válido", r.status_code == HTTPStatus.NOT_FOUND)
    
    r = requests.get(f"{CATALOG}/movies", params={"actor": "Tom Hardy"}, headers=headers_alice)
    if ok("Buscar películas en las que participa 'Tom Hardy'", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        if data:
            for movie in data:
                print(f"\t[{movie['movieid']}] {movie['title']}")
                movieids.append(movie['movieid'])
    
    print("\n# =======================================================")
    print("# Gestión del carrito de alice (CON PRUEBAS P3: STOCK Y NUEVOS ENDPOINTS)")
    print("# =======================================================")

    stock_before = 0
    if movieids:
        r_stock = requests.get(f"{CATALOG}/movies/{movieids[0]}", headers=headers_alice)
        if r_stock.status_code == HTTPStatus.OK:
            stock_before = r_stock.json().get('stock', 0)

    for movieid in movieids:
        r = requests.put(f"{CATALOG}/cart/{movieid}", headers=headers_alice)
        if ok(f"Añadir película con ID [{movieid}] al carrito", r.status_code == HTTPStatus.OK):
            if movieid == movieids[0]:
                 r_stock_new = requests.get(f"{CATALOG}/movies/{movieid}", headers=headers_alice)
                 stock_after = r_stock_new.json().get('stock', 0)
                 ok(f"[P3 Trigger] Verificar stock reducido (Antes: {stock_before}, Después: {stock_after})", stock_after == stock_before - 1)

            r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
            if ok("Obtener carrito del usuario con el nuevo contenido", r.status_code == HTTPStatus.OK and r.json()):
                data = r.json()
                if data:
                    for movie in data:
                        print(f"\t[{movie['movieid']}] {movie['title']} - {movie['price']}")
            
    if movieids:
        r = requests.put(f"{CATALOG}/cart/{movieids[0]}", headers=headers_alice)
        ok(f"Añadir película con ID [{movieids[0]}] al carrito más de una vez", r.status_code == HTTPStatus.CONFLICT)

        r_stock_del = requests.get(f"{CATALOG}/movies/{movieids[-1]}", headers=headers_alice)
        stock_before_del = r_stock_del.json().get('stock', 0)

        r = requests.delete(f"{CATALOG}/cart/{movieids[-1]}", headers=headers_alice)
        if ok(f"Elimimar película con ID [{movieids[-1]}] del carrito", r.status_code == HTTPStatus.OK):
            
            r_stock_del_new = requests.get(f"{CATALOG}/movies/{movieids[-1]}", headers=headers_alice)
            stock_after_del = r_stock_del_new.json().get('stock', 0)
            ok(f"[P3 Trigger] Verificar stock repuesto al borrar (Antes: {stock_before_del}, Después: {stock_after_del})", stock_after_del == stock_before_del + 1)

            r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
            if ok(f"Obtener carrito del usuario sin la película [{movieids[-1]}]", r.status_code == HTTPStatus.OK):
                data = r.json()
                if data:
                    for movie in data:
                        print(f"\t[{movie['movieid']}] {movie['title']} - {movie['price']}")
                else:
                    print("\tEl carrito está vacío.")
    
    r = requests.get(f"{CATALOG}/clientesSinPedidos", headers=headers_alice)
    alice_found = False
    if r.status_code == HTTPStatus.OK:
        list_users = r.json().get("clientes_sin_compras", [])
        alice_found = any(u['username'] == 'alice' for u in list_users)
    ok("[P3 Endpoint] /clientesSinPedidos: Alice debe aparecer antes de comprar", alice_found)

    r = requests.post(f"{CATALOG}/cart/checkout", headers=headers_alice)
    ok("Checkout del carrito con saldo insuficiente", r.status_code == HTTPStatus.PAYMENT_REQUIRED) 

    r = requests.post(f"{CATALOG}/user/credit", json={"amount": 1200.75}, headers=headers_alice)
    if ok("Aumentar el saldo de alice", r.status_code == HTTPStatus.OK and r.json()):
        saldo = float(r.json()["new_credit"])
        print(f"\tSaldo actualizado a {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    r = requests.post(f"{CATALOG}/user/credit", json={"amount": 1000000}, headers=headers_alice)
    if ok("Aumentar el saldo de alice", r.status_code == HTTPStatus.OK and r.json()):
        saldo = float(r.json()["new_credit"])
        print(f"\tSaldo actualizado a {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    r = requests.post(f"{CATALOG}/cart/checkout", headers=headers_alice)
    if ok("Checkout del carrito", r.status_code == HTTPStatus.OK and r.json()):
        data = r.json()
        ORDER_ID = data['orderid'] 
        print(f"\tPedido {ORDER_ID} creado correctamente:")

        r = requests.get(f"{CATALOG}/orders/{ORDER_ID}", headers=headers_alice)
        if ok(f"Recuperar datos del pedido {ORDER_ID}", r.status_code == HTTPStatus.OK and r.json()):
            order = r.json()

            print(f"\tFecha: {order['date']}\n\tPrecio: {order['total_price']}")
            print("\tContenidos:")
            for movie in order['movies']:
                    print(f"\t- [{movie['movieid']}] {movie['title']} ({movie['price']})")
        
        r = requests.get(f"{CATALOG}/cart", headers=headers_alice)
        ok("Obtener carrito vacío después de la venta", r.status_code == HTTPStatus.OK and not r.json())
        
    current_year = datetime.now().year
    r = requests.get(f"{CATALOG}/estadisticaVentas/{current_year}/España", headers=headers_alice)
    sales_found = False
    if r.status_code == HTTPStatus.OK:
        sales = r.json().get("sales", [])
        sales_found = any(s['orderid'] == ORDER_ID for s in sales)
    ok(f"[P3 Endpoint] /estadisticaVentas: Verificar que aparece la venta {ORDER_ID} en {current_year}/España", sales_found)

    r = requests.get(f"{CATALOG}/clientesSinPedidos", headers=headers_alice)
    alice_gone = True
    if r.status_code == HTTPStatus.OK:
        list_users = r.json().get("clientes_sin_compras", [])
        alice_gone = not any(u['username'] == 'alice' for u in list_users)
    ok("[P3 Endpoint] /clientesSinPedidos: Alice NO debe aparecer después de comprar", alice_gone)

    
    print("\n# =======================================================")
    print("# 3. Limpieza de base de datos")
    print("# =======================================================")
    

    r = requests.delete(f"{CATALOG}/movies/{TEST_MOVIE_ID}", headers=headers_admin)
    ok(f"CRUD M: Borrar película de prueba ID [{TEST_MOVIE_ID}]", r.status_code == HTTPStatus.OK)
    
    r = requests.delete(f"{CATALOG}/actors/{TEST_ACTOR_ID}", headers=headers_admin)
    ok(f"CRUD A: Borrar actor de prueba ID [{TEST_ACTOR_ID}]", r.status_code == HTTPStatus.OK)
    

    print("\nPruebas completadas.")


    print("\n# =======================================================")
    print("# 4. Pruebas de Transacciones (Borrado de País)")
    print("# =======================================================")

    r = requests.put(f"{USERS}/user", json={"name": "pierre", "password": "secret"}, headers=headers_admin)
    if r.status_code == HTTPStatus.OK:
        uid_pierre = r.json()["uid"]
        token_pierre = r.json()["token"]
        h_pierre = {"Authorization": f"Bearer {token_pierre}"}
        
      
        
        requests.post(f"{CATALOG}/user/credit", json={"amount": 500}, headers=h_pierre)
        requests.put(f"{CATALOG}/cart/1", headers=h_pierre) 
        requests.post(f"{CATALOG}/movies/1/vote", json={"rating": 5}, headers=h_pierre) 
    
    target_country = "España" 

    r = requests.delete(f"{CATALOG}/borraPaisIncorrecto/{target_country}", headers=headers_admin)
    ok("Transacción: Borrado Incorrecto debe fallar (409)", r.status_code == HTTPStatus.CONFLICT)
    
    r = requests.get(f"{USERS}/user", json={"name": "pierre", "password": "secret"})
    ok("Transacción: Verificar que el usuario sigue existiendo tras Rollback", r.status_code == HTTPStatus.OK)

    r = requests.delete(f"{CATALOG}/borraPaisIntermedio/{target_country}", headers=headers_admin)
    ok("Transacción: Borrado Intermedio debe fallar parcialmente (409)", r.status_code == HTTPStatus.CONFLICT)

    r = requests.get(f"{CATALOG}/cart", headers=h_pierre)
    cart_empty = (r.status_code == HTTPStatus.OK and not r.json()) or (r.status_code == HTTPStatus.NOT_FOUND) 
    ok("Transacción: Verificar que el carrito SÍ se borró (Commit intermedio)", cart_empty)

    r = requests.delete(f"{CATALOG}/borraPais/{target_country}", headers=headers_admin)
    ok("Transacción: Borrado Correcto debe funcionar (200)", r.status_code == HTTPStatus.OK)

    r = requests.get(f"{USERS}/user", json={"name": "pierre", "password": "secret"})
    ok("Transacción: Verificar que el usuario ha sido eliminado", r.status_code == 401) 
if __name__ == "__main__":
    main()