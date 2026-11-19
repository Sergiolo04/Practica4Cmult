from pathlib import Path
import unicodedata, re

root=Path.cwd()
src=root/'output/pdf/guia_ejercicio2.tex'
s=src.read_text(encoding='utf-8')
chunks=[]
def p(t): chunks.append(t+'\n')
def sec(t): p('\\section{'+t+'}')
def sub(t): p('\\subsection{'+t+'}')
def snippet(f,a,b):
    lines=(root/f).read_text(encoding='utf-8-sig').splitlines()
    text='\n'.join(lines[a-1:b])
    text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode()
    name=f.replace('_',r'\_')
    p(r'\textbf{Código real:} \texttt{'+name+r'}, líneas '+str(a)+' a '+str(b)+'.')
    p(r'\begin{lstlisting}[firstnumber='+str(a)+']\n'+text+'\n'+r'\end{lstlisting}')
def block(t,f,a,b,txt):
    p(r'\par\medskip\noindent\begin{minipage}{\linewidth}')
    sub(t);snippet(f,a,b);p(r'\end{minipage}\par');p(txt)

p(r'\chapter{Compresión: entender cada instrucción}')
p(r'''Este capítulo sigue la ejecución real de \texttt{jcom\_custom} y entra
en \texttt{EncodeScans\_custom} cuando la primera la llama. No estudies las
líneas como órdenes aisladas: sigue el dato que cambia de representación.
En cada bloque se identifica la entrada, se interpreta la sintaxis y se explica
qué queda preparado para el siguiente. Los números a la izquierda son las
líneas del archivo original, no una nueva numeración de ejemplos.

Al terminar debes poder señalar una variable y decir si contiene píxeles,
coeficientes, etiquetas, símbolos, códigos o bytes. Esa distinción evita la
mayoría de las confusiones al explicar el proyecto.''')
sec('Antes de ejecutar: leer la sintaxis de MATLAB')
p(r'''\texttt{=} asigna un resultado a una variable; no es una comparación.
\texttt{==} compara igualdad y \texttt{\textasciitilde=} significa distinto.
El punto y coma final evita imprimir automáticamente el resultado, pero no
impide que la instrucción se ejecute. Los comentarios comienzan por \% y no
son órdenes ejecutables. \texttt{...} continúa una misma instrucción en la
siguiente línea: no es un bucle ni una operación sobre los datos.

Los paréntesis sirven para llamar a una función o indexar una matriz.
\texttt{A(:,1)} selecciona todas las filas de la columna 1;
\texttt{A(:,:,2)} selecciona el plano 2 completo. Los corchetes pueden
recoger varias salidas de una función o concatenar matrices. Las llaves
crean celdas o extraen su contenido. Por ejemplo, \texttt{[a;b]} coloca b
debajo de a y \texttt{[a b]} lo coloca a la derecha, si sus dimensiones encajan.

Un \texttt{if} ejecuta su interior cuando la condición es verdadera; un
\texttt{for} repite un bloque. Cada \texttt{end} cierra el bloque correspondiente.
Dentro de un índice, en cambio, \texttt{end} representa la última posición.
Es el mismo término con dos usos que se distinguen por el contexto.''')
sec('Arranque del compresor: contrato, controles y archivo original')
block('La declaración de la función','jcom_custom.m',1,5,r'''
\textbf{Qué entra.} fname identifica el archivo de imagen; caliQ determina
la fuerza de la cuantización. \texttt{function RC = ...} indica una única
salida, RC. En una llamada como \texttt{ahorro=jcom\_custom('Img00.bmp',100)},
el argumento de texto se recibe en fname y 100 en caliQ. Al terminar, el valor
local de RC se copia a ahorro: no hace falta que ambos nombres coincidan.

La función crea su propio espacio de variables. Que exista una variable X
en la ventana de comandos no significa que esta función pueda usarla sin
recibirla o crearla. Del mismo modo, sus variables internas no se exportan
automáticamente. El archivo .huc es un efecto de la función además de su
salida numérica; no es el contenido de RC.
''')
block('Validar caliQ antes de procesar','jcom_custom.m',7,9,r'''
\texttt{validateattributes} recibe tres argumentos: el valor que se revisa,
las clases admitidas y una lista de propiedades. Las dos listas se escriben
con llaves porque son celdas de textos.

\texttt{numeric} exige un tipo numérico; \texttt{scalar}, un único elemento;
\texttt{real} excluye complejos; \texttt{finite} excluye NaN e infinito;
\texttt{integer} exige valor entero aunque esté almacenado como double;
\texttt{positive} exige que sea mayor que cero. Así, 100 es válido, 0 y 2,5
no lo son, y un vector como [50 100] tampoco.

Este control no cambia caliQ ni ajusta automáticamente la calidad: si falla,
detiene la función con un error. Se hace al principio para no transformar
una imagen con una entrada que incumple el contrato. No significa que caliQ
deba almacenarse ya como uint32: su tipo de escritura se decide más tarde.
''')
block('Guardar TO y elegir el nombre de salida','jcom_custom.m',11,16,r'''
\texttt{dir(fname)} consulta el archivo, no sus píxeles. Devuelve una estructura
con campos; el punto de \texttt{info.bytes} accede a su tamaño en bytes.
Ese número se asigna a TO y permanece disponible para RC y para la cabecera.
No calculamos TO como altura por anchura por tres: el archivo de entrada
puede tener cabeceras, paleta o compresión propia.

\texttt{archivo='comprimido.huc'} guarda un texto. Todavía no abre ni crea
nada. Si no se especifica una carpeta, la escritura posterior se hará en el
directorio actual de MATLAB. El nombre fijo implica que otra ejecución puede
reemplazar el resultado anterior. En esta parte, a diferencia del descompresor,
no se añade una comprobación explícita con isfile; se presupone una ruta válida.
''')
sec('Preparar los bloques y transformar la imagen')
block('imlee: interpretar sus siete resultados','jcom_custom.m',18,19,r'''
La llamada es una única instrucción que recoge siete salidas en el orden
definido por imlee. X es el original representado en RGB uint8. Xamp es la
imagen convertida a YCbCr, en double, con dimensiones ampliadas. tipo identifica
si la entrada era indexada o truecolor. m y n son filas y columnas originales;
mamp y namp son las dimensiones tras completar bloques.

Dentro de imlee, una imagen indexada admitida se convierte primero a RGB.
Después se convierte a YCbCr y se replican las últimas filas o columnas que
sean necesarias. Por ejemplo, con m=13 y n=10, mamp=namp=16: se añaden tres
filas y seis columnas. Cada canal se amplía igual y sigue habiendo tres planos.
La función no elimina crominancia ni hace submuestreo.

El compresor no usa después todas estas salidas: X, tipo y los tamaños ampliados
pueden quedar sin nuevas referencias en el archivo principal. Eso no es una
operación oculta. Las salidas forman parte de la interfaz reutilizada. m y n
sí se guardarán para recuperar el tamaño final.
''')
block('imdct: pasar de muestras a coeficientes','jcom_custom.m',21,22,r'''
El argumento es Xamp, porque ya tiene el espacio de color y las dimensiones
que requiere la transformación. No se pasa X, que contiene RGB sin preparar.
La asignación crea Xtrans con el resultado; no cambia el significado de Xamp.

La auxiliar resta 128, separa los tres planos, construye T con dctmtx(8)
y usa blkproc para aplicar $TBT^{\mathsf T}$ a cada bloque centrado B.
Después reúne los tres resultados. Cada bloque contiene DC en (1,1) y 63 AC.
Xtrans mantiene el tamaño ampliado, pero ya no contiene intensidades de píxeles.

Un coeficiente grande significa una contribución fuerte de un patrón, no un
píxel muy luminoso en esa posición. La DCT por sí sola no reduce la cantidad
de coeficientes. Su utilidad es hacer que la cuantización posterior pueda
anular muchos valores pequeños con un coste visual asumible.
''')
block('quantmat: introducir la pérdida controlada','jcom_custom.m',24,25,r'''
quantmat necesita dos entradas: los coeficientes y caliQ. Separa Y, Cb y Cr;
utiliza QY para Y y QC para las otras dos. Las tablas se escalan con caliQ/100,
se redondean y se limita cada escalón a un mínimo de uno.

Para cada bloque, quant88 ejecuta \texttt{floor((x ./ P1)+0.5)}. El operador
\texttt{./} divide elemento a elemento: cada coeficiente utiliza su propio
escalón, no se calcula una división matricial. floor se aplica después de
sumar 0,5. Por ejemplo, 37/10 produce la etiqueta 4, mientras 3/10 produce 0.
DC y AC se cuantizan; ninguno de los 64 coeficientes está exento.

Xlab contiene etiquetas enteras con signo, aunque la matriz sea double.
Un valor entero y un tipo entero no son lo mismo: double puede almacenar
exactamente muchas etiquetas enteras. No convertimos Xlab a uint8 porque
perderíamos los negativos y otros valores fuera del rango 0 a 255.
''')
block('scan: preparar el recorrido de los coeficientes','jcom_custom.m',27,28,r'''
scan recibe etiquetas cuantizadas y llama a zigzag64 por bloques. Conserva
las dimensiones de la imagen y cambia las posiciones de las etiquetas dentro
de cada bloque. El orden deja primero el DC y después los AC desde frecuencias
bajas hacia altas. No ordena de menor a mayor valor numérico.

En XScan los bloques se podrán leer por filas para obtener su secuencia
zigzag. Los ceros que antes ocupaban distintas posiciones de frecuencia
tienden a aparecer seguidos, facilitando la representación por rachas.
Ningún valor se descarta: invscan puede deshacer esta permutación exactamente.
''')
sec('Entrar en EncodeScans\_custom: la parte específica de Huffman')
block('La llamada que conecta el programa principal con la auxiliar','jcom_custom.m',30,34,r'''
Aquí MATLAB pausa el avance por jcom\_custom y ejecuta EncodeScans\_custom
con XScan como entrada. Al regresar, asigna sus once salidas por posición:
tres secuencias binarias y ocho vectores de especificaciones.

Los puntos suspensivos solo hacen legible la instrucción. BITS y HUFFVAL
son las especificaciones que se escribirán en el archivo; CodedY, CodedCb
y CodedCr contienen los datos ya codificados de cada componente. No se están
leyendo todavía desde disco ni se devuelve un archivo por cada componente.
Para entender esta llamada hay que seguir ahora el interior de la auxiliar.
''')
block('Contrato de la auxiliar y separación de planos','EncodeScans_custom.m',1,9,r'''
La cabecera declara las mismas once salidas que recoge el programa principal.
La entrada es una matriz tridimensional XScan. La línea 7 selecciona todas
las filas, todas las columnas y el plano 1; las dos siguientes hacen lo mismo
con los planos 2 y 3. El resultado son tres matrices bidimensionales.

No se convierte el color en estas líneas: ya se hizo en imlee. Tampoco se
copian canales RGB. En esta etapa los planos contienen etiquetas Y, Cb y Cr
en zigzag. Los nombres indican la componente, no una nueva transformación.
''')
block('CollectScan: producir las dos clases de símbolos','EncodeScans_custom.m',11,14,r'''
Cada llamada devuelve dos matrices. Para Y, Y\_DC\_CP tiene una fila por
bloque: columna 1, categoría de la diferencia DC; columna 2, su posición P.
Y\_AC\_ZCP tiene una fila por símbolo AC emitido: columna 1, ZCdec; columna 2, P.
Se repite el contrato para Cb y Cr.

Dentro de CollectScan, DCprevio empieza en cero y se actualiza después de
cada bloque. Los bloques se recorren por filas de bloques, de izquierda a
derecha. La transposición antes de reshape convierte el recorrido habitual
por columnas de MATLAB en la lectura por filas esperada para el zigzag.

catpos calcula C y P para las diferencias DC. zercatpos localiza AC no nulos,
cuenta sus ceros anteriores, calcula categorías y posiciones, emite ZRL si
una racha supera 15 y añade EOB. Para AC=-5, C=3 y P=2; con tres ceros previos,
el símbolo es 51. No se aplica Huffman todavía y no se cuentan frecuencias.

Separar las llamadas evita que el último DC de Y se utilice como referencia
del primero de Cb. La predicción pertenece a cada componente y se reinicia
para cada una. Ese reinicio debe reproducirse al decodificar.
''')
block('Freq256: contar los símbolos adecuados','EncodeScans_custom.m',16,22,r'''
Las líneas 17 y 18 seleccionan solo la primera columna. En DC esa columna
contiene C; en AC contiene el símbolo combinado ZCdec. La segunda columna P
no se usa para diseñar Huffman, porque sus bits se emitirán aparte.

Las líneas 21 y 22 concatenan verticalmente los símbolos de Cb y Cr: primero
los de Cb y después los de Cr. Para un histograma el orden no importa, pero
sí importa incluir todas las apariciones. Si Cb contiene [0;1;1] y Cr [1;2],
la frecuencia conjunta de 1 es tres, no la media de los recuentos por plano.

Freq256 recorre los símbolos 0 a 255 y cuenta coincidencias. FREQ(1) cuenta
el símbolo 0, FREQ(2) el 1, etc. Las posiciones sin apariciones valen cero.
Los cuatro resultados corresponden a dos familias de símbolos por dos grupos
de componentes: Y y crominancia conjunta. No se están contando píxeles ni P.
''')
block('HSpecTables: diseñar las longitudes y el orden de símbolos','EncodeScans_custom.m',24,30,r'''
Cada línea transforma una distribución de frecuencias en un par BITS/HUFFVAL.
El proceso es independiente para Y\_DC, Y\_AC, C\_DC y C\_AC. Cambiar la imagen
o caliQ puede cambiar los símbolos y, por tanto, sus tablas.

HSpecTables combina frecuencias pequeñas para obtener longitudes, añade
temporalmente el símbolo reservado 256 y llama a AdjustBits para limitar
las longitudes y retirar el punto reservado. HUFFVAL final solo contiene
símbolos reales de 0 a 255. No es un vector de frecuencias ni de códigos.

BITS(i) dice cuántos símbolos recibirán códigos de i bits. HUFFVAL enumera
esos símbolos en el orden de asignación: primero los de menor longitud.
La suma de BITS debe coincidir con la longitud de HUFFVAL. Todavía falta
calcular los números binarios concretos que utilizará el codificador.
''')
block('Las cuatro tablas de consulta: analizar el patrón repetido','EncodeScans_custom.m',32,50,r'''
Cada grupo de tres instrucciones tiene una función diferente. HCodeTables
genera HUFFSIZE y HUFFCODE en el orden de HUFFVAL. HUFFSIZE(k) es la longitud
del código de HUFFVAL(k); HUFFCODE(k), su valor numérico.

HCodingTables reorganiza esos datos para que el índice dependa del símbolo,
no del orden de asignación. Produce EHUFCO y EHUFSI de 256 posiciones.
Para un símbolo s, EHUFCO(s+1) es el código y EHUFSI(s+1) su longitud.
Los corchetes de la tercera instrucción concatenan ambas columnas para
formar una matriz de 256 por 2, llamada ehuf de esa familia.

Por ejemplo, si al símbolo 7 se le asigna 001, la fila 8 contiene [1 3].
El 1 no basta para distinguir 1, 01 y 001; el 3 conserva la longitud. Una
longitud cero corresponde a un símbolo sin código; un código numérico cero
con longitud positiva sí es válido.

En las líneas 38 a 40 se repite para Y\_AC, en 43 a 45 para C\_DC y en
48 a 50 para C\_AC. Se reutilizan nombres temporales como HUFFCODE porque
cada tabla definitiva ya quedó almacenada en su propia variable ehuf.
Reasignar el temporal no cambia las matrices guardadas anteriormente.
''')
block('Emitir los tres flujos y devolver resultados','EncodeScans_custom.m',52,63,r'''
Cada llamada pasa cinco argumentos: el plano, sus DC preparados, sus AC
preparados, la tabla DC y la tabla AC. EncodeSingleScan utiliza el plano
como parte de su interfaz; los valores a emitir se encuentran en las matrices
recogidas. Las tres salidas son secuencias de caracteres 0 y 1.

Y utiliza ehuf\_Y\_DC y ehuf\_Y\_AC. Cb y Cr utilizan el mismo par ehuf\_C\_DC
y ehuf\_C\_AC, pero siguen siendo dos flujos separados. Compartir tabla
significa compartir diccionario, no mezclar componentes en una sola secuencia.

La auxiliar recorre cada bloque, escribe la palabra de su categoría DC,
los bits de posición cuando corresponden, los símbolos AC y EOB. Los símbolos
Huffman no codifican por sí solos la amplitud: P completa la información.
La copia suministrada merece revisar el caso C=0, explicado en el capítulo
de validación; la intención del formato es no añadir amplitud de longitud cero.

El end de la línea 63 cierra la función. MATLAB vuelve a la llamada del
programa principal con las once salidas ya asignadas; no hace falta un return
explícito al final. Las tablas intermedias locales desaparecen al salir.
''')
sec('Volver a jcom\_custom: empaquetar y definir el contenedor')
block('Empaquetar no es volver a comprimir con otro algoritmo','jcom_custom.m',37,45,r'''
Cada llamada a bits2bytes recibe un vector de caracteres y devuelve bytes
uint8 e indicador ultl. '10110010' se representa como el número 178 en un
solo byte. Se cambia de representación: no se modifica el significado del flujo.

Si hay 11 bits, se obtiene un byte completo y otro con tres bits válidos
y cinco ceros de relleno. ultl vale 3. Si hay 16 bits, se obtienen dos bytes
completos y ultl vale 0. En esta implementación, cero significa que no existe
grupo residual; no significa que el último byte carezca de datos.

numel cuenta elementos de los vectores de bytes. Como cada elemento uint8
se guardará en un byte, LY, LCb y LCr son los tamaños de datos de cada componente.
No incluyen la cabecera ni las tablas, y tampoco son longitudes en bits.
Se guardan para que el lector sepa dónde termina cada flujo.
''')
block('Controlar el rango antes de convertir','jcom_custom.m',47,57,r'''
La línea 50 reúne siete números en un vector fila para revisarlos juntos:
dimensiones, caliQ, tamaño original y tres longitudes. No es todavía la
cabecera del archivo: las longitudes se escribirán junto a sus componentes.

validateattributes exige que todos sean reales, finitos, enteros y no negativos.
El par de entradas \texttt{'<=', double(intmax('uint32'))} impone un máximo
de 4294967295. intmax obtiene ese límite y double permite trabajar con él
en el control numérico. Validar antes de convertir evita ocultar un valor
demasiado grande mediante saturación.

La línea 57 crea la cabecera con solo [m n caliQ TO] y la convierte a uint32.
El orden de sus cuatro elementos es el contrato de lectura. No se escriben
mamp ni namp porque se pueden deducir de m y n. Cambiar este orden exige
cambiar el descompresor de manera compatible.
''')
block('Celdas: guardar cuatro vectores de tamaños diferentes','jcom_custom.m',59,63,r'''
Las llaves construyen una celda fila con cuatro contenidos, en el orden
Y\_DC, Y\_AC, C\_DC, C\_AC. Una celda permite que cada HUFFVAL tenga una
longitud distinta. Una concatenación numérica normal exigiría dimensiones
compatibles y perdería la separación explícita entre tablas.

\texttt{tablasBITS\{2\}} devuelve el vector BITS de Y\_AC; en cambio,
\texttt{tablasBITS(2)} devolvería una celda que contiene ese vector. Las
auxiliares de suma y escritura necesitan el contenido numérico. Las dos
celdas están alineadas por índice: BITS y HUFFVAL de la posición k pertenecen
a la misma familia. No hay nombres de tabla escritos en el archivo.
''')
block('Normalizar BITS: entender cada línea del bucle','jcom_custom.m',65,79,r'''
\textbf{Línea 66.} k toma sucesivamente 1, 2, 3 y 4. Todo el interior se
ejecuta una vez por tabla. \textbf{Línea 67.} Se extrae su vector en b.
\textbf{Línea 68.} b(:) coloca todos sus elementos en una columna, conservando
su orden. No calcula frecuencias ni ordena valores.

\textbf{Líneas 70 y 71.} assert exige una condición verdadera; si es falsa,
lanza el mensaje. Se permiten hasta 16 posiciones. AdjustBits puede recortar
su cola, por lo que exigir exactamente 16 antes de completar provocó el
primer error del desarrollo.

\textbf{Línea 74.} Dentro del índice, end representa la última fila actual.
Si b tiene 10 elementos, end+1:16 es 11:16. Se asigna cero a esas filas de
la columna 1. Si ya tiene 16, el intervalo 17:16 está vacío y no añade nada.
Se afirma que no existen códigos de las longitudes ausentes; no se crean
símbolos. \textbf{Línea 75.} Se devuelve la copia normalizada a su celda.

\textbf{Líneas 77 y 78.} sum(b) cuenta todas las palabras declaradas, mientras
numel(HUFFVAL) cuenta sus símbolos. Deben ser iguales. \textbf{Línea 79.}
Este end cierra el for, no la función. Las tablas ya codificadas con el BITS
corto conservan los mismos códigos que con esta cola de ceros.
''')
sec('Escribir bytes con un contrato verificable')
block('Abrir la salida y detectar un fallo de apertura','jcom_custom.m',82,87,r'''
fopen devuelve un número identificador, fid, que las siguientes funciones
utilizan para referirse al archivo abierto. No contiene los bytes ni su tamaño.
El texto wb indica escritura binaria; ieee-le fija little-endian para campos
de más de un byte. Si el archivo existía, puede truncarse al abrirlo.

La comparación fid==-1 detecta que no se pudo abrir. error interrumpe la
función; no se intenta seguir escribiendo con un identificador inválido.
El end de la línea 87 cierra solamente ese if. Los errores de escritura
posteriores se controlan con el try/catch del siguiente bloque.
''')
block('Calcular el tamaño esperado antes de escribir','jcom_custom.m',89,97,r'''
Los 16 bytes de cabecera salen de cuatro uint32. Los 128 bytes de BITS son
cuatro tablas por 16 recuentos por dos bytes. Los 15 bytes adicionales son
tres longitudes uint32 de cuatro bytes más tres indicadores de un byte.
A eso se añaden LY, LCb y LCr, que ya representan datos empaquetados.

La primera asignación suma las partes fijas y los flujos. El bucle añade
numel(HUFFVAL) para cada tabla: un byte por símbolo. Esos tamaños son variables,
por lo que no se pueden sustituir siempre por 256. Si las cuatro tablas
tuvieran 4, 20, 3 y 12 símbolos, añadirían 39 bytes.

TCprevisto se mide en bytes. No se reserva memoria del archivo mediante esta
fórmula ni se escribe ese total como un campo: se conserva en memoria para
comprobar la escritura y el tamaño real al terminar.
''')
block('Escribir cabecera y especificaciones','jcom_custom.m',99,110,r'''
try inicia el bloque protegido. La línea 101 escribe cuatro valores de la
cabecera como uint32. fwrite devuelve la cantidad de elementos efectivamente
escritos; si son cuatro, multiplicar por cuatro da 16 bytes. escritos nace
con ese recuento. No se escribe la propia variable escritos en el archivo.

El for vuelve a seguir el orden de las cuatro tablas. Para cada una,
uint16 convierte sus recuentos y fwrite solicita esa precisión de salida.
El recuento devuelto se multiplica por dos. Después uint8 convierte HUFFVAL
y fwrite lo guarda: un elemento coincide con un byte. Los puntos suspensivos
continúan cada asignación de suma en la siguiente línea.

La forma \texttt{escritos = escritos + ...} actualiza un acumulador: el nuevo
valor es lo ya contabilizado más lo que acaba de escribirse. Se alternan BITS
y HUFFVAL de una tabla antes de pasar a la siguiente. No se escriben primero
todos los BITS y luego todos los HUFFVAL; el lector debe respetar esta alternancia.
''')
block('Escribir Y, Cb y Cr sin confundir sus límites','jcom_custom.m',112,125,r'''
Cada componente se escribe con tres instrucciones. La primera guarda su
cantidad de bytes como un único uint32 y suma cuatro bytes al acumulador.
La segunda guarda ultl como uint8 y suma un byte. La tercera guarda todos
los valores de su vector uint8 y suma cuantos haya escrito.

Así, Y ocupa 5+LY bytes; Cb, 5+LCb; Cr, 5+LCr. Sus tres indicadores no se
guardan juntos al principio: cada uno está junto a la longitud de su plano.
Las líneas 118 a 120 repiten el patrón para Cb y 123 a 125 para Cr. Usar
accidentalmente LY al escribir Cb produciría un contrato erróneo aunque los
bytes individuales fuesen válidos.

uint32(LY) y uint8(ultlY) especifican los valores a serializar; el último
argumento de fwrite indica cómo se escribirán. Aquí se hacen explícitas ambas
cosas. Los flujos ya son uint8 y no necesitan una nueva conversión.
''')
block('Control de escritura y ruta de error','jcom_custom.m',127,135,r'''
El if compara el acumulador con el tamaño esperado. El operador distinto
no significa que las imágenes difieran; compara dos tamaños de archivo.
Si se ha escrito menos o más de lo previsto, error genera una excepción.

catch fallo captura los errores que se produzcan dentro de try, incluidos
los lanzados por ese if. fallo es un objeto con información del error.
fclose libera el descriptor y rethrow(fallo) vuelve a lanzar el mismo error
para que se vea su causa. No convierte un fallo en un resultado correcto.
El end de la línea 135 termina try/catch; en el camino de error no se avanza
normalmente al cálculo de RC.
''')
block('Cerrar correctamente en el camino normal','jcom_custom.m',137,141,r'''
Si no se ha producido ningún error en try, se llega a esta llamada a fclose.
Su valor de retorno se guarda en estado: cero indica cierre correcto.
La comparación estado distinto de cero provoca un error si el cierre falla.

No se está cerrando normalmente dos veces: el cierre del catch solo se
ejecuta cuando hay una excepción y rethrow abandona esa ruta. Cerrar antes
de medir permite finalizar la escritura pendiente. TO es el tamaño original;
todavía falta consultar el tamaño del nuevo archivo completo.
''')
block('Medir TC, devolver RC y terminar','jcom_custom.m',143,155,r'''
dir consulta ahora el archivo de salida. Su campo bytes se guarda en TC.
Se contrasta ese tamaño real con TCprevisto; el recuento de fwrite y la
medición posterior son comprobaciones relacionadas pero diferentes.

La fórmula calcula el ahorro respecto a TO. Si TO=1000 y TC=400,
RC=60. Si TC=1200, RC=-20: el resultado ha crecido un 20 por ciento.
No se toma el tamaño de Xlab ni la longitud de los caracteres binarios.
En el valor final se incluye el coste de las tablas y los metadatos.

La asignación a RC deja preparada la salida declarada en la primera línea.
El end final cierra la función y devuelve el control al llamador. El archivo
queda en disco, aunque las variables locales desaparezcan.
''')
sec('Seguir una ejecución sin perderse entre funciones')
p(r'''Para estudiar, escribe tres columnas en papel: variable, representación y
función que la crea. Antes de EncodeScans\_custom tienes etiquetas; al volver,
tienes caracteres binarios y especificaciones. Antes de fwrite tienes valores
numéricos en memoria; después existe una representación binaria en disco.

Una lectura correcta del compresor en voz alta sería: ``Valido entradas y
mido el original; preparo la imagen; transformo y cuantizo; permuto los bloques;
obtengo símbolos y sus frecuencias; construyo códigos; represento los símbolos
con códigos y amplitudes; empaqueto; guardo la información necesaria para
invertir esa representación; finalmente mido y calculo el ahorro''.

Comprueba que puedes explicar por qué caliQ se usa antes de contar frecuencias:
cambiar la cuantización cambia las etiquetas, sus rachas y las categorías.
Por eso las tablas a medida dependen de la imagen y de la cuantización,
no solamente del nombre del archivo.''')
comp='\n'.join(chunks);chunks=[]

