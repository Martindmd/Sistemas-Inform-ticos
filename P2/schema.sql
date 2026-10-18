
-- Creación de tablas

CREATE TABLE Usuario (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    pais VARCHAR(100) NOT NULL,
    saldo NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (saldo >= 0)
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
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    director_id INTEGER NOT NULL REFERENCES Director(id)
);

CREATE TABLE Pedido (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES Usuario(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'pagado')),
    fecha_pago TIMESTAMP,
    total NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    CHECK (
        (estado = 'pendiente' AND fecha_pago IS NULL)
        OR (estado = 'pagado' AND fecha_pago IS NOT NULL)
    )
);

CREATE TABLE PedidoPelicula (
    pedido_id INTEGER NOT NULL REFERENCES Pedido(id),
    pelicula_id INTEGER NOT NULL REFERENCES Pelicula(id),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    PRIMARY KEY (pedido_id, pelicula_id)
);

CREATE TABLE PeliculaActor (
    pelicula_id INTEGER NOT NULL REFERENCES Pelicula(id),
    actor_id INTEGER NOT NULL REFERENCES Actor(id),
    PRIMARY KEY (pelicula_id, actor_id)
);

CREATE TABLE Valoracion (
    usuario_id INTEGER NOT NULL REFERENCES Usuario(id),
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

    -- Recalcular el precio total del pedido
    UPDATE Pedido
    SET total = (
        SELECT COALESCE(SUM(pp.cantidad * p.precio), 0)
        FROM PedidoPelicula pp
        JOIN Pelicula p ON pp.pelicula_id = p.id
        WHERE pp.pedido_id = id_pedido
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