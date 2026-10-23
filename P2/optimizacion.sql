-- Optimización de la consulta de /ventas/<año>/<país>
-- Ejecutar una sola vez con la base de datos recién creada:
--   docker compose exec -T db psql -U alumnodb -d si1 < optimizacion.sql


-- 1. Datos de prueba
-- Con los pocos datos de populate.sql cualquier consulta es instantánea y Postgres siempre recorre
-- las tablas enteras, así que se generan 20.000 usuarios de 10 países y 5 pedidos pagados por usuario
-- con fechas entre 2020 y 2026 (unos 100.000 pedidos).
-- Los pedidos se insertan ya pagados: solo sirven para medir la consulta, no pasan por el carrito.

INSERT INTO Usuario (nombre, password_hash, pais, saldo)
SELECT 'usuario_' || i, 'sin_password',
       (ARRAY['España', 'Francia', 'Portugal', 'Italia', 'Alemania',
              'Reino Unido', 'Grecia', 'Irlanda', 'Bélgica', 'Suiza'])[1 + i % 10],
       0
FROM generate_series(1, 20000) AS i;

INSERT INTO Pedido (usuario_id, estado, fecha_pago, total)
SELECT u.id, 'pagado',
       TIMESTAMP '2020-01-01' + random() * INTERVAL '7 years',
       ROUND((random() * 50)::NUMERIC, 2)
FROM Usuario u, generate_series(1, 5);

-- Actualizar las estadísticas que usa Postgres para decidir el plan de ejecución
ANALYZE;


-- 2. Plan de ejecución SIN optimizar (la misma consulta que api.py)

EXPLAIN ANALYZE
SELECT pe.id AS pedido_id, u.nombre AS usuario, pe.fecha_pago, pe.total
FROM Pedido pe
JOIN Usuario u ON u.id = pe.usuario_id
WHERE pe.estado = 'pagado'
AND u.pais = 'Francia'
AND EXTRACT(YEAR FROM pe.fecha_pago) = 2026
ORDER BY pe.fecha_pago;


-- 3. Primera estrategia: índice normal sobre Pedido(fecha_pago)
-- NO se usa: la consulta no busca por fecha_pago sino por EXTRACT(YEAR FROM fecha_pago),
-- y el índice guarda fechas, no años

CREATE INDEX idx_pedido_fecha ON Pedido (fecha_pago);
ANALYZE;

EXPLAIN ANALYZE
SELECT pe.id AS pedido_id, u.nombre AS usuario, pe.fecha_pago, pe.total
FROM Pedido pe
JOIN Usuario u ON u.id = pe.usuario_id
WHERE pe.estado = 'pagado'
AND u.pais = 'Francia'
AND EXTRACT(YEAR FROM pe.fecha_pago) = 2026
ORDER BY pe.fecha_pago;

-- Como no aporta nada se elimina (cada índice ocupa espacio y ralentiza los INSERT y UPDATE)
DROP INDEX idx_pedido_fecha;


-- 4. Segunda estrategia (la elegida): índice de expresión sobre el año de fecha_pago
-- El índice guarda directamente EXTRACT(YEAR FROM fecha_pago), que es justo lo que busca la consulta,
-- así que se usa sin cambiar nada en la API. Además Postgres pasa a estimar bien cuántas filas hay.

CREATE INDEX idx_pedido_anio ON Pedido ((EXTRACT(YEAR FROM fecha_pago)));
ANALYZE;

EXPLAIN ANALYZE
SELECT pe.id AS pedido_id, u.nombre AS usuario, pe.fecha_pago, pe.total
FROM Pedido pe
JOIN Usuario u ON u.id = pe.usuario_id
WHERE pe.estado = 'pagado'
AND u.pais = 'Francia'
AND EXTRACT(YEAR FROM pe.fecha_pago) = 2026
ORDER BY pe.fecha_pago;
