
-- Usuarios (contraseña de prueba: 1234, hash SHA-256)
INSERT INTO Usuario (nombre, password_hash, pais, saldo) VALUES
('Taha',   '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'España', 80.00),
('Ana',    '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Francia', 60.00),
('Martin', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'España', 70.00),
('Andres', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Portugal', 40.00),
('Lucia',  '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'España', 50.00),
('Pierre', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Francia', 90.00),
('Claire', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Francia', 45.00),
('Joao',   '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Portugal', 60.00),
('Giulia', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Italia', 55.00),
('Marco',  '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Italia', 35.00);

-- Directores
INSERT INTO Director (nombre) VALUES
('Peter Jackson'),
('Sam Raimi'),
('Chris Columbus'),
('Keiichiro Saito'),
('Shunsuke Nakashige'),
('Christopher Nolan'),
('Hayao Miyazaki');

-- Películas
INSERT INTO Pelicula (titulo, anio, genero, precio, stock, director_id) VALUES
('El señor de los anillos', 2001, 'Fantasía', 12.00, 10, 1),
('Spiderman', 2002, 'Acción', 10.00, 10, 2),
('Harry Potter', 2001, 'Fantasía', 9.00, 8, 3),
('Frieren', 2023, 'Anime', 8.00, 10, 4),
('Solo Leveling', 2024, 'Anime', 7.00, 10, 5),
('Origen', 2010, 'Ciencia ficción', 11.00, 6, 6),
('Interstellar', 2014, 'Ciencia ficción', 11.00, 8, 6),
('El viaje de Chihiro', 2001, 'Anime', 9.00, 6, 7),
('El caballero oscuro', 2008, 'Acción', 10.00, 7, 6),
('Mi vecino Totoro', 1988, 'Anime', 8.00, 0, 7);

-- Actores
INSERT INTO Actor (nombre) VALUES
('Elijah Wood'),
('Tobey Maguire'),
('Daniel Radcliffe'),
('Yui Ishikawa'),
('Taito Ban'),
('Leonardo DiCaprio'),
('Matthew McConaughey'),
('Christian Bale'),
('Michael Caine'),
('Rumi Hiiragi');

-- Relaciones entre películas y actores
INSERT INTO PeliculaActor (pelicula_id, actor_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4),
(5, 5),
(6, 6),
(6, 9),
(7, 7),
(7, 9),
(8, 10),
(9, 8),
(9, 9);

-- Valoraciones
INSERT INTO Valoracion (usuario_id, pelicula_id, puntuacion) VALUES
(1, 1, 9),
(2, 1, 8),
(3, 2, 7),
(4, 4, 10),
(1, 5, 8),
(6, 7, 10),
(6, 6, 9),
(7, 3, 6),
(9, 7, 8),
(9, 8, 9),
(10, 9, 7),
(8, 1, 5);

-- Pedidos pagados: se usa el procedimiento del carrito y se paga con una fecha concreta
-- para tener ventas de distintos años y países (los triggers ajustan stock, total y saldo)
CALL anadir_al_carrito(2, 1, 1);
CALL anadir_al_carrito(2, 4, 2);
UPDATE Pedido SET estado = 'pagado', fecha_pago = '2026-02-14 18:30' WHERE usuario_id = 2 AND estado = 'pendiente';

CALL anadir_al_carrito(6, 7, 1);
CALL anadir_al_carrito(6, 6, 1);
UPDATE Pedido SET estado = 'pagado', fecha_pago = '2026-05-03 21:10' WHERE usuario_id = 6 AND estado = 'pendiente';

CALL anadir_al_carrito(6, 8, 2);
UPDATE Pedido SET estado = 'pagado', fecha_pago = '2025-11-20 17:45' WHERE usuario_id = 6 AND estado = 'pendiente';

CALL anadir_al_carrito(7, 3, 1);
UPDATE Pedido SET estado = 'pagado', fecha_pago = '2025-06-10 12:00' WHERE usuario_id = 7 AND estado = 'pendiente';

CALL anadir_al_carrito(1, 2, 1);
CALL anadir_al_carrito(1, 9, 1);
UPDATE Pedido SET estado = 'pagado', fecha_pago = '2026-03-01 20:15' WHERE usuario_id = 1 AND estado = 'pendiente';

CALL anadir_al_carrito(3, 5, 3);
UPDATE Pedido SET estado = 'pagado', fecha_pago = '2025-12-24 10:30' WHERE usuario_id = 3 AND estado = 'pendiente';

CALL anadir_al_carrito(4, 1, 1);
UPDATE Pedido SET estado = 'pagado', fecha_pago = '2026-04-15 19:00' WHERE usuario_id = 4 AND estado = 'pendiente';

CALL anadir_al_carrito(9, 7, 1);
CALL anadir_al_carrito(9, 8, 1);
UPDATE Pedido SET estado = 'pagado', fecha_pago = '2026-07-08 16:20' WHERE usuario_id = 9 AND estado = 'pendiente';

-- Un carrito sin pagar
CALL anadir_al_carrito(5, 4, 1);
