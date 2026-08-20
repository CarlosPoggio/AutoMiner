# Glosario

Términos técnicos usados en este proyecto, explicados en una línea.

- **Repositorio (repo)**: la carpeta del proyecto, controlada por git, donde
  vive todo el código y su historial de cambios.
- **Git**: el sistema que guarda un historial de versiones de los ficheros,
  para poder ver o deshacer cambios pasados.
- **Commit**: una "foto" guardada del estado del proyecto en un momento
  dado, con un mensaje que explica qué cambió.
- **.gitignore**: lista de ficheros que git debe ignorar y nunca subir
  (por ejemplo, tu wallet real).
- **Script**: un programa pequeño que automatiza una tarea (en este caso,
  arrancar el minado).
- **Minería / minado**: el proceso por el que un ordenador hace cálculos
  para una red de criptomoneda a cambio de una recompensa.
- **Wallet**: la dirección donde se reciben las recompensas de minado (como
  un número de cuenta).
- **Pool de minado**: un servidor donde muchos ordenadores minan juntos y
  reparten la recompensa, en vez de minar cada uno por su cuenta.
- **XMRig**: el programa externo y ya existente que hace el trabajo real
  de minado; nuestro script solo lo configura y lo arranca.
- **RandomX**: el algoritmo de minado que usa Monero, diseñado para
  funcionar bien en procesadores normales (CPU) en vez de necesitar
  hardware especial.
- **Dry-run**: modo de "simulación": el programa muestra lo que haría sin
  hacerlo de verdad.
- **Tests (pruebas automáticas)**: pequeños programas que comprueban que
  el código sigue funcionando como se espera, sin tener que probarlo todo
  a mano cada vez.
- **CLI (línea de comandos)**: forma de usar un programa escribiendo
  instrucciones de texto en una terminal, en vez de hacer clic en botones.
- **GPU / CPU**: la GPU es la tarjeta gráfica (útil para minar algunas
  monedas); la CPU es el procesador principal del ordenador (útil para
  minar otras monedas, como Monero).
- **VRAM**: la memoria propia de la tarjeta gráfica. Algunas monedas
  necesitan una cantidad mínima para poder minarse.
- **Algoritmo de minado**: la "receta" de cálculo concreta que usa cada
  criptomoneda (RandomX, KawPow, Etchash...). Determina qué hardware
  sirve para minarla y con qué programa.
- **DAG**: una especie de "libro de datos" que usan algunos algoritmos de
  minado por GPU y que va creciendo con el tiempo; por eso el requisito
  mínimo de VRAM de esas monedas sube poco a poco.
- **Ingreso vs. beneficio**: el ingreso es lo que se gana minando; el
  beneficio es el ingreso menos el coste de la electricidad. Aquí solo
  calculamos ingreso, porque no preguntamos el precio de tu luz.
- **Tkinter**: la librería que viene incluida con Python para crear
  ventanas y formularios sencillos, sin instalar nada adicional (en
  algunos Linux hay que instalar un paquete extra del sistema).
- **API**: una forma en que un programa pide datos a otro por internet
  (aquí se usa para consultar ingresos de minado en tiempo real).
- **JSON**: un formato de texto muy común para intercambiar datos entre
  programas.
