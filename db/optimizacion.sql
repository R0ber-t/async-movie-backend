-- Se hace un DROP para asegurar que la prueba inicial se hace desde 0 sin tener indices
DROP INDEX IF EXISTS idx_users_nationality;
DROP INDEX IF EXISTS idx_orders_year;
-- EXPLAIN se usa para visualizar al estrategia de optimizacion
-- Ejecutamos una consulta antes de optimizar para ver el antes
EXPLAIN SELECT o.orderid, o.order_date, o.total_price, u.username, u.nationality
FROM orders o
JOIN users u ON o.userid = u.userid
WHERE u.nationality = 'España'
AND EXTRACT(YEAR FROM o.order_date) = 2023;
-- Se crean índices para agilizar la búsqueda
CREATE INDEX idx_users_nationality ON users(nationality);
CREATE INDEX idx_orders_year ON orders ((EXTRACT(YEAR FROM order_date AT TIME ZONE 'UTC')));
-- Ejecutamos la misma consulta para probar la optimización una vez usados los índices
EXPLAIN SELECT o.orderid, o.order_date, o.total_price, u.username, u.nationality
FROM orders o
JOIN users u ON o.userid = u.userid
WHERE u.nationality = 'España'
AND EXTRACT(YEAR FROM o.order_date) = 2023;