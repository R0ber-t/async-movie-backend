# Async Movie Backend

Backend de microservicios y API REST asíncrona desarrollado para la gestión de un catálogo de películas, carritos de compra y procesamiento de pedidos. El sistema está contenerizado con Docker y utiliza PostgreSQL como motor principal, delegando gran parte de la lógica de negocio y control de concurrencia directamente a la base de datos.

## Stack Tecnológico

* **Python & Quart:** Implementación de la API con soporte nativo para asincronía.
* **PostgreSQL 15:** Motor de base de datos relacional.
* **PL/pgSQL:** Desarrollo de funciones, procedimientos almacenados y triggers.
* **SQLAlchemy:** Uso mixto del ORM para mapeo de entidades simples y Core para la ejecución de consultas y control fino de transacciones.
* **Docker & Docker-Compose:** Orquestación y despliegue del entorno.

## Arquitectura y Decisiones de Diseño

El enfoque principal de este desarrollo ha sido garantizar la consistencia de los datos y el manejo seguro de la concurrencia a nivel de base de datos:

* **Lógica Transaccional en BBDD:** Se han implementado triggers (ej. `gestionStockCarrito`) para automatizar las actualizaciones de stock y recalcular el importe total del carrito en tiempo real, evitando condiciones de carrera en el servidor web.
* **Control de Transacciones y Rollbacks:** Manejo explícito de bloques transaccionales desde la API. En operaciones críticas (como borrados masivos con dependencias), el sistema captura excepciones de integridad referencial y fuerza un `rollback` automático para asegurar que el sistema nunca quede en un estado inconsistente.
* **Concurrencia y Aislamiento:** El sistema está diseñado para soportar bloqueos de escritura concurrentes. Se validó el aislamiento de las transacciones inyectando bloqueos temporales (`pg_sleep`) durante el flujo de pago, gestionando correctamente la espera de otras sesiones y la resolución de deadlocks por parte del motor.
* **Optimización de Consultas:** Análisis de planes de ejecución mediante `EXPLAIN` e implementación de índices específicos (ej. sobre nacionalidad y fechas de pedidos) para reducir el coste computacional en búsquedas complejas.

## Despliegue del Entorno

Para levantar el proyecto en local es necesario contar con Docker y Docker Compose.

1. Clonar el repositorio:
```bash
   git clone [https://github.com/R0ber-t/async-movie-backend.git](https://github.com/R0ber-t/async-movie-backend.git)
   cd async-movie-backend
   ```

2. Construir y levantar los servicios:
```bash
   docker-compose up --build
   ```
   *Nota: Durante el primer arranque, el contenedor de PostgreSQL ejecutará automáticamente los scripts `schema.sql`, `populate.sql`, `actualiza.sql` y `optimizacion.sql` situados en el directorio `/db` para inicializar el esquema, los datos de prueba y los triggers.*

## Endpoints Destacados

* `POST /user`: Login y autenticación (emisión de token SHA-1).
* `GET /cart` | `PUT /cart/<movie_id>`: Gestión asíncrona del carrito de compras.
* `POST /cart/checkout`: Ejecución transaccional del pago. Activa los triggers de validación de saldo y actualización de inventario.
* `DELETE /borraPais/<pais>`: Endpoint diseñado para auditar el control transaccional. Ejecuta un borrado en cascada manual (ítems, pedidos, carrito, votos, usuarios) realizando un rollback automático en caso de fallo de integridad.

## Documentación Adicional

La Wiki del repositorio debe contener la documentación del proyecto, en forma de memoria técnica explicativa detallada, que recoja todas las decisiones de implementación realizadas a lo largo del desarrollo de la práctica.
