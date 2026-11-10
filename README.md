# Redis como capa de cache para una tienda en linea

Proyecto final de Bases de Datos. Tema: NoSQL clave-valor y caching (Redis).

## Requisitos
- Docker
- Python 3 y el paquete `redis` (`pip install redis`)
- Redis Insight (opcional, interfaz grafica gratuita): https://redis.io/insight/

## Como ejecutarlo
1. Levantar Redis con persistencia AOF, limite de memoria y notificaciones de expiracion
   (si ya tenias un contenedor con ese nombre, borralo antes con `docker rm -f redis-tienda`):

       docker run -d --name redis-tienda -p 6379:6379 -v redis-data:/data redis:8 redis-server --appendonly yes --appendfsync everysec --maxmemory 256mb --maxmemory-policy volatile-lru --notify-keyspace-events Ex

2. Ejecutar todos los scripts en orden (datos, consultas y DML, transacciones, funciones y consultas complejas).

   Linux / Mac / Git Bash:

       cat scripts/*.redis | docker exec -i redis-tienda redis-cli

   PowerShell:

       Get-Content scripts\*.redis | docker exec -i redis-tienda redis-cli

3. Medir la mejora con y sin cache:

       python prueba_cache.py

4. Abrir Redis Insight, agregar la base `localhost:6379` y revisar las claves en la pestana Browser.

## Archivos
- `scripts/01_datos.redis`: carga de datos (claves, TTL, categorias).
- `scripts/02_consultas_y_dml.redis`: consultas y modificaciones (lectura, actualizacion, borrado).
- `scripts/03_transacciones.redis`: transaccion con WATCH / MULTI / EXEC.
- `scripts/04_funciones.redis`: funciones almacenadas en Lua (comprar y agregar_carrito) y sus pruebas.
- `scripts/05_consultas_complejas.redis`: rankings por categoria con ZINTERSTORE y consultas de posicion y rango.
- `prueba_cache.py`: prueba cache-aside con una base de datos simulada de 200 ms.
- `docs/`: documento final en PDF y diagramas.
