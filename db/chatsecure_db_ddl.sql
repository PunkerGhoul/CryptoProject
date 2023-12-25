CREATE DATABASE IF NOT EXISTS chatsecure_db;

USE chatsecure_db;

CREATE TABLE usuarios (
  id_usuario INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  nombres VARCHAR(40) NOT NULL,
  apellidos VARCHAR(40) NOT NULL,
  correo VARCHAR(40) NOT NULL,
  contrasena VARCHAR(60) NOT NULL
);

CREATE TABLE conversaciones (
  id_conversacion INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  p INT NOT NULL,
  k INT NOT NULL,
  A INT NOT NULL,
  B INT NOT NULL,
  id_usuario1 INT NOT NULL,
  id_usuario2 INT NOT NULL,
  FOREIGN KEY (id_usuario1) REFERENCES usuarios(id_usuario),
  FOREIGN KEY (id_usuario2) REFERENCES usuarios(id_usuario)
);

CREATE TABLE mensajes (
  id_mensaje INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  mensaje TEXT NOT NULL,
  id_conversacion INT NOT NULL,
  FOREIGN KEY (id_conversacion) REFERENCES conversaciones(id_conversacion)
);

-- ALTER TABLE nombre_tabla AUTO_INCREMENT = 1;