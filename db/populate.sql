INSERT INTO users (username, password_hash, userrole, balance) VALUES
(
    'admin',
    '$2b$12$7eR.x/CGUxwDdQLF3nbG/eRnIa5Oz0R3snsC8e2dyIMusZ0mFNApK',
    'admin',
    9999.00
),
(
    'bob',
    '$2b$12$f9gfdL1M6IMYtV/ipGeG.OyoyR9uGwgvB8BKx7ok6YWeqoVK2yf9m',
    'user',
    50.00
);


INSERT INTO actors (actorname) VALUES
('Keanu Reeves'),
('Laurence Fishburne'),
('Carrie-Anne Moss'),
('Russell Crowe'),
('Joaquin Phoenix'),
('Tom Hardy'),
('Leonardo DiCaprio'),
('Cillian Murphy');


INSERT INTO movies (title, moviedescription, movieyear, genre, price) VALUES
(
    'The Matrix',
    'Un programador descubre que la realidad es una simulación.',
    1999,
    'sci-fi',
    9.99
),
(
    'Gladiator',
    'Un general romano traicionado busca venganza.',
    2000,
    'action',
    12.50
),
(
    'Inception',
    'Un ladrón que roba información entrando en los sueños.',
    2010,
    'sci-fi',
    11.00
),
(
    'The Dark Knight Rises',
    'Batman se enfrenta a Bane.',
    2012,
    'action',
    10.50
),
(
    'Oppenheimer',
    'La historia del creador de la bomba atómica.',
    2023,
    'drama',
    19.99
),
(
    'The Matrix Reloaded',
    'Neo continúa su lucha contra las máquinas.',
    2003,
    'sci-fi',
    8.99
);


INSERT INTO movie_actors (movieid, actorid) VALUES
(1, 1), 
(1, 2), 
(1, 3), 
(2, 4), 
(2, 5), 
(3, 7), 
(3, 6),
(3, 8),
(4, 6), 
(5, 8), 
(6, 1), 
(6, 2); 


INSERT INTO movie_votes (userid, movieid, rating) VALUES
(1, 1, 5),
(2, 1, 5),
(2, 2, 4),
(2, 3, 4),
(1, 5, 3);


INSERT INTO cart_items (userid, movieid) VALUES
(2, 5); 


INSERT INTO orders (userid, total_price, order_date) VALUES
(2, 22.49, '2025-09-15 14:30:00Z'); 


INSERT INTO order_items (orderid, movieid, price_at_purchase) VALUES
(1, 1, 9.99),  
(1, 2, 12.50); 
