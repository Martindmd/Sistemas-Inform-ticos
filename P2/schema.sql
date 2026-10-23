
-- Creación de tablas

CREATE TABLE Usuario (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    pais VARCHAR(100) NOT NULL,
    saldo NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (saldo >= 0),
    -- Contador de sesión: forma parte del token y se incrementa en el logout para invalidarlo
    sesion INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE Director (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE Actor (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE Pelicula (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    anio INTEGER NOT NULL,
    genero VARCHAR(50) NOT NULL,
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    director_id INTEGER NOT NULL REFERENCES Director(id),
    -- Borrado lógico: una película borrada deja de estar en el catálogo pero se conservan sus ventas
    activa BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE Pedido (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES Usuario(id) ON DELETE CASCADE,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'pagado')),
    fecha_pago TIMESTAMP,
    total NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    CHECK (
        (estado = 'pendiente' AND fecha_pago IS NULL)
        OR (estado = 'pagado' AND fecha_pago IS NOT NULL)
    )
);

-- Cada usuario solo puede tener un carrito (pedido pendiente) a la vez
CREATE UNIQUE INDEX un_carrito_por_usuario ON Pedido (usuario_id) WHERE estado = 'pendiente';

CREATE TABLE PedidoPelicula (
    pedido_id INTEGER NOT NULL REFERENCES Pedido(id) ON DELETE CASCADE,
    pelicula_id INTEGER NOT NULL REFERENCES Pelicula(id),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    -- Precio de la película en el momento de añadirla al carrito
    precio_unitario NUMERIC(10, 2) NOT NULL CHECK (precio_unitario >= 0),
    PRIMARY KEY (pedido_id, pelicula_id)
);

CREATE TABLE PeliculaActor (
    pelicula_id INTEGER NOT NULL REFERENCES Pelicula(id),
    actor_id INTEGER NOT NULL REFERENCES Actor(id),
    PRIMARY KEY (pelicula_id, actor_id)
);

CREATE TABLE Valoracion (
    usuario_id INTEGER NOT NULL REFERENCES Usuario(id) ON DELETE CASCADE,
    pelicula_id INTEGER NOT NULL REFERENCES Pelicula(id),
    puntuacion INTEGER NOT NULL CHECK (puntuacion BETWEEN 0 AND 10),
    PRIMARY KEY (usuario_id, pelicula_id)
);


-- Triggers 

CREATE FUNCTION actualizar_carrito()
RETURNS TRIGGER AS $$
DECLARE
    estado_pedido VARCHAR(20);
    id_pedido INTEGER;
BEGIN
    -- Obtener el pedido afectado
    IF TG_OP = 'DELETE' THEN
        id_pedido := OLD.pedido_id;
    ELSE
        id_pedido := NEW.pedido_id;
    END IF;

    -- Comprobar que el pedido está pendiente
    SELECT estado INTO estado_pedido
    FROM Pedido
    WHERE id = id_pedido
    FOR UPDATE; -- Bloquear la fila del pedido para evitar condiciones de carrera

    -- El pedido ya no existe (borrado en cascada al borrar el usuario): no se toca el stock
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    IF estado_pedido <> 'pendiente' THEN
        RAISE EXCEPTION 'No se puede modificar un pedido pagado';
    END IF;

    IF TG_OP = 'INSERT' THEN

        -- Restar stock al añadir una película
        UPDATE Pelicula
        SET stock = stock - NEW.cantidad
        WHERE id = NEW.pelicula_id
          AND stock >= NEW.cantidad;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Stock insuficiente';
        END IF;

    ELSIF TG_OP = 'UPDATE' THEN

        -- No permitir cambiar los identificadores
        IF NEW.pelicula_id <> OLD.pelicula_id
           OR NEW.pedido_id <> OLD.pedido_id THEN
            RAISE EXCEPTION 'No se puede cambiar la película o el pedido';
        END IF;

        -- Ajustar el stock según el cambio de cantidad
        UPDATE Pelicula
        SET stock = stock + OLD.cantidad - NEW.cantidad
        WHERE id = NEW.pelicula_id
          AND stock + OLD.cantidad >= NEW.cantidad;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Stock insuficiente';
        END IF;

    ELSIF TG_OP = 'DELETE' THEN

        -- Devolver las unidades al stock
        UPDATE Pelicula
        SET stock = stock + OLD.cantidad
        WHERE id = OLD.pelicula_id;

    END IF;

    -- Recalcular el precio total del pedido con el precio guardado al añadir cada película
    UPDATE Pedido
    SET total = (
        SELECT COALESCE(SUM(cantidad * precio_unitario), 0)
        FROM PedidoPelicula
        WHERE pedido_id = id_pedido
    )
    WHERE id = id_pedido;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER actualizar_carrito_trigger
AFTER INSERT OR UPDATE OR DELETE ON PedidoPelicula
FOR EACH ROW
EXECUTE FUNCTION actualizar_carrito();



CREATE FUNCTION actualizar_saldo()
RETURNS TRIGGER AS $$
BEGIN
    -- Impedir modificar un pedido ya pagado
    IF OLD.estado = 'pagado' THEN
        RAISE EXCEPTION 'No se puede modificar un pedido pagado';
    END IF;

    -- Impedir cambiar el propietario o el total al pagar
    IF NEW.estado = 'pagado' AND
       (NEW.usuario_id <> OLD.usuario_id OR NEW.total <> OLD.total) THEN
        RAISE EXCEPTION 'No se puede modificar el usuario o el total al pagar';
    END IF;

    -- Comprobar si el pedido acaba de pagarse
    IF NEW.estado = 'pagado' AND OLD.estado = 'pendiente' THEN

        -- No se puede pagar un carrito vacío
        IF NOT EXISTS (SELECT 1 FROM PedidoPelicula WHERE pedido_id = NEW.id) THEN
            RAISE EXCEPTION 'El carrito está vacío';
        END IF;

        -- Descontar el dinero al usuario
        UPDATE Usuario
        SET saldo = saldo - NEW.total
        WHERE id = NEW.usuario_id
          AND saldo >= NEW.total;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Saldo insuficiente';
        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER actualizar_saldo_trigger
AFTER UPDATE ON Pedido
FOR EACH ROW
EXECUTE FUNCTION actualizar_saldo();

-- Stored procedures

CREATE FUNCTION obtener_media_pelicula(p_id INTEGER)
RETURNS NUMERIC AS $$
DECLARE
    media NUMERIC;
BEGIN
    SELECT ROUND(AVG(puntuacion), 2)
    INTO media
    FROM Valoracion 
    WHERE pelicula_id = p_id;
    RETURN media;
END;
$$ LANGUAGE plpgsql;


-- Crear una película con su director y actores (por nombre; los que no existan se crean)
CREATE FUNCTION crear_pelicula(p_titulo VARCHAR, p_anio INTEGER, p_genero VARCHAR, p_precio NUMERIC,
                               p_stock INTEGER, p_director VARCHAR, p_actores VARCHAR[])
RETURNS INTEGER AS $$
DECLARE
    v_director INTEGER;
    v_pelicula INTEGER;
    v_actor INTEGER;
    v_nombre VARCHAR;
BEGIN
    -- Buscar el director o crearlo
    SELECT id INTO v_director FROM Director WHERE nombre = p_director;

    IF NOT FOUND THEN
        INSERT INTO Director (nombre) VALUES (p_director)
        RETURNING id INTO v_director;
    END IF;

    INSERT INTO Pelicula (titulo, anio, genero, precio, stock, director_id)
    VALUES (p_titulo, p_anio, p_genero, p_precio, p_stock, v_director)
    RETURNING id INTO v_pelicula;

    -- Lo mismo con cada actor, y se relaciona con la película
    FOREACH v_nombre IN ARRAY p_actores LOOP
        SELECT id INTO v_actor FROM Actor WHERE nombre = v_nombre;

        IF NOT FOUND THEN
            INSERT INTO Actor (nombre) VALUES (v_nombre)
            RETURNING id INTO v_actor;
        END IF;

        INSERT INTO PeliculaActor (pelicula_id, actor_id) VALUES (v_pelicula, v_actor)
        ON CONFLICT DO NOTHING;
    END LOOP;

    RETURN v_pelicula;
END;
$$ LANGUAGE plpgsql;


-- Listado de películas del catálogo filtrando por género, director y/o actor (NULL = sin filtro)
CREATE FUNCTION buscar_peliculas(p_genero VARCHAR, p_director VARCHAR, p_actor VARCHAR)
RETURNS TABLE (id INTEGER, titulo VARCHAR, anio INTEGER, genero VARCHAR,
               precio NUMERIC, stock INTEGER, director VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.titulo, p.anio, p.genero, p.precio, p.stock, d.nombre
    FROM Pelicula p
    JOIN Director d ON d.id = p.director_id
    WHERE p.activa
      AND (p_genero IS NULL OR p.genero ILIKE p_genero) -- ILIKE para que sea case-insensitive
      AND (p_director IS NULL OR d.nombre ILIKE '%' || p_director || '%') -- ILIKE con comodines para buscar coincidencias parciales
      AND (p_actor IS NULL OR EXISTS (
            SELECT 1
            FROM PeliculaActor pa
            JOIN Actor a ON a.id = pa.actor_id
            WHERE pa.pelicula_id = p.id
              AND a.nombre ILIKE '%' || p_actor || '%'
          ))
    ORDER BY p.titulo;
END;
$$ LANGUAGE plpgsql;


-- Añadir unidades de una película al carrito del usuario (si no tiene carrito se le crea)
CREATE PROCEDURE anadir_al_carrito(p_usuario INTEGER, p_pelicula INTEGER, p_cantidad INTEGER)
AS $$
DECLARE
    v_pedido INTEGER;
    v_precio NUMERIC(10, 2);
BEGIN
    -- Precio actual de la película (solo si sigue en el catálogo)
    SELECT precio INTO v_precio
    FROM Pelicula
    WHERE id = p_pelicula AND activa;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Película no disponible';
    END IF;

    -- Buscar el carrito del usuario o crearlo
    SELECT id INTO v_pedido
    FROM Pedido
    WHERE usuario_id = p_usuario AND estado = 'pendiente';

    IF NOT FOUND THEN
        INSERT INTO Pedido (usuario_id) VALUES (p_usuario)
        RETURNING id INTO v_pedido;
    END IF;

    -- Añadir la película, o sumar unidades si ya estaba (se mantiene el precio con el que se añadió)
    -- El trigger actualizar_carrito se encarga del stock y del total
    INSERT INTO PedidoPelicula (pedido_id, pelicula_id, cantidad, precio_unitario)
    VALUES (v_pedido, p_pelicula, p_cantidad, v_precio)
    ON CONFLICT (pedido_id, pelicula_id)
    DO UPDATE SET cantidad = PedidoPelicula.cantidad + EXCLUDED.cantidad;
END;
$$ LANGUAGE plpgsql;


-- Pagar el carrito del usuario guardando la fecha de pago
-- El trigger actualizar_saldo descuenta el total del saldo
CREATE PROCEDURE pagar_carrito(p_usuario INTEGER)
AS $$
BEGIN
    UPDATE Pedido
    SET estado = 'pagado', fecha_pago = NOW()
    WHERE usuario_id = p_usuario AND estado = 'pendiente';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario no tiene carrito';
    END IF;
END;
$$ LANGUAGE plpgsql;


-- Borrar un usuario devolviendo al stock lo que tuviera en el carrito
CREATE PROCEDURE borrar_usuario(p_usuario INTEGER)
AS $$
BEGIN
    -- Vaciar el carrito: el trigger actualizar_carrito repone el stock
    DELETE FROM PedidoPelicula
    WHERE pedido_id IN (
        SELECT id FROM Pedido
        WHERE usuario_id = p_usuario AND estado = 'pendiente'
    );

    -- Sus pedidos y valoraciones se borran en cascada
    DELETE FROM Usuario WHERE id = p_usuario;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Usuario no encontrado';
    END IF;
END;
$$ LANGUAGE plpgsql;
