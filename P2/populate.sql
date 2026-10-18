
-- Usuarios (contraseña de prueba: 1234, hash SHA-256)
INSERT INTO Usuario (nombre, password_hash, pais, saldo) VALUES
('Taha',   '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'España', 50.00),
('Ana',    '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Francia', 30.00),
('Martin', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'España', 40.00),
('Andres', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Portugal', 25.00);

-- Directores
INSERT INTO Director (nombre) VALUES
('Peter Jackson'),
('Sam Raimi'),
('Chris Columbus'),
('Keiichiro Saito'),
('Shunsuke Nakashige');

-- Películas
INSERT INTO Pelicula (titulo, precio, stock, director_id) VALUES
('El señor de los anillos', 12.00, 5, 1),
('Spiderman', 10.00, 6, 2),
('Harry Potter', 9.00, 4, 3),
('Frieren', 8.00, 5, 4),
('Solo Leveling', 7.00, 7, 5);

-- Actores
INSERT INTO Actor (nombre) VALUES
('Elijah Wood'),
('Tobey Maguire'),
('Daniel Radcliffe'),
('Yui Ishikawa'),
('Taito Ban');

-- Relaciones entre películas y actores
INSERT INTO PeliculaActor (pelicula_id, actor_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4),
(5, 5);

-- Valoraciones
INSERT INTO Valoracion (usuario_id, pelicula_id, puntuacion) VALUES
(1, 1, 9),
(2, 1, 8),
(3, 2, 7),
(4, 4, 10),
(1, 5, 8);

-- Los pedidos se crearán después mediante la API.