p(r'\chapter{Descompresión: entender cada instrucción}')
p(r'''El descompresor trabaja primero con un archivo de bytes y termina con una
matriz RGB. Su primera mitad interpreta un formato; su segunda mitad reconstruye
la imagen; al final evalúa. Separar mentalmente estas tres responsabilidades
ayuda a no confundir leer bytes, decodificar Huffman y aplicar DCT inversa.

Los fragmentos siguientes recorren todo el archivo principal y toda la auxiliar
DecodeScans\_custom. Cuando una secuencia se repite para Cb y Cr se explica
qué conserva y qué cambia. Los números corresponden a las líneas reales
del código reproducido en los apéndices.''')
sec('Entrada, salida y referencia para evaluar')
block('Qué recibe y qué devuelve jdes\_custom','jdes_custom.m',1,16,r'''
La función declara dos resultados: primero MSE y después RC. Por ejemplo:
\begin{quote}\small\ttfamily [e,r]=jdes\_custom('comprimido.huc')\end{quote}
e recibirá MSE y r recibirá RC.
fname identifica el comprimido, no el BMP original. La función también
guardará una imagen BMP como efecto de la ejecución.

En la línea 8, isfile pregunta si existe un archivo y el tilde delante niega
la respuesta. Si no existe, error detiene el proceso antes de leer nada.
El end cierra ese control. dir devuelve la información del comprimido;
TC=info.bytes conserva su tamaño real para RC y para los límites de lectura.

archivoSalida solo contiene el nombre del futuro BMP. Aún no se ha creado.
Tampoco se ha calculado MSE ni RC: son salidas que se asignarán cuando existan
los datos necesarios. El nombre fijo puede sobrescribir una reconstrucción previa.
''')
block('Pedir el original: lectura de texto y comprobación','jdes_custom.m',18,24,r'''
input muestra la pregunta y espera una respuesta. Su segundo argumento s
indica que se quiere texto, sin evaluar lo escrito como una instrucción MATLAB.
Por eso el usuario puede escribir Img00.bmp sin comillas en esa pregunta.
El texto queda en nombreOriginal.

Se utiliza de nuevo isfile con negación: si la ruta no existe, se lanza error.
La petición del original es una decisión de evaluación, no un requisito de
Huffman. El .huc ya contiene los datos para reconstruir la imagen. La referencia
original se necesita para comparar, calcular MSE y mostrar ambas imágenes.
El código no guarda su nombre dentro del contenedor.
''')
block('Recibir solo las salidas que hacen falta','jdes_custom.m',26,31,r'''
imlee convierte la referencia a RGB si es necesario y entrega X como primera
salida. Los dos tildes siguientes descartan Xamp y tipo; mOriginal y nOriginal
recogen la cuarta y quinta salida. Pedir menos salidas no modifica el orden
de las restantes ni convierte mOriginal en una dimensión ampliada.

La condición de la línea 29 combina dos motivos de error mediante OR lógico
de cortocircuito, escrito con dos barras verticales: que el tamaño de la
dimensión 3 no sea tres, o que X no sea uint8. Si cualquiera es verdadero,
se detiene. size(X,3) devuelve el número de canales e isa consulta la clase.

X no se envía a DecodeScans\_custom. Se conserva en jdes\_custom para evaluar
al final. Seleccionar otra imagen del mismo tamaño superaría el control de
dimensiones, pero produciría una comparación equivocada: el usuario debe
indicar la referencia correcta.
''')
sec('Abrir el archivo y entender la lectura binaria')
block('Descriptor y cierre automático','jdes_custom.m',33,42,r'''
fopen usa rb para leer bytes y ieee-le para interpretar los campos multibyte
en el mismo orden del escritor. fid identifica el archivo abierto. -1 indica
fallo de apertura; si aparece, error detiene la función y no se sigue leyendo.

La expresión \texttt{@() fclose(fid)} crea una función anónima sin argumentos.
No cierra el archivo al escribir esa expresión: define la acción que debe
ejecutarse después. onCleanup guarda esa acción en un objeto y la ejecuta
cuando ese objeto se destruye.

Si se abandona la función por un error, las variables locales se liberan
y el objeto cierra el archivo. En el camino correcto se destruye explícitamente
con clear cierreArchivo después de terminar la lectura. Esta estrategia
evita repetir try/catch en cada operación. No debe añadirse otro fclose
independiente que cierre el mismo descriptor antes de seguir leyendo.
''')
block('Leer cuatro elementos, no cuatro bytes','jdes_custom.m',44,49,r'''
fread recibe fid, la cantidad 4 y la precisión *uint32. Se solicitan cuatro
elementos de cuatro bytes: en total 16 bytes. El asterisco hace que el
resultado se conserve como uint32, en vez de entregarse por defecto como double.
El resultado datos es un vector columna en el orden de lectura.

fread avanza la posición del archivo. Después de una lectura completa queda
en el desplazamiento 16, donde empieza BITS de Y\_DC. No hay separadores
ni nombres de campos que el lector pueda buscar: el orden define el significado.

numel(datos) verifica que realmente llegaron cuatro elementos. Si el archivo
está truncado, fread puede devolver menos sin que por sí solo detenga el programa.
El control evita acceder a datos(4) cuando no existe. El end termina el if.
''')
block('Asignar significado a cada posición y validar','jdes_custom.m',51,60,r'''
Cada asignación extrae un elemento del vector: m es altura, n anchura,
caliQ factor de cuantización y TO tamaño original. double cambia el tipo
numérico para los cálculos, no el valor de estos uint32. Los enteros de
uint32 caben exactamente en double, por lo que aquí no se pierde precisión.

\texttt{[m n caliQ TO]==0} produce cuatro valores lógicos. any devuelve
verdadero si al menos uno lo es. Por tanto, se rechaza que cualquiera de
los cuatro datos sea cero. Los negativos ya eran imposibles al leer uint32.
Este control detecta algunos valores no válidos, pero no garantiza que toda
cabecera arbitraria represente una imagen razonable.

El TO leído no se calcula a partir de la referencia seleccionada: es el
tamaño que el compresor guardó cuando creó el archivo. Así ambos calculan RC
con el mismo dato de origen. caliQ se utilizará en la descuantización,
no para diseñar de nuevo Huffman.
''')
block('Reconstruir tamaños ampliados y contrastar la referencia','jdes_custom.m',61,68,r'''
ceil redondea hacia arriba. Dividir m entre ocho, aplicar ceil y multiplicar
por ocho obtiene el menor múltiplo de ocho que no es menor que m. Si m=13,
sale 16; si m=16, se mantiene. Se repite para n. Estas dimensiones determinan
el tamaño de los planos y el número de bloques que se decodificarán.

El OR lógico de la línea 66 detecta que la altura o la anchura de la referencia
no coincida con la cabecera. Basta una diferencia para lanzar error.
No se compara aquí el contenido de X. El control evita un MSE entre matrices
de distinta forma, pero la identidad del original depende de la elección del usuario.
''')
sec('Leer las cuatro tablas sin perder la posición del archivo')
block('Reservar celdas y comenzar el bucle','jdes_custom.m',70,75,r'''
cell(1,4) crea una fila de cuatro celdas inicialmente vacías. Una guardará
los cuatro vectores BITS y otra los HUFFVAL, de longitudes variables.
No reserva cuatro veces 256 símbolos ni lee nada por sí misma.

El bucle k=1:4 determina la identidad de cada pareja: 1 es Y\_DC, 2 Y\_AC,
3 C\_DC y 4 C\_AC. Como el archivo no contiene etiquetas de texto, cambiar
ese orden asignaría códigos incorrectos aunque todas las lecturas devolvieran bytes.
''')
block('Leer BITS y averiguar cuántos símbolos vienen después','jdes_custom.m',76,90,r'''
fread solicita 16 elementos uint16, equivalentes a 32 bytes. Como el escritor
completó BITS con ceros, siempre debe existir esa cantidad. El control numel
detecta lectura incompleta; el texto del error incorpora k mediante \%d,
que es un marcador para un entero dentro de ese mensaje.

b=double(b) prepara el vector para sum y las auxiliares. cantidadSimbolos=sum(b)
suma códigos de todas las longitudes. Si b=[0;2;2;0;...] significa que deben
aparecer cuatro símbolos de HUFFVAL a continuación. No significa que haya
cuatro bits de datos ni que todas las palabras midan cuatro.

La condición comprueba un límite inferior y otro superior: se necesitan
entre uno y 256 símbolos. En una imagen no vacía cada familia genera datos;
un HUFFVAL vacío no es una tabla útil en este contrato. El OR permite rechazar
cualquiera de los dos extremos fuera del rango.
''')
block('Leer HUFFVAL, descartar duplicados y almacenar','jdes_custom.m',92,107,r'''
Ahora fread lee cantidadSimbolos elementos uint8: un byte por símbolo. La
posición avanza justo hasta el comienzo del siguiente BITS. No es necesario
guardar un campo adicional con la longitud de HUFFVAL, porque se acaba de
deducir de BITS.

numel comprueba que se haya leído todo. Tras convertir h a double, unique(h)
produce sus valores distintos. Si esa cantidad es menor que cantidadSimbolos,
existe un símbolo repetido y el archivo se rechaza. Por ejemplo, [2;5;2]
solo tiene dos valores distintos y fallaría. Esto no es una comprobación
completa de todas las propiedades de un código prefijo.

Las asignaciones con llaves guardan el vector numérico en la celda k.
El end de la línea 107 cierra el for y repite el proceso hasta completar
las cuatro parejas. Se reutilizan b y h como temporales, conservando cada
resultado en su celda antes de pasar a la siguiente tabla.
''')
block('Recuperar nombres explícitos para la interfaz','jdes_custom.m',109,120,r'''
Estas ocho asignaciones no recalculan ninguna tabla. Extraen los contenidos
de las celdas y los asocian a nombres legibles que coinciden con los argumentos
de DecodeScans\_custom. La posición 1 contiene Y\_DC; la 2 Y\_AC; la 3 C\_DC;
la 4 C\_AC. Cada BITS se mantiene emparejado con su HUFFVAL.

La utilidad es hacer visible qué familia se pasa en cada llamada. Si se
intercambiara HUFFVAL\_Y\_DC con el de AC, las matrices seguirían siendo
numéricas, pero los bits recuperarían símbolos equivocados. La compatibilidad
de dimensiones no garantiza compatibilidad de significado.
''')
sec('Leer las componentes: tamaño, indicador y datos')
block('Preparar el bucle común para Y, Cb y Cr','jdes_custom.m',123,129,r'''
nombres es una celda con tres textos y se usa en mensajes de error.
bytesComponentes será otra celda, porque los tres flujos pueden ocupar
distintas cantidades de bytes. longitudes e indicadores son vectores fila
de tres ceros, creados con zeros(1,3), que después recibirán los valores leídos.

El for recorre primero Y, después Cb y después Cr. No se utiliza un bucle
de cuatro porque estas son componentes, no familias de tablas Huffman.
Hay tres flujos y cuatro tablas: son dos cantidades diferentes por diseño.
''')
block('Leer la longitud y ultl antes del vector','jdes_custom.m',130,145,r'''
La primera llamada solicita un elemento uint32: la longitud del flujo en
bytes. Si no hay un elemento completo, isempty detecta la ausencia y se
lanza error. El marcador \%s del mensaje se sustituye por nombres\{k\},
el texto de la componente actual.

La segunda lectura solicita un uint8 con ultl. Se comprueba también que
exista. El orden importa: si primero se interpretara la longitud como un
byte, la posición del lector quedaría desplazada y todo lo posterior fallaría.
Se convierten ambos escalares a double para compararlos y usarlos en cálculos.

Por ejemplo, si se escribieron LY=2000 y ultlY=3, se leen cuatro bytes que
forman el número 2000, después un byte con el número 3 y, más adelante,
exactamente 2000 bytes de datos. No se leen 2000 bits.
''')
block('Comprobar el indicador y que la longitud sea posible','jdes_custom.m',147,153,r'''
ultl debe estar entre cero y siete. Ya se leyó como uint8, por lo que no
puede ser negativo; la condición solo necesita rechazar valores mayores que siete.
Cero significa bytes completos, no ausencia de datos.

ftell(fid) devuelve cuántos bytes se han recorrido desde el inicio. TC menos
esa posición da los que quedan. Si la longitud declara más datos que los
restantes, el archivo es inconsistente. También se rechaza longitud cero,
porque este contrato espera un flujo no vacío por componente.

Este control se aplica antes de pedir el vector para no aceptar una lectura
de tamaño imposible. No demuestra todavía que los bytes contengan códigos
Huffman válidos; solo revisa un límite estructural.
''')
block('Leer los bytes y conservar los tres resultados','jdes_custom.m',155,165,r'''
fread solicita longitud elementos uint8 y devuelve un vector columna.
numel(bytes) contrasta la cantidad real con la anunciada. Solo después de
superar la comprobación se guarda la longitud en la posición k de su vector,
el indicador en la misma posición y los bytes en la celda k.

Aunque la variable temporal se llame bytes para las tres iteraciones,
cada vector anterior queda conservado en bytesComponentes. El end cierra
el bucle: a continuación se dispone de toda la información de los tres planos,
no solo de la última componente.
''')
block('Extraer variables y terminar la lectura','jdes_custom.m',167,186,r'''
Las tres primeras asignaciones recuperan las longitudes con paréntesis,
porque longitudes es un vector numérico. Las tres siguientes hacen lo mismo
con indicadores. Los vectores de bytes se extraen con llaves, porque están
en una celda. Ninguna de estas líneas vuelve a leer el archivo.

Se exige que ftell coincida con TC: después de consumir las tres componentes
no debe quedar una cola sin interpretar. Si sobra contenido, error detiene
la función; el objeto onCleanup cerrará el descriptor durante la salida por error.

En el camino correcto, clear cierreArchivo destruye el objeto y ejecuta
fclose. No borra bytesY, las tablas ni el archivo de disco. Solo libera el
recurso de lectura que ya no hace falta. A partir de aquí se trabaja con
los datos guardados en memoria.
''')
sec('Recuperar los bits y decodificar las etiquetas')
block('bytes2bits: recuperar exactamente la secuencia anterior','jdes_custom.m',188,191,r'''
Cada llamada recibe los bytes de una componente y su propio indicador.
La auxiliar usa dec2bin con ancho ocho para conservar los ceros iniciales
de cada byte, concatena por filas y recorta el último grupo solo cuando
ultl es positivo. Por ejemplo, el byte 5 produce 00000101, no solo 101.

Si el último byte es 10100000 y ultl=3, se conservan 101. Si ultl=0, se
conservan los ocho bits de todos los bytes. Eliminar todos los ceros finales
sería incorrecto porque pueden pertenecer a códigos o amplitudes reales.

CodedY, CodedCb y CodedCr son caracteres binarios. Todavía no contienen
etiquetas, coeficientes o píxeles. El empaquetado ya se ha invertido; ahora
falta interpretar los códigos con el diccionario adecuado.
''')
block('Llamar a la auxiliar con el tamaño y las tablas correctos','jdes_custom.m',193,197,r'''
La llamada pasa doce argumentos: tres secuencias, un vector de dos dimensiones
y los ocho vectores BITS/HUFFVAL. [mamp namp] es una concatenación de dos
escalares y define la forma que tendrá cada plano decodificado.

Las tablas no se generan de nuevo desde el original ni desde las intensidades:
son exactamente las leídas del archivo. Como el código es canónico, bastan
para reproducir los mismos códigos. El resultado XScanrec se asignará cuando
termine la auxiliar. Entramos ahora en DecodeScans\_custom para entender
qué ocurre dentro de esta sola instrucción.
''')
block('Interfaz de DecodeScans\_custom','DecodeScans_custom.m',1,4,r'''
La declaración nombra las entradas en el mismo orden de la llamada.
tam recibe [mamp namp]. La única salida es XScanrec, que reunirá los tres
planos de etiquetas. Los nombres son locales: la auxiliar no puede consultar
directamente X, TC ni otras variables del programa principal si no las recibe.

Esto explica el error de visualización corregido en el desarrollo: poner
imshow(X) aquí no funciona porque esta función no ha creado ni recibido X.
Su responsabilidad es decodificar etiquetas; la evaluación y figura pertenecen
a jdes\_custom.
''')
block('Reconstruir las cuatro tablas de decodificación','DecodeScans_custom.m',6,24,r'''
Cada familia necesita dos llamadas. HCodeTables recibe BITS/HUFFVAL y genera
los mismos códigos canónicos que usó el compresor. El primer resultado,
HUFFSIZE, se descarta con tilde porque esta ruta no lo usa. HUFFCODE conserva
los números de los códigos en el orden de HUFFVAL.

HDecodingTables recibe BITS y HUFFCODE y produce tres vectores. MINCODE(i)
es el primer código de longitud i cuando existen códigos de esa longitud;
MAXCODE(i) es el último y vale -1 si no existe ninguno; VALPTR(i) indica
dónde empieza ese grupo dentro de HUFFVAL. Son ayudas de búsqueda, no
nuevas frecuencias ni palabras de imagen.

El patrón se repite para Y\_AC en 12 a 14, C\_DC en 17 a 19 y C\_AC en
22 a 24. Se reutiliza HUFFCODE como temporal, pero cada conjunto de mincode,
maxcode y valptr queda en variables propias. Las tablas de crominancia
se aplicarán por igual a Cb y Cr.

Ejemplo: si HUFFVAL=[10;20;30;40] y los códigos son 00, 01, 100, 101,
para longitud 3 MINCODE=4, MAXCODE=5 y VALPTR=3. Al leer 101, su valor 5
produce índice $3+5-4=4$ y HUFFVAL(4)=40. El código se traduce en símbolo,
no en un píxel de valor 40.
''')
block('DecodeSingleScan: argumentos y retorno de cada plano','DecodeScans_custom.m',26,45,r'''
Cada llamada pasa diez argumentos: el flujo de caracteres; MINCODE, MAXCODE,
VALPTR y HUFFVAL de DC; el mismo grupo de cuatro para AC; y tam. La separación
DC/AC es necesaria porque una misma palabra de bits puede representar
símbolos diferentes en diccionarios distintos.

La primera llamada utiliza tablas de Y. Las dos siguientes utilizan las
tablas compartidas de crominancia, pero leen sus propias secuencias CodedCb
y CodedCr. Cada llamada inicializa su propio DCprevio a cero. Los resultados
son matrices bidimensionales de etiquetas en zigzag, de tamaño tam.

Dentro de DecodeSingleScan se mantiene ptr, el índice del siguiente carácter
del flujo. DecodeWord lee bits hasta reconocer una palabra con las tablas
canónicas y devuelve un símbolo más el puntero actualizado. Después el
decodificador lee C bits de posición, si C es positivo. El puntero cuenta
bits representados como caracteres, no bytes del archivo ya cerrado.

Para DC se recupera la diferencia y se suma al DC anterior. Para AC se deja
el bloque inicialmente a cero, se avanza por las rachas y se colocan los
valores no nulos. ZRL suma 16 posiciones cero; EOB termina ese bloque. Este
procedimiento debe reconstruir las etiquetas exactamente, no aproximadamente.
La aproximación se introducirá al interpretar las etiquetas como coeficientes.
''')
block('Reunir planos y regresar al programa principal','DecodeScans_custom.m',47,50,r'''
cat recibe primero el número de dimensión. El 3 indica que se apilan los
tres planos en la tercera dimensión. No se suman ni se concatenan horizontalmente:
el resultado tiene tamaño mamp por namp por 3, con Y, Cb y Cr en ese orden.

La asignación prepara XScanrec, la salida de la auxiliar. El end final
termina la función y el programa principal continúa después de su llamada.
Las tablas mincode y el resto de temporales no se exportan porque ya han
cumplido su función. XScanrec aún no es una imagen RGB para mostrar.
''')
sec('Reconstruir la imagen a partir de las etiquetas')
block('invscan: devolver cada etiqueta a su frecuencia','jdes_custom.m',199,200,r'''
invscan deshace la permutación realizada por scan. Su entrada son las etiquetas
en zigzag de los tres planos. Su salida Xlabrec contiene los mismos valores
en las posiciones naturales de cada bloque de coeficientes.

No se aplica una DCT en este paso. Tampoco se multiplican etiquetas ni se
eliminan ceros. Cada posición vuelve a representar la frecuencia horizontal
y vertical correspondiente: DC en la esquina superior izquierda y los AC
en el resto. El tamaño ampliado no cambia.
''')
block('desquantmat: qué se puede recuperar y qué no','jdes_custom.m',202,203,r'''
La función recibe Xlabrec y el caliQ leído de la cabecera. Reconstruye los
mismos escalones QY y QC que utilizó el compresor y multiplica cada etiqueta
por su escalón correspondiente, elemento a elemento y por bloques.

Si se obtuvo etiqueta 4 con escalón 10, el coeficiente reconstruido es 40.
No se sabe si el original era 37, 39 o algún otro valor del mismo intervalo.
La multiplicación no puede recuperar la fracción descartada al cuantizar.
Por eso Xtransrec se llama reconstruido y contiene coeficientes aproximados.

Usar aquí caliQ=100 por costumbre sería un error si el archivo se comprimió
con 50 o 500. Debe utilizarse el valor guardado, no una preferencia nueva
del usuario del descompresor.
''')
block('imidct: deshacer la transformación y el centrado','jdes_custom.m',205,206,r'''
imidct recibe los coeficientes aproximados y las dimensiones originales.
Separa los tres planos, aplica $T^{\mathsf T}FT$ por bloques y suma 128
para invertir el centrado de imdct. Xamprec vuelve a contener muestras
espaciales, ya no coeficientes de frecuencia.

Su espacio de color sigue siendo YCbCr, porque las transformaciones se
aplicaron a esos planos. La implementación local no recorta aunque reciba
m y n: conserva mamp por namp por 3. Esos argumentos se utilizan en el
mensaje informativo. No debe deducirse del texto mostrado que la matriz
ya tiene el tamaño original; el recorte aparece expresamente más adelante.
''')
block('Descomponer la conversión a RGB en operaciones sencillas','jdes_custom.m',208,209,r'''
La expresión anidada se entiende desde dentro hacia fuera. Primero
Xamprec/255 cambia la escala numérica a la convención double usada por
ycbcr2rgb. Dividir una matriz por un escalar equivale aquí a dividir cada
muestra. La función de color convierte los planos YCbCr a canales RGB.

Después se multiplica por 255 para volver a la escala de 8 bits. round
redondea las muestras y uint8 las convierte a enteros sin signo de un byte,
con saturación para los valores fuera de 0 a 255. La salida Xrgb es una
imagen RGB de 8 bits, todavía ampliada.

Estas multiplicaciones por 255 no son la cuantización DCT ni una ganancia
de calidad. Adaptan la escala entre representaciones de imagen. Los redondeos
o saturaciones finales también pueden aportar pequeñas diferencias respecto
al RGB original, además de las provocadas por la cuantización.
''')
block('Recortar el borde y escribir un BMP real','jdes_custom.m',211,215,r'''
Xrgb(1:m,1:n,:) conserva filas desde 1 hasta m, columnas desde 1 hasta n
y todos los planos. Las filas y columnas de ampliación estaban al final;
por eso basta seleccionar esa región. Si las dimensiones ya eran múltiplos
de ocho, la selección conserva toda la matriz.

Xrec es la imagen final de tamaño original. imwrite recibe esa matriz,
archivoSalida y el formato bmp. Guardar con extensión bmp y especificar el
formato garantiza que se escribe una imagen BMP, no un volcado de bytes
comprimidos con un nombre nuevo.

Se guarda Xrec, no Xrgb ampliada ni Xamprec en YCbCr. Se conserva la matriz
en memoria porque a continuación se compara muestra a muestra con X.
''')
sec('Medir calidad, medir tamaño y mostrar resultados')
block('MSE: calcular sin errores de tipo ni de dimensiones','jdes_custom.m',217,220,r'''
La primera instrucción convierte ambas imágenes a double antes de restar.
Si se restaran como uint8, las diferencias negativas no se representarían
correctamente. Por ejemplo, 20-30 debe dar -10, no un valor saturado.

El operador .\^{}2 eleva cada diferencia al cuadrado. El punto significa
operación elemento a elemento, a diferencia de una potencia matricial.
Una diferencia -10 y una +10 aportan ambas 100; las diferencias no se cancelan.

erroresCuadrados(:) coloca todas las filas, columnas y canales en un solo
vector. mean calcula su media, equivalente a sumar todo y dividir por 3mn.
No se promedia solo el canal Y ni se usa el tamaño del archivo. MSE tiene
unidades de nivel de muestra al cuadrado y no es un porcentaje.

Ejemplo con errores 0, 2 y -1: los cuadrados son 0, 4 y 1, y MSE=5/3.
MSE cero indica igualdad de muestras; un resultado positivo no demuestra
por sí solo un error de Huffman, porque la cuantización es con pérdida.
Para aislar Huffman se comparan etiquetas, como explica el capítulo de pruebas.
''')
block('RC: una métrica distinta del error de imagen','jdes_custom.m',222,223,r'''
Se utiliza TO de la cabecera y TC medido al abrir el archivo. El tamaño del
BMP recién reconstruido no interviene. TO-TC es la cantidad ahorrada; al
dividir entre TO se obtiene una proporción y al multiplicar por 100, un porcentaje.

Si ambos procesos trabajan con el mismo .huc, RC debe coincidir con el valor
que devolvió el compresor. No depende de que la referencia elegida para
MSE sea visualmente correcta: ese es otro control. La coincidencia de RC
verifica la aritmética de tamaños, no la exactitud de las etiquetas.
''')
block('La figura y el final de la función','jdes_custom.m',226,237,r'''
figure abre una ventana de gráficos. subplot(1,2,1) la organiza en una fila
y dos columnas y activa la primera posición. imshow(X) dibuja el original;
title le asigna el texto que identifica ese panel.

subplot(1,2,2) activa la segunda posición. imshow(Xrec) dibuja el reconstruido
y title lo distingue del original. No se muestran Xlabrec ni coeficientes:
son imágenes RGB listas para visualización. La figura permite ver dónde
se pierde detalle, algo que un único MSE no localiza.

El end final cierra jdes\_custom. MSE y RC, ya asignados, se devuelven en el
orden declarado al principio; la imagen BMP permanece guardada. Los objetos
y variables locales restantes se liberan. La ventana gráfica puede seguir abierta.
''')
sec('Comprobar que puedes explicar cualquier línea')
p(r'''Al señalar una llamada a fread, debes decir cuántos elementos solicita,
cuántos bytes ocupa cada uno, qué tipo devuelve y dónde queda el puntero.
Al señalar una conversión de tipo, distingue si solo prepara cálculos
(double de uint32) o si discretiza y limita muestras (uint8 del RGB final).

Al señalar un control, explica qué error evita y qué no demuestra. La igualdad
de dimensiones no identifica una imagen; la cantidad correcta de bytes no
valida todos los códigos; una imagen parecida no demuestra igualdad de etiquetas.
Al señalar un end, identifica si cierra un if, un for o una función.

El recorrido de vuelta se resume así: ``Interpreto metadatos; leo diccionarios
y flujos; deshago empaquetado; reconozco símbolos y amplitudes; recupero
etiquetas; restauro posiciones; aproximo coeficientes; reconstruyo muestras;
convierto y recorto; evalúo''. Cada verbo corresponde a una responsabilidad
concreta del código, no a una promesa de recuperar información ya descartada.
''')
des='\n'.join(chunks)

