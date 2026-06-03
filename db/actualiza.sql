---CREACION DE COLUMNAS Y ACTUALIZACION DE LAS MISMAS---
ALTER TABLE movies ADD COLUMN stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0);
ALTER TABLE movies ADD COLUMN average_rating NUMERIC(3, 2) DEFAULT 0.00;
-- Añadimos un stock inicial de 100 a cada producto
UPDATE movies SET stock = 100; 
-- Actualizamos la media de votos para peliculas antiguas ya votadas antes de este campo
UPDATE movies m SET average_rating = (
    SELECT COALESCE(AVG(rating), 0) 
    FROM movie_votes v 
    WHERE v.movieid = m.movieid
);

-- Se añaden columnas a las tablas
ALTER TABLE users ADD COLUMN cart_total NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (cart_total >= 0);
ALTER TABLE users ADD COLUMN nationality VARCHAR(100) NOT NULL DEFAULT 'España';
ALTER TABLE users ADD COLUMN discount NUMERIC(5, 2) NOT NULL DEFAULT 0.00 CHECK (discount >= 0 AND discount <= 100);
ALTER TABLE orders ADD COLUMN payment_date TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp;


---CREACION DE TRIGGERS---
-- (1)Creamos una funcion para el trigger pedido
CREATE OR REPLACE FUNCTION gestionStockCarrito()
RETURNS TRIGGER AS $$ 
DECLARE
    precio_peli movies.price%type; 
BEGIN
    IF(TG_OP = 'INSERT') THEN 
        SELECT price INTO precio_peli FROM movies WHERE movieid = NEW.movieid;
        UPDATE movies SET stock = stock - 1 WHERE movieid = NEW.movieid;
        UPDATE users SET cart_total = cart_total + precio_peli WHERE userid = NEW.userid;
        RETURN NEW; 
    ELSIF(TG_OP = 'DELETE') THEN 
        SELECT price INTO precio_peli FROM movies WHERE movieid = OLD.movieid;
        UPDATE movies SET stock = stock + 1 WHERE movieid = OLD.movieid;        
        UPDATE users 
        SET cart_total = GREATEST(0, cart_total - precio_peli) 
        WHERE userid = OLD.userid;
        
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
-- (1)Creamos el trigger
CREATE TRIGGER actualizarCarrito
AFTER INSERT OR DELETE ON cart_items
FOR EACH ROW EXECUTE FUNCTION gestionStockCarrito();





-- (2)Creamos una funcion para el trigger pedido
CREATE OR REPLACE FUNCTION cobrar_pedido()
RETURNS TRIGGER AS $$
DECLARE
    saldo_actual users.balance%type;
    descuento_user users.discount%type;
    precio_final NUMERIC(10, 2);
BEGIN
    SELECT balance, discount INTO saldo_actual, descuento_user FROM users WHERE userid = NEW.userid;
    
    precio_final := NEW.total_price * (1 - (descuento_user / 100.0));
    NEW.total_price := precio_final;

    IF (saldo_actual < precio_final) THEN
        RAISE EXCEPTION 'Pago rechazado: Saldo insuficiente';
    END IF;


    UPDATE users SET balance = balance - precio_final WHERE userid = NEW.userid;
    PERFORM pg_sleep(15);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- (2)Creamos el trigger
CREATE TRIGGER tr_cobrar_pedido
BEFORE INSERT ON orders
FOR EACH ROW EXECUTE FUNCTION cobrar_pedido();




-- (3)Creamos una funcion para el trigger pedido
CREATE OR REPLACE FUNCTION actualizar_valoracion_global()
RETURNS TRIGGER AS $$
DECLARE
    id_pelicula_afectada movies.movieid%type;
BEGIN
    IF (TG_OP = 'DELETE') THEN id_pelicula_afectada := OLD.movieid;
    ELSE id_pelicula_afectada := NEW.movieid; END IF;

    UPDATE movies 
    SET average_rating = (SELECT COALESCE(AVG(rating), 0) FROM movie_votes WHERE movieid = id_pelicula_afectada)
    WHERE movieid = id_pelicula_afectada;

    IF (TG_OP = 'DELETE') THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- (3)Creamos el trigger
CREATE TRIGGER valoracion_automatica
AFTER INSERT OR UPDATE OR DELETE ON movie_votes
FOR EACH ROW EXECUTE FUNCTION actualizar_valoracion_global();



---CREACION DE PROCEDIMIENTO--
CREATE OR REPLACE PROCEDURE calcular_media_pelicula(p_movieid INTEGER, INOUT media_final NUMERIC)
LANGUAGE plpgsql AS $$
BEGIN
    SELECT COALESCE(AVG(rating), 0) INTO media_final FROM movie_votes WHERE movieid = p_movieid;
END;
$$;