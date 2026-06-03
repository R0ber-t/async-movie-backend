-- CATALOGO DE PELICULAS
CREATE TABLE movies (
    movieid SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    moviedescription varchar(255),
    movieyear INTEGER,
    genre VARCHAR(100),
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0.00),
    CONSTRAINT price_positive CHECK (price >= 0)
);

-- LISTA DE ACTORES
CREATE TABLE actors (
    actorid SERIAL PRIMARY KEY,
    actorname VARCHAR(255) NOT NULL
);

-- RELACION PELICULA/ACTORES
CREATE TABLE movie_actors (
    movieid INTEGER NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
    actorid INTEGER NOT NULL REFERENCES actors(actorid) ON DELETE CASCADE,
    PRIMARY KEY (movieid, actorid)
);

-- USUARIOS REGISTRADOS
CREATE TABLE users(
    userid SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    userrole VARCHAR(50) NOT NULL CHECK (userrole IN ('admin', 'user')),
    balance NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0)
);

-- CARRITO DE COMPRAS DEL USUARIO
CREATE TABLE cart_items (
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE RESTRICT,
    movieid INTEGER NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
    PRIMARY KEY (userid, movieid)
);

-- PEDIDOS REALIZADOS
CREATE TABLE orders (
    orderid SERIAL PRIMARY KEY,
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE RESTRICT,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    total_price NUMERIC(10, 2) NOT NULL
);

-- PELICULAS DENTRO DE CADA PEDIDO
CREATE TABLE order_items (
    orderid INTEGER NOT NULL REFERENCES orders(orderid) ON DELETE RESTRICT,
    movieid INTEGER NOT NULL REFERENCES movies(movieid) ON DELETE RESTRICT,
    price_at_purchase NUMERIC(5, 2) NOT NULL,
    PRIMARY KEY (orderid, movieid)
);

-- CALIFICACIONES DE CADA USUARIO
CREATE TABLE movie_votes (
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE RESTRICT,
    movieid INTEGER NOT NULL REFERENCES movies(movieid) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    PRIMARY KEY (userid, movieid)
);