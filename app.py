import time

import redis
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

USUARIO = 1
TTL_PRODUCTO = 600

# Base de datos simulada (fuente de verdad). Cada consulta tarda 200 ms.
BASE_DE_DATOS = {
    1: {"nombre": "Auriculares inalambricos", "precio": "29.99"},
    2: {"nombre": "Teclado mecanico", "precio": "45.50"},
    3: {"nombre": "Lampara LED", "precio": "12.00"},
}


def consultar_bd(id_producto):
    time.sleep(0.2)
    return BASE_DE_DATOS[id_producto]


def obtener_producto(id_producto):
    clave = f"producto:{id_producto}"
    inicio = time.perf_counter()
    dato = r.hgetall(clave)
    origen = "HIT"
    if not dato:
        dato = consultar_bd(id_producto)
        r.hset(clave, mapping=dato)
        r.expire(clave, TTL_PRODUCTO)
        origen = "MISS"
    ms = (time.perf_counter() - inicio) * 1000
    return dato, origen, ms


def llamar_funcion(nombre, clave1, clave2, arg1, arg2):
    try:
        return int(r.fcall(nombre, 2, clave1, clave2, arg1, arg2))
    except redis.exceptions.ResponseError:
        return None


def nombre_de(id_producto):
    return BASE_DE_DATOS.get(int(id_producto), {}).get("nombre", f"producto {id_producto}")


def volver(tipo, texto):
    return redirect(url_for("inicio", tipo=tipo, msg=texto))


PAGINA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tienda con Redis</title>
<style>
  :root {
    --tinta: #1b2a41; --suave: #5a6b82; --papel: #f6f8fa; --blanco: #ffffff;
    --linea: #cbd5e1; --hit: #0f7b6c; --miss: #b26a00; --error: #b3261e;
    color-scheme: light;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--papel); color: var(--tinta);
         font: 16px/1.5 "Avenir Next", "Segoe UI", system-ui, sans-serif; }
  main { max-width: 1040px; margin: 0 auto; padding: 32px 20px 56px; }
  h1 { font-size: 1.9rem; margin: 0 0 4px; letter-spacing: -0.01em; }
  h2 { font-size: 1.15rem; margin: 0 0 12px; }
  h3 { font-size: 1.05rem; margin: 0; }
  p { margin: 0; }
  .intro { color: var(--suave); max-width: 62ch; margin-bottom: 20px; }
  .aviso { padding: 10px 14px; border-left: 4px solid var(--hit); background: var(--blanco);
           margin-bottom: 20px; }
  .aviso.error { border-color: var(--error); }
  .rejilla { display: grid; grid-template-columns: 1fr 300px; gap: 28px; align-items: start; }
  .barra { display: flex; align-items: center; justify-content: space-between; gap: 12px;
           margin-bottom: 12px; }
  .barra p { color: var(--suave); font-size: 0.9rem; }
  .fila { display: grid; grid-template-columns: 1fr 190px; gap: 8px 20px; padding: 16px;
          background: var(--blanco); border: 1px solid var(--linea); border-bottom-width: 0; }
  .fila:last-of-type { border-bottom-width: 1px; }
  .datos span { display: block; color: var(--suave); }
  .origen { grid-row: span 2; border-left: 4px solid var(--hit); padding-left: 12px; }
  .origen.miss { border-color: var(--miss); }
  .origen strong { display: block; font-size: 1.6rem; line-height: 1.1; color: var(--hit); }
  .origen.miss strong { color: var(--miss); }
  .origen span, .origen small { display: block; }
  .origen small { color: var(--suave); }
  .acciones { display: flex; gap: 8px; flex-wrap: wrap; }
  button { font: inherit; padding: 7px 14px; border: 1px solid var(--tinta); background: var(--tinta);
           color: var(--blanco); border-radius: 4px; cursor: pointer; }
  button.claro { background: var(--blanco); color: var(--tinta); }
  button:hover { filter: brightness(1.15); }
  button:focus-visible { outline: 3px solid var(--hit); outline-offset: 2px; }
  aside section { background: var(--blanco); border: 1px solid var(--linea); padding: 16px;
                  margin-bottom: 20px; }
  ul, ol { margin: 0; padding-left: 20px; }
  li + li { margin-top: 4px; }
  .vacio { color: var(--suave); }
  @media (max-width: 760px) {
    .rejilla { grid-template-columns: 1fr; }
    .fila { grid-template-columns: 1fr; }
    .origen { grid-row: auto; }
  }
</style>
</head>
<body>
<main>
  <h1>Tienda en línea con Redis</h1>
  <p class="intro">Cada producto muestra de dónde salió el dato y cuánto tardó. La primera lectura va a la base
    de datos simulada; las siguientes salen de Redis.</p>

  {% if msg %}<p class="aviso {{ tipo }}" role="status">{{ msg }}</p>{% endif %}

  <div class="rejilla">
    <section>
      <div class="barra">
        <h2>Productos</h2>
        <form method="post" action="{{ url_for('borrar_cache') }}">
          <button class="claro" type="submit">Borrar caché</button>
        </form>
      </div>
      {% for p in productos %}
      <article class="fila">
        <div class="datos">
          <h3>{{ p.nombre }}</h3>
          <span>Precio: ${{ p.precio }}</span>
          <span>Stock: {{ p.stock if p.stock is not none else "sin dato" }}</span>
        </div>
        <div class="origen {{ 'miss' if p.origen == 'MISS' else '' }}">
          <strong>{{ "%.1f"|format(p.ms) }} ms</strong>
          <span>{{ "Desde la base de datos (MISS)" if p.origen == "MISS" else "Desde la caché (HIT)" }}</span>
          <small>Expira en {{ p.ttl }} s</small>
        </div>
        <div class="acciones">
          <form method="post" action="{{ url_for('agregar', id_producto=p.id) }}">
            <button class="claro" type="submit">Agregar al carrito</button>
          </form>
          <form method="post" action="{{ url_for('comprar', id_producto=p.id) }}">
            <button type="submit">Comprar 1</button>
          </form>
        </div>
      </article>
      {% endfor %}
    </section>

    <aside>
      <section>
        <h2>Carrito del usuario {{ usuario }}</h2>
        {% if carrito %}
        <ul>{% for nombre, cantidad in carrito %}<li>{{ nombre }}: {{ cantidad }}</li>{% endfor %}</ul>
        {% else %}<p class="vacio">El carrito está vacío. Agrega un producto.</p>{% endif %}
      </section>
      <section>
        <h2>Más vendidos</h2>
        {% if ranking %}
        <ol>{% for nombre, unidades in ranking %}<li>{{ nombre }}: {{ unidades }} {{ 'vendida' if unidades == 1 else 'vendidas' }}</li>{% endfor %}</ol>
        {% else %}<p class="vacio">Aún no hay ventas. Compra un producto.</p>{% endif %}
      </section>
    </aside>
  </div>
</main>
</body>
</html>
"""

ERROR_REDIS = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Sin conexión</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 560px; margin: 60px auto; padding: 0 20px;">
<h1>No hay conexión con Redis</h1>
<p>Revisa que Docker Desktop esté abierto y que el contenedor esté corriendo:
<code>docker start redis-tienda</code>. Luego recarga esta página.</p>
</body></html>"""


@app.route("/")
def inicio():
    try:
        productos = []
        for id_producto in BASE_DE_DATOS:
            dato, origen, ms = obtener_producto(id_producto)
            productos.append({
                "id": id_producto,
                "nombre": dato["nombre"],
                "precio": dato["precio"],
                "stock": r.get(f"stock:{id_producto}"),
                "origen": origen,
                "ms": ms,
                "ttl": r.ttl(f"producto:{id_producto}"),
            })
        carrito = [(nombre_de(i), cantidad)
                   for i, cantidad in sorted(r.hgetall(f"carrito:{USUARIO}").items())]
        ranking = [(nombre_de(i), int(puntos))
                   for i, puntos in r.zrevrange("ranking:ventas", 0, 4, withscores=True)]
    except redis.exceptions.ConnectionError:
        return ERROR_REDIS, 503
    return render_template_string(
        PAGINA, productos=productos, carrito=carrito, ranking=ranking, usuario=USUARIO,
        msg=request.args.get("msg"), tipo=request.args.get("tipo", "ok"))


@app.post("/agregar/<int:id_producto>")
def agregar(id_producto):
    resultado = llamar_funcion("agregar_carrito", f"stock:{id_producto}", f"carrito:{USUARIO}", id_producto, 1)
    if resultado == 1:
        return volver("ok", f"Agregado al carrito: {nombre_de(id_producto)}.")
    if resultado == -1:
        return volver("error", "Ese producto no existe en el inventario.")
    return volver("error", "Falta cargar los scripts: ejecuta los archivos de la carpeta scripts/.")


@app.post("/comprar/<int:id_producto>")
def comprar(id_producto):
    resultado = llamar_funcion("comprar", f"stock:{id_producto}", "ranking:ventas", 1, id_producto)
    if resultado == 1:
        return volver("ok", f"Compra realizada: 1 unidad de {nombre_de(id_producto)}.")
    if resultado == 0:
        return volver("error", f"No hay stock suficiente de {nombre_de(id_producto)}.")
    if resultado == -1:
        return volver("error", "Ese producto no existe en el inventario.")
    return volver("error", "Falta cargar los scripts: ejecuta los archivos de la carpeta scripts/.")


@app.post("/borrar-cache")
def borrar_cache():
    r.delete(*[f"producto:{i}" for i in BASE_DE_DATOS])
    return volver("ok", "Caché borrada. La próxima lectura irá a la base de datos.")


if __name__ == "__main__":
    app.run(port=5001)