a=s.index(r'\chapter{Compresión: del diario al código real}')
b=s.index(r'\chapter{El contrato binario del archivo .huc}')
s=s[:a]+comp+'\n'+s[b:]
a=s.index(r'\chapter{Descompresión: reconstruir y evaluar}')
b=s.index(r'\chapter{Ejemplo resuelto y seguimiento de variables}')
s=s[:a]+des+'\n'+s[b:]
s=s.replace('BITS(2)=2, BITS(3)=2 y los demás recuentos cero;', 'BITS(2)=2 y BITS(3)=2; los demás recuentos valen cero.')
s=s.replace('15 de noviembre de 2026','15 de noviembre de 2026 · Edición ampliada')
s=s.replace('Teoría desde cero, explicación del código', 'Teoría desde cero y lectura detallada del código')
# Limit the contents to chapter and section headings: detailed blocks remain bookmarked.
s=s.replace(r'\tableofcontents',r'\setcounter{tocdepth}{1}'+'\n'+r'\tableofcontents')
target=root/'output/pdf/guia_ejercicio2_ampliada.tex'
target.write_text(s,encoding='utf-8')
print('Expanded source:',len(s),'characters')
print('Chapter 3:',len(comp.split()),'words; Chapter 5:',len(des.split()),'words (including source code)')
