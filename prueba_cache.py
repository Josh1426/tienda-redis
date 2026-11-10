import time
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Base de datos simulada (fuente de verdad). Cada consulta tarda 200 ms.
BASE_DE_DATOS = {
    1: {"nombre": "Auriculares inalambricos", "precio": "29.99"},
    2: {"nombre": "Teclado mecanico", "precio": "45.50"},
    3: {"nombre": "Lampara LED", "precio": "12.00"},
}


def consultar_bd(id_producto):
    time.sleep(0.2)
    return BASE_DE_DATOS[id_producto]


def obtener_producto(id_producto, usar_cache=True):
    clave = f"producto:{id_producto}"
    if usar_cache:
        dato = r.hgetall(clave)
        if dato:
            return dato, "HIT"
    dato = consultar_bd(id_producto)
    if usar_cache:
        r.hset(clave, mapping=dato)
        r.expire(clave, 600)
        return dato, "MISS"
    return dato, "SIN CACHE"


def medir_ms(usar_cache):
    inicio = time.perf_counter()
    _, origen = obtener_producto(1, usar_cache)
    return (time.perf_counter() - inicio) * 1000, origen


if __name__ == "__main__":
    r.delete("producto:1")

    sin_cache = [medir_ms(False)[0] for _ in range(10)]
    promedio_sin = sum(sin_cache) / len(sin_cache)
    print(f"SIN cache: promedio de 10 consultas = {promedio_sin:.1f} ms")

    primera, origen = medir_ms(True)
    print(f"CON cache: primera consulta ({origen}) = {primera:.1f} ms")
    con_cache = [medir_ms(True)[0] for _ in range(9)]
    promedio_con = sum(con_cache) / len(con_cache)
    print(f"CON cache: promedio de las 9 siguientes (HIT) = {promedio_con:.2f} ms")

    print(f"La cache fue {promedio_sin / promedio_con:.0f} veces mas rapida")
    print("TTL restante de producto:1 =", r.ttl("producto:1"), "segundos")
