from pathlib import Path
import re, unicodedata

root=Path.cwd()
out=root/'output/pdf'
parts=[]
def add(s): parts.append(s)
def section(title,text): add('\\section{'+title+'}\n'+text+'\n')
def sub(title,text): add('\\subsection{'+title+'}\n'+text+'\n')
def code(s): add('\\begin{lstlisting}\n'+s.strip()+'\n\\end{lstlisting}\n')
def ref(file,needle):
    lines=(root/file).read_text(encoding='utf-8-sig').splitlines()
    n=next(i+1 for i,s in enumerate(lines) if needle in s)
    return r'\texttt{'+file.replace('_',r'\_')+r'}, línea '+str(n)+r' (apéndice \ref{src:'+file+r'}).'

add(r'''\documentclass[11pt,a4paper,oneside]{report}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[spanish,es-nodecimaldot]{babel}
\usepackage[margin=25mm,headheight=15pt]{geometry}
\usepackage{amsmath,amssymb,booktabs,longtable,array,listings,fancyhdr}
\usepackage[hidelinks]{hyperref}
\hypersetup{pdftitle={Guía de estudio: jcom custom y jdes custom},pdfauthor={Material de estudio de la práctica 4}}
\setlength{\parskip}{6pt}
\setlength{\parindent}{0pt}
\setlength{\emergencystretch}{3em}
\renewcommand{\baselinestretch}{1.08}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small Compresión multimedia | Práctica 4}
\fancyhead[R]{\small Guía de estudio}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\lstset{basicstyle=\ttfamily\scriptsize,columns=fullflexible,keepspaces=true,
breaklines=true,breakatwhitespace=false,showstringspaces=false,
numbers=left,numberstyle=\tiny,numbersep=8pt,frame=single,rulecolor=\color{black},
keywordstyle=\bfseries,commentstyle=\itshape,tabsize=4,
aboveskip=10pt,belowskip=10pt}
\usepackage{xcolor}
\begin{document}
\begin{titlepage}
\vspace*{12mm}
{\large COMPRESIÓN MULTIMEDIA\par}
\vspace{4mm}{\large Práctica 4 · Ejercicio 2\par}
\vspace{17mm}\hrule\vspace{9mm}
{\Huge\bfseries Compresión de imágenes\par}
\vspace{3mm}{\huge con Huffman a medida\par}
\vspace{9mm}\hrule
\vspace{12mm}{\Large Comprender \texttt{jcom\_custom}\par
y \texttt{jdes\_custom}\par}
\vspace{10mm}
{\large Teoría desde cero, explicación del código\par
y preparación de la defensa oral\par}
\vfill
\begin{minipage}{0.9\textwidth}
Guía elaborada a partir del diario de desarrollo y del código
real del proyecto. Incluye el formato binario, ejemplos resueltos,
comprobaciones y los cuatro archivos principales con líneas numeradas.
\end{minipage}
\vspace{13mm}\par
15 de noviembre de 2026
\end{titlepage}
\pagenumbering{roman}
\chapter*{Cómo estudiar esta guía}
\addcontentsline{toc}{chapter}{Cómo estudiar esta guía}
No necesitas memorizar todas las líneas. Debes poder explicar qué información
entra en cada etapa, qué sale, por qué se hace y qué función la ejecuta.
Lee primero los capítulos 1 y 2; después sigue el compresor y el descompresor
con los listados del apéndice abiertos. Por último, resuelve los ejemplos y
contesta las preguntas sin mirar la respuesta.

La numeración de pasos del diario no siempre coincide con los comentarios
del código: algunas etapas del diario ocurren dentro de una auxiliar.
Esta guía conserva esa distinción y proporciona referencias a líneas reales.
Las referencias corresponden a la copia del proyecto consultada al generar
este documento; si editas los archivos, sus líneas pueden cambiar.

El objetivo es que comprendas y puedas explicar tus decisiones con tus propias
palabras. Distingue lo implementado por ti de las auxiliares suministradas
por la librería. La prueba comunicada por el estudiante se presenta como tal;
no equivale a una nueva ejecución de MATLAB ni a una validación exhaustiva.
\tableofcontents
\clearpage\pagenumbering{arabic}
\chapter{El problema y el recorrido completo}
''')
section('Qué construye el ejercicio',r'''
Construyes un compresor con pérdida para imágenes y un descompresor compatible.
El compresor transforma la imagen, cuantiza los coeficientes y codifica las
etiquetas resultantes con tablas Huffman calculadas para esa imagen.
El archivo obtenido utiliza tu propio contenedor \texttt{.huc}. No es un
archivo JPEG estándar: comparte ideas de JPEG, pero no implementa sus
marcadores ni toda su estructura de intercambio.

\texttt{jcom\_custom(fname,caliQ)} recibe la ruta de una imagen, produce
\texttt{comprimido.huc} y devuelve el ahorro porcentual RC.
\texttt{jdes\_custom(fname)} recibe la ruta del comprimido, produce
\texttt{comprimido\_des\_cus.bmp} y devuelve MSE y RC.
El nombre fijo de salida es una decisión de tu implementación: una nueva
ejecución puede sobrescribir el resultado anterior.
''')
section('Mapa de ida y vuelta',r'''
\begin{center}\begin{tabular}{p{.43\textwidth}p{.43\textwidth}}
\toprule Compresión & Descompresión \\\midrule
RGB original & Bytes y tablas del .huc\\
YCbCr y ampliación & Desempaquetado de bytes\\
DCT por bloques & Decodificación Huffman\\
Cuantización & Etiquetas en zigzag\\
Zigzag & Zigzag inverso\\
DC diferencial y AC con rachas & Descuantización\\
Frecuencias y Huffman canónico & DCT inversa y suma de 128\\
Codificación y empaquetado & Conversión a RGB y recorte\\
Cabecera, tablas y bytes en .huc & BMP reconstruido, MSE y RC\\\bottomrule
\end{tabular}\end{center}
Las dos ramas no son inversas exactas en todos sus pasos. La cuantización
descarta precisión; la descuantización solo aproxima. En cambio, el zigzag,
la representación de símbolos, Huffman y el empaquetado deben ser reversibles.

\textbf{Idea central:} primero se obtiene una representación que admite
pérdida controlada; después se almacena esa representación sin perder nada más.
''')
section('Qué cambia frente a dflt',r'''
La lectura, conversión de color, DCT, cuantización, zigzag y reconstrucción
se mantienen. En \texttt{dflt}, las tablas Huffman son conocidas de antemano.
En \texttt{custom}, se calculan a partir de los símbolos de la imagen
ya cuantizada. Como el descompresor no puede adivinarlas, se guardan sus
especificaciones BITS/HUFFVAL dentro del archivo.

No se calculan las frecuencias de los píxeles RGB para esta codificación.
Se cuentan las categorías de las diferencias DC y los símbolos AC que
combinan racha y categoría. Tampoco se crean seis tablas: son cuatro,
porque Cb y Cr comparten las dos de crominancia.
''')
add(r'\chapter{La teoría mínima, entendida con ejemplos}')
section('Píxeles, componentes y bloques',r'''
Una imagen RGB de altura $m$ y anchura $n$ contiene tres números por píxel:
rojo, verde y azul. En la representación de 8 bits, cada muestra está entre
0 y 255. En MATLAB, $m$ es el número de filas y $n$ el número de columnas.

YCbCr separa una componente relacionada con el brillo (Y) de dos diferencias
de color (Cb y Cr). Esto permite tratar luminancia y crominancia con tablas
de cuantización distintas. Tu código conserva tres planos de igual tamaño:
\textbf{no realiza submuestreo 4:2:0 ni reduce espacialmente Cb o Cr}.

Cada componente se divide en bloques de $8\times8$. Si una dimensión no es
múltiplo de ocho, \texttt{imlee} replica el borde hasta completarla. Por ejemplo,
una imagen de $13\times10$ pasa a $16\times16$. Repetir el borde evita introducir
un salto artificial a cero. Se guardan las dimensiones originales para recortar
al final. El número de bloques por componente es
$N_b=(m_{amp}/8)(n_{amp}/8)$.
''')
section('Qué significa la DCT',r'''
La DCT expresa un bloque como combinación de 64 patrones de distinta frecuencia
espacial. Una frecuencia baja representa cambios suaves; una alta representa
alternancias rápidas, bordes y detalles. Los coeficientes indican cuánto
participa cada patrón. No son píxeles ni coordenadas.

El DC corresponde al patrón constante; está relacionado con el nivel medio.
Con la DCT ortonormal de esta librería, para un bloque centrado de media $a$,
el DC vale $8a$. Los otros 63 coeficientes son AC y describen variaciones.
Un bloque constante ideal tiene únicamente DC distinto de cero.

Si $T$ es la matriz DCT de orden 8 y $B$ un bloque de muestras,
\[
F=T(B-128)T^{\mathsf T},\qquad
\widehat B=T^{\mathsf T}\widehat F T+128.
\]
Restar 128 centra la señal alrededor de cero; no es una cuantización.
La DCT es invertible en aritmética exacta. El ahorro aparece sobre todo
cuando cuantizamos y muchos coeficientes pequeños se convierten en cero.
''')
section('Cuantizar no es aplicar Huffman',r'''
Cada posición DCT tiene su propio escalón $Q(u,v)$. La librería calcula
\[
Q=\max\!\left(\operatorname{round}(Q_{base}\,caliQ/100),1\right)
\]
elemento a elemento. Después \texttt{quant88} aplica exactamente
\[
L(u,v)=\left\lfloor \frac{F(u,v)}{Q(u,v)}+0.5\right\rfloor.
\]
No es simplemente truncar ni multiplicar el coeficiente por caliQ.
\texttt{floor} redondea hacia menos infinito después de sumar 0,5.
En los empates negativos puede diferir de \texttt{round} de MATLAB:
$\lfloor-1.5+0.5\rfloor=-1$.

Por ejemplo, con $F=37$ y $Q=10$, la etiqueta es 4. Al descuantizar obtenemos
$\widehat F=4\cdot10=40$, no 37. Con $F=3$ y $Q=10$, la etiqueta es cero.
Varios valores producen la misma etiqueta: esa información ya no puede recuperarse.

Con caliQ=100 se usan las tablas base; con 50 los escalones suelen ser menores
y la calidad mayor; con 500 son mayores y suele haber más ceros y más pérdida.
\textbf{En esta práctica aumentar caliQ no significa aumentar la calidad}.
No debe confundirse con el selector habitual de calidad de un editor JPEG.
''')
section('Zigzag: cambiar el orden, no los valores',r'''
El zigzag comienza en DC y visita después las posiciones AC de frecuencias
progresivamente más altas, siguiendo diagonales. No ordena los coeficientes
por su valor numérico. Como muchas frecuencias altas quedan a cero tras
cuantizar, tienden a aparecer rachas largas de ceros al final del recorrido.

Tu \texttt{scan} conserva el tamaño tridimensional: reorganiza cada bloque
para poder leer por filas la secuencia zigzag. No devuelve directamente
una matriz de 64 columnas. \texttt{CollectScan} extrae cada bloque y lo convierte
en un vector; \texttt{invscan} deshace la permutación al reconstruir.
''')
section('Categoría C y posición P',r'''
Huffman no codifica directamente todos los enteros con signo. Se representa
un valor $v$ mediante categoría y posición:
\[
C=\lceil\log_2(|v|+1)\rceil,\qquad
P=\begin{cases}v,&v\geq0,\\2^C-1+v,&v<0.\end{cases}
\]
Para valores no nulos, C indica cuántos bits de amplitud se necesitan.
La categoría 0 corresponde al valor cero. P identifica el valor dentro de su
categoría; no es la posición del coeficiente en el bloque.

\begin{center}\begin{tabular}{rrrrl}\toprule
$v$ & C & P & Bits de P & Interpretación\\\midrule
0&0&0&ninguno&Valor cero\\
1&1&1&1&Positivo\\
-1&1&0&0&Negativo\\
5&3&5&101&Positivo\\
-5&3&2&010&Negativo\\\bottomrule
\end{tabular}\end{center}
El signo está implícito en estos bits; no se añade un bit de signo independiente
ni se utiliza complemento a dos. Para $C>0$, si $P<2^{C-1}$, el valor es
$P-(2^C-1)$; en caso contrario es P. Para C=0 se recupera cero sin leer amplitud.
''')
section('DC diferencial y rachas de AC',r'''
Para los DC se codifica la diferencia respecto al bloque anterior del mismo
plano. Si los DC son 80, 83 y 79, se representan 80, 3 y -4. El primer
DC se resta de cero. Al decodificar se acumulan las diferencias y se recuperan
80, 83 y 79. Esta operación no pierde información y suele producir valores
menores, con categorías más pequeñas. La referencia se reinicia para cada componente.

En los AC se cuenta la cantidad Z de ceros antes de un valor no nulo y se
combina con su categoría C mediante $s=16Z+C$. Por ejemplo, tres ceros
seguidos de -5 producen $Z=3$, $C=3$, $s=51$ y $P=2$ (010).
Huffman representa 51 y después se añaden los tres bits de P. Si solo
contáramos C, perderíamos la cantidad de ceros.

EOB es el símbolo 0, equivalente a Z=0,C=0: cierra el bloque y deja a cero
los AC restantes. ZRL es 240, equivalente a Z=15,C=0, y representa 16 ceros.
No es un AC de valor 240. Una racha de 20 ceros antes de un valor se representa
con ZRL y luego un símbolo con Z=4. En tu \texttt{zercatpos} se añade un EOB
a todos los bloques para simplificar el recorrido, incluso si no quedan ceros finales.
''')
section('Huffman canónico y las cuatro familias de tablas',r'''
Un código prefijo permite reconocer cada palabra sin separadores: ninguna
palabra válida es prefijo de otra. Huffman combina repetidamente los dos
pesos menores para obtener longitudes que favorecen los símbolos frecuentes.
La implementación adapta las longitudes a un máximo de 16 bits.

\texttt{HSpecTables} añade temporalmente el símbolo 256 con frecuencia 1
para reservar el código formado solo por unos. Ese símbolo no pertenece
a los datos y se excluye del HUFFVAL final. \texttt{AdjustBits} ajusta longitudes
y retira el punto reservado. No necesitas guardar un árbol de punteros.

BITS cuenta códigos por longitud. HUFFVAL enumera los símbolos en el orden
de asignación. Con ambas listas, el algoritmo canónico comienza en cero,
incrementa el código dentro de una longitud y desplaza a la izquierda cuando
pasa a una longitud mayor. Se reproducen los mismos códigos sin guardar frecuencias.

Ejemplo didáctico: BITS(2)=2, BITS(3)=2 y los demás recuentos cero;
HUFFVAL=[10,20,30,40]. Se asignan 00, 01, 100 y 101 respectivamente.
Para consultar el símbolo 30, la tabla de codificación guarda el número 4
y la longitud 3. Si el código fuera 001, guardar solo el número 1 perdería
sus ceros iniciales; de ahí la necesidad de conservar también la longitud.
''')
add(r'\chapter{Compresión: del diario al código real}')
section('Pasos 1 y 2 del diario: contrato y lectura',ref('jcom_custom.m','validateattributes(caliQ')+r'''
\texttt{validateattributes} exige caliQ numérico, escalar, real, finito, entero
y positivo. \texttt{dir(fname)} devuelve información del archivo; su campo
\texttt{bytes} se guarda en TO. El código supone que fname identifica un archivo
válido: no contiene aquí el mismo control explícito con isfile que el descompresor.

\texttt{imlee} devuelve X en RGB y Xamp en YCbCr con bordes replicados.
También devuelve tipo, m, n, mamp y namp. Algunas salidas no se usan después
en el compresor, pero permiten observar el resultado de la preparación.
No se guarda la matriz X en el .huc. El tamaño TO se conserva para RC,
no para reconstruir los píxeles.
''')
section('Pasos 3 a 5: DCT, cuantización y scan',ref('jcom_custom.m','Xtrans = imdct')+r'''
La secuencia tiene una dependencia estricta: DCT recibe Xamp; quantmat recibe
Xtrans; scan recibe Xlab. Aplicar scan antes de cuantizar o pasar X RGB a imdct
rompería el significado del flujo previsto.
''')
code('Xtrans = imdct(Xamp);\nXlab = quantmat(Xtrans, caliQ);\nXScan = scan(Xlab);')
add(r'''
Las tres matrices tienen tamaño $m_{amp}\times n_{amp}\times3$, pero su significado
cambia. Xtrans contiene coeficientes reales; Xlab, etiquetas enteras con signo;
XScan, las mismas etiquetas permutadas por bloque. La forma de una matriz
no basta para saber qué representa: el punto del flujo determina su interpretación.
''')
section('Paso 6: recoger símbolos dentro de EncodeScans\_custom',ref('EncodeScans_custom.m','YScan  =')+r'''
El índice \texttt{(:,:,1)} selecciona todas las filas y columnas del primer plano.
Los planos 2 y 3 son Cb y Cr. Se aplica CollectScan por separado para que cada
componente tenga su referencia DC inicial independiente.

Cada DC\_CP tiene dos columnas: C y P, con una fila por bloque. Cada AC\_ZCP
tiene dos columnas: símbolo ZCdec y P; su número de filas depende de las rachas
y valores no nulos. El nombre ZCP no implica tres columnas en esta versión:
Z y C ya están empaquetados en el primer valor.

CollectScan recorre bloques de izquierda a derecha y de arriba abajo. La expresión
\texttt{reshape((bloque)',1,64)} lee por filas mediante transposición porque
MATLAB normalmente recorre los elementos por columnas. El mismo convenio se
utiliza al reconstruir; cambiarlo solo en un lado desordenaría las etiquetas.
''')
section('Paso 7: las cuatro frecuencias',ref('EncodeScans_custom.m','FREQ_Y_DC =')+r'''
\texttt{(:,1)} extrae los símbolos y excluye P. Los símbolos de Cb y Cr se
concatenan verticalmente mediante punto y coma antes de llamar a Freq256.
Se obtiene la frecuencia conjunta; no se promedian probabilidades normalizadas.
''')
code('FREQ_Y_DC = Freq256(Y_DC_CP(:,1));\nFREQ_Y_AC = Freq256(Y_AC_ZCP(:,1));\nFREQ_C_DC = Freq256([Cb_DC_CP(:,1); Cr_DC_CP(:,1)]);\nFREQ_C_AC = Freq256([Cb_AC_ZCP(:,1); Cr_AC_ZCP(:,1)]);')
add(r'''
Freq256 devuelve 256 recuentos. El símbolo s ocupa la posición s+1 por los
índices de MATLAB. La suma de FREQ\_Y\_DC debe ser el número de bloques de Y;
la de FREQ\_C\_DC, la suma de bloques de Cb y Cr. Las frecuencias AC cuentan
símbolos de la representación, incluidos EOB y ZRL, no los 63 coeficientes
individuales de cada bloque.
''')
section('Pasos 8 y 9: especificaciones y tablas de consulta',ref('EncodeScans_custom.m','HSpecTables(FREQ_Y_DC)')+r'''
Se llama cuatro veces a HSpecTables. Después, para cada familia,
HCodeTables produce HUFFSIZE y HUFFCODE y HCodingTables los reorganiza por símbolo.
\texttt{ehuf=[EHUFCO EHUFSI]} tiene 256 filas y dos columnas: número del código
y longitud. El símbolo s se consulta en \texttt{ehuf(s+1,:)}.

Es importante distinguir cuatro órdenes: FREQ se indexa por símbolo;
BITS por longitud; HUFFVAL/HUFFCODE/HUFFSIZE por orden de asignación;
EHUFCO/EHUFSI vuelven a indexarse por símbolo. No son vectores intercambiables.
Una longitud cero en EHUFSI significa que un símbolo no tiene código; un valor
numérico de código cero puede ser perfectamente válido si su longitud es positiva.
''')
section('Paso 10: tres secuencias binarias',ref('EncodeScans_custom.m','CodedY = EncodeSingleScan')+r'''
EncodeSingleScan recorre los bloques y añade el código de la categoría DC,
la posición del DC y los símbolos AC con sus posiciones. Y usa sus dos tablas;
Cb y Cr comparten las de crominancia. Se devuelve una secuencia por plano.
Las secuencias son vectores de caracteres de MATLAB, no bytes comprimidos todavía.

La auxiliar devuelve además ocho vectores, los cuatro pares BITS/HUFFVAL.
Las frecuencias y las matrices ehuf no se devuelven al archivo porque pueden
reemplazarse por estas especificaciones compactas. El compresor principal
coordina las etapas; EncodeScans\_custom concentra la construcción y uso de Huffman.
''')
section('Paso 11: bytes y bits válidos',ref('jcom_custom.m','bits2bytes(CodedY)')+r'''
bits2bytes agrupa ocho caracteres, interpreta su valor binario y guarda un
uint8. El indicador ultl es la longitud residual módulo 8: 0 si no hay resto;
1 a 7 si el último byte tiene solo esos bits válidos. El comentario antiguo
de la auxiliar menciona 1 a 8, pero su implementación devuelve 0 a 7.

Para una longitud original $b$, se almacenan $L=\lceil b/8\rceil$ bytes.
Si ultl es positivo, $b=8(L-1)+ultl$; si vale cero, $b=8L$.
Por ejemplo, 11 bits necesitan 2 bytes y ultl=3. Los cinco ceros de relleno
no se cuentan como datos. numel calcula la cantidad de elementos de bytesY,
que ya coincide con su cantidad de bytes almacenados.
''')
section('Paso 12 y corrección de BITS',ref('jcom_custom.m','b = tablasBITS{k}')+r'''
Antes de convertir campos a uint32 se comprueba su rango. Este tipo admite
enteros de 0 a $2^{32}-1$; convertir sin validar podría saturar y perder información.
Los cuatro BITS y HUFFVAL se agrupan en celdas: los HUFFVAL no tienen por qué
tener igual longitud. Los corchetes concatenan; las llaves crean celdas y
\texttt{tablasBITS\{k\}} extrae el contenido de la celda k.

La primera prueba detectó una suposición incorrecta: AdjustBits recorta BITS
hasta la mayor longitud que conserva, por lo que puede devolver menos de
16 elementos. La corrección transforma b en columna con \texttt{b(:)} y añade
ceros al final hasta 16. Esto no añade códigos ni cambia los existentes.
Se valida que no supere 16 y que $\sum BITS=\operatorname{numel}(HUFFVAL)$.
Se normaliza solo la copia destinada al archivo; los códigos ya construidos
siguen siendo equivalentes.
''')
section('Pasos 13 y 14: escribir y devolver RC',ref('jcom_custom.m',"fid = fopen")+r'''
fopen devuelve un identificador de archivo o -1 si falla. El modo wb escribe
binario y puede sobrescribir; ieee-le selecciona little-endian. fwrite devuelve
elementos escritos, no bytes: se multiplica por 4 para uint32 y por 2 para uint16.
Para uint8 ambos recuentos coinciden.

Se acumulan los bytes y se comparan con TCprevisto. El bloque try/catch
cierra el descriptor si falla la escritura y rethrow conserva el error.
En la ruta correcta se comprueba también el resultado de fclose. Solo después
se mide el archivo con dir y se calcula RC. El tamaño de los datos binarios
por sí solo no sería suficiente: también hay que pagar la cabecera y las tablas.
''')
add(r'\chapter{El contrato binario del archivo .huc}')
section('Campos, tipos y orden',r'''
El formato se interpreta por posición: no se escriben los nombres de variables
ni separadores de texto. Compresor y descompresor deben compartir el contrato.
\begin{center}\begin{tabular}{p{.24\textwidth}p{.27\textwidth}p{.35\textwidth}}
\toprule Campo & Tipo y tamaño & Interpretación\\\midrule
m, n, caliQ, TO & 4 uint32; 16 bytes & Datos generales\\
BITS Y\_DC & 16 uint16; 32 bytes & Recuentos por longitud\\
HUFFVAL Y\_DC & $N_1$ uint8 & Símbolos, $N_1=\sum BITS$\\
BITS/HUFFVAL Y\_AC & 32+$N_2$ bytes & Segunda especificación\\
BITS/HUFFVAL C\_DC & 32+$N_3$ bytes & Tercera especificación\\
BITS/HUFFVAL C\_AC & 32+$N_4$ bytes & Cuarta especificación\\
LY, ultlY, bytesY & uint32, uint8, LY uint8 & Flujo de Y\\
LCb, ultlCb, bytesCb & Igual estructura & Flujo de Cb\\
LCr, ultlCr, bytesCr & Igual estructura & Flujo de Cr\\\bottomrule
\end{tabular}\end{center}
El primer BITS comienza en el desplazamiento 16, contando el inicio del archivo
como cero. El primer HUFFVAL comienza en el 48. A partir de ahí los desplazamientos
dependen del número de símbolos de cada tabla. Por eso el lector obtiene primero
BITS y luego lee exactamente su suma de símbolos.
''')
section('Por qué se eligieron esos tipos',r'''
Los símbolos van de 0 a 255: caben en uint8. BITS se guarda en uint16 para
admitir recuentos de hasta 256. Las dimensiones y longitudes pueden superar
255 e incluso 65535; se usa uint32. Los indicadores ultl solo necesitan 0 a 7.
El formato usa bytes enteros aunque algunos rangos podrían codificarse con menos bits:
es una elección de simplicidad, no un mínimo teórico.

Little-endian significa que un entero multibyte guarda primero el byte menos
significativo. Por ejemplo, uint16(258) se escribe como 02 01 en hexadecimal.
No significa invertir los bits de los códigos Huffman. El orden de bytes de
los campos y el orden de los caracteres del flujo son asuntos distintos.
''')
section('Tamaño total y límites del formato',r'''
Si $N_k$ es la cantidad de símbolos de la tabla k, el tamaño esperado es
\[
TC=159+\sum_{k=1}^{4}N_k+L_Y+L_{Cb}+L_{Cr}.
\]
Los 159 bytes fijos son $16+128+15$: cabecera, cuatro BITS y tres parejas
longitud/indicador. Los HUFFVAL y los flujos tienen tamaño variable.

No se guardan ni X, ni frecuencias, ni árbol Huffman, ni nombre del original.
Las dimensiones ampliadas se deducen de m y n. TO permite RC, y caliQ permite
reconstruir los escalones de cuantización. No hay firma, versión ni suma de
comprobación. Las validaciones detectan varias inconsistencias, pero no toda
corrupción posible: un archivo arbitrario no queda validado solo por su extensión.
''')
add(r'\chapter{Descompresión: reconstruir y evaluar}')
section('Pasos 1 y 2: archivo y referencia original',ref('jdes_custom.m','if ~isfile(fname)')+r'''
Se comprueba que exista fname y se mide TC. Después se solicita el original
con input y la opción s, que recibe texto sin evaluarlo como una expresión.
imlee proporciona X, mOriginal y nOriginal. Los símbolos tilde descartan
salidas que no se necesitan. Se exige RGB de 8 bits para comparar muestras.

\textbf{El original no interviene en la decodificación de los datos.} Esta función
lo pide porque también evalúa y visualiza el resultado. Si quisiéramos un
decodificador independiente, separaríamos esa evaluación. Coincidir en dimensiones
no demuestra que se haya seleccionado la misma imagen; es responsabilidad del
usuario elegir la referencia correcta.
''')
section('Paso 3: abrir, leer y recuperar dimensiones',ref('jdes_custom.m','cierreArchivo =')+r'''
El modo rb lee binario y utiliza el mismo little-endian del escritor.
onCleanup crea un objeto cuya destrucción llama a fclose. Si un error abandona
la función, el objeto cierra el archivo. Más adelante, clear cierreArchivo
lo destruye explícitamente una vez terminada la lectura. No se debe cerrar
por duplicado el mismo descriptor.

fread(fid,4,'*uint32') solicita cuatro elementos y conserva su tipo.
Se comprueba que llegaron todos antes de acceder a ellos. Después se convierten
a double para cálculos: m, n, caliQ y TO deben ser positivos.
La ampliación se recalcula con $8\lceil m/8\rceil$ y $8\lceil n/8\rceil$.
Una dimensión que ya sea múltiplo de ocho permanece igual.
''')
section('Paso 4: reconstruir el contenido de las especificaciones',ref('jdes_custom.m',"b = fread")+r'''
El bucle de cuatro iteraciones lee 16 uint16 de BITS y luego sum(BITS) uint8
de HUFFVAL. Los convierte a double para las auxiliares. Se verifica que haya
entre 1 y 256 símbolos y que no se repitan. unique elimina duplicados para
poder comparar su cantidad con la esperada.

Se guardan primero en celdas y luego se asignan nombres Y\_DC, Y\_AC, C\_DC
y C\_AC. Es la misma información adaptada a la interfaz de DecodeScans\_custom.
No se reconstruyen frecuencias: múltiples distribuciones podrían producir
los mismos códigos, y para decodificar bastan sus especificaciones.
''')
section('Paso 5: leer los tres flujos',ref('jdes_custom.m',"nombres =")+r'''
Para cada plano se lee una longitud uint32, un indicador uint8 y esa cantidad
de bytes. isempty detecta la ausencia de un campo. ultl no puede superar 7;
la longitud debe ser positiva y no superar $TC-ftell(fid)$, los bytes restantes.
El número de elementos efectivamente leídos debe coincidir con lo solicitado.

ftell devuelve la posición en bytes desde el comienzo. Al terminar se exige
ftell(fid)=TC, por lo que no quedan datos adicionales fuera del contrato.
Esto comprueba la estructura externa, no que cada código Huffman sea válido.
Se extraen bytesY, bytesCb, bytesCr y sus indicadores, y se cierra el archivo
mediante clear cierreArchivo. Las matrices ya leídas permanecen en memoria.
''')
section('Paso 6: deshacer el empaquetado',ref('jdes_custom.m','CodedY  = bytes2bits')+r'''
bytes2bits convierte cada número a una representación de exactamente ocho
bits, preservando ceros iniciales, concatena por filas y recorta únicamente
si ultl es positivo. El flujo vuelve a ser un vector de caracteres.
No se pueden eliminar todos los ceros finales: algunos podrían ser datos.
Por ejemplo, el byte 160 representa 10100000; con ultl=3 recuperamos 101,
y con ultl=0 recuperamos los ocho bits completos.
''')
section('Paso 7: preparar DecodeScans\_custom',ref('DecodeScans_custom.m','HCodeTables(BITS_Y_DC')+r'''
Se reconstruyen HUFFCODE con HCodeTables para las cuatro familias. El tilde
descarta HUFFSIZE porque no se necesita después. HDecodingTables produce
MINCODE, MAXCODE y VALPTR por longitud. Para longitudes sin códigos, MAXCODE
vale -1. No se utiliza HufDecodTables\_dflt, porque cargaría otras tablas.

DecodeWord mantiene un puntero ptr al siguiente bit. Empieza con un bit y
amplía el código mientras su valor supera MAXCODE de la longitud actual.
Una vez reconocido, calcula el índice de HUFFVAL:
\[
j=VALPTR(i)+code-MINCODE(i).
\]
Devuelve el símbolo y el puntero situado justo después de su palabra.
Los bits de posición se leen a continuación según la categoría recuperada.
''')
section('Paso 8: reconstruir etiquetas por componente',ref('DecodeScans_custom.m','YScanrec = DecodeSingleScan')+r'''
DecodeSingleScan recibe la secuencia, las tablas DC/AC y tam=[mamp namp].
Inicializa cada bloque con ceros y DCprevio con cero por componente. Recupera
la diferencia DC mediante categoría y posición y la suma al DC previo.
Para los AC acumula ceros indicados por ZRL y Z, coloca el valor no nulo y
continúa hasta EOB. Lo que queda en el bloque permanece a cero.

Las tres matrices resultantes se reúnen con cat(3,...), en orden Y, Cb, Cr.
XScanrec todavía contiene etiquetas en la distribución zigzag de la librería.
El comentario del código principal salta de PASO 6 a PASO 8: el paso 7 del
diario se realiza dentro de la auxiliar, no falta una transformación.
''')
section('Pasos 9 a 11: del zigzag a las muestras',ref('jdes_custom.m','Xlabrec = invscan')+r'''
invscan devuelve cada etiqueta a su posición de frecuencia en el bloque.
desquantmat reconstruye las mismas tablas QY y QC con caliQ y multiplica
elemento a elemento. Obtiene coeficientes aproximados, no los originales exactos.
imidct aplica $T^{\mathsf T}\widehat F T$ por bloques y añade 128.

Aunque imidct recibe m y n, su código no recorta la salida: los usa en el
mensaje de información. Xamprec conserva las dimensiones ampliadas y sigue
en YCbCr. Algunos comentarios heredados de las auxiliares dicen RGB o tamaño
original; hay que atender a las operaciones reales, no asumir que todo comentario
describe exactamente la implementación actual.
''')
section('Paso 12: RGB, recorte y BMP',ref('jdes_custom.m','Xrgb = uint8')+r'''
La expresión divide las muestras por 255 para la convención double de la
conversión de color, transforma a RGB, vuelve a multiplicar por 255 y redondea.
uint8 convierte a muestras de 8 bits, con saturación en el intervalo de ese tipo.
No se está deshaciendo la cuantización mediante esta multiplicación por 255:
solo se cambia la escala de representación de las muestras.

\texttt{Xrgb(1:m,1:n,:)} elimina los bordes de ampliación. El símbolo dos puntos
en la tercera dimensión conserva los tres canales. imwrite guarda un BMP
real con el nombre fijo preparado al principio. La imagen final en memoria
es Xrec y se usa para evaluar, no Xamprec ni XScanrec.
''')
section('Pasos 13 a 15: MSE, RC y figura',ref('jdes_custom.m','errorImagen =')+r'''
MSE promedia los errores cuadrados de todas las muestras RGB:
\[
MSE=\frac{1}{3mn}\sum_{r=1}^m\sum_{c=1}^n
\sum_{k=1}^{3}\bigl(X(r,c,k)-Xrec(r,c,k)\bigr)^2.
\]
Se convierte a double antes de restar para no saturar las diferencias negativas.
El operador .\^{}2 eleva cada elemento; erroresCuadrados(:) forma un vector y
mean promedia todos sus elementos. MSE=0 significa igualdad muestra a muestra,
no es obligatorio en un compresor con cuantización. MSE no es un porcentaje.

RC se calcula como $100(TO-TC)/TO$. Un 97,80\% de ahorro significa que queda
el 2,20\% del tamaño del archivo original. No debe confundirse con el factor
TO/TC ni con $100TC/TO$. Una RC negativa indica expansión. No se utiliza
el tamaño del BMP reconstruido para calcularla.

figure crea la ventana; subplot(1,2,1) selecciona la izquierda y subplot(1,2,2)
la derecha. imshow recibe X o Xrec y title identifica cada una. El bloque debe
estar en jdes\_custom: sus variables locales no existen dentro de DecodeScans\_custom.
''')
add(r'\chapter{Ejemplo resuelto y seguimiento de variables}')
section('Un bloque sencillo de principio a fin',r'''
Considera un plano Y con un bloque constante de valor 138. Al centrarlo queda
10 en cada muestra. Su DCT ideal tiene DC=80 y todos los AC cero.
Con caliQ=100, QY(1,1)=16, por lo que la etiqueta DC es
$\lfloor80/16+0.5\rfloor=5$. Los AC siguen siendo cero.

En el primer bloque, la diferencia DC es 5-0=5; catpos produce C=3,P=5.
La representación AC solo necesita EOB. El flujo conceptual es:
\[
H_{Y,DC}(3)\;||\;101\;||\;H_{Y,AC}(0),
\]
donde $||$ significa concatenación y H indica el código de la tabla a medida.
No se pueden dar sus palabras concretas sin conocer las frecuencias del conjunto
de la imagen. Si fuera una imagen artificial de un único bloque, se calcularían
las tablas de ese caso particular.

Al decodificar, se obtiene la categoría 3, se leen 101 y se recupera 5.
Se suma la referencia DC inicial cero. EOB deja los 63 AC a cero. invscan
restaura posiciones y la descuantización devuelve DC=5 por 16=80.
La IDCT devuelve 10 y se suma 128: se recuperan las muestras Y=138 en este
ejemplo ideal. No demuestra que todo bloque se recupere exactamente: aquí
el DC era múltiplo del escalón. Con DC=83 también se etiquetaría como 5
y se reconstruiría 80. Además, el recorrido RGB/YCbCr y la conversión final
pueden aportar redondeos.
''')
section('Diccionario de las matrices principales',r'''
\begin{longtable}{p{.23\textwidth}p{.65\textwidth}}
\toprule Variable & Contenido y significado\\\midrule\endhead
X & Original RGB uint8, $m\times n\times3$; referencia del MSE.\\
Xamp & Muestras YCbCr double, ampliadas a múltiplos de 8.\\
Xtrans & Coeficientes DCT por bloque, con signo.\\
Xlab & Etiquetas cuantizadas, enteras aunque se almacenen como double.\\
XScan & Las mismas etiquetas reordenadas por bloque.\\
DC\_CP & Categoría y posición de diferencias DC; dos columnas.\\
AC\_ZCP & Símbolo ZCdec y posición; dos columnas.\\
FREQ & Recuentos absolutos; índice símbolo+1.\\
BITS & Recuentos de códigos por longitud.\\
HUFFVAL & Símbolos en orden de asignación de códigos.\\
ehuf & Código numérico y longitud por símbolo.\\
CodedY/Cb/Cr & Caracteres binarios anteriores al empaquetado.\\
bytesY/Cb/Cr & Valores uint8 listos para escribir.\\
XScanrec & Etiquetas recuperadas por Huffman, aún en zigzag.\\
Xlabrec & Etiquetas en sus posiciones DCT naturales.\\
Xtransrec & Coeficientes aproximados tras descuantizar.\\
Xamprec & Muestras YCbCr reconstruidas y ampliadas.\\
Xrgb & Imagen RGB uint8 todavía ampliada.\\
Xrec & Imagen RGB final, recortada a $m\times n\times3$.\\\bottomrule
\end{longtable}
''')
add(r'\chapter{Validación, errores y límites reales}')
section('Qué demuestra la prueba comunicada',r'''
El diario y la captura aportados recogen Img00.bmp con caliQ=100,
anchura 480 y altura 640, RCcomp=RCdes=97,80\% y MSE=34,546211.
Ambas dimensiones son múltiplos de ocho, por lo que no hubo ampliación.
Hay $80\cdot60=4800$ bloques por componente y 14400 entre los tres planos.

El resultado muestra que esa ejecución llegó al final, produjo una imagen
visualmente coherente y obtuvo RC compatibles. No verifica otras imágenes,
otras calidades, casos constantes ni dimensiones no múltiplos de ocho.
Tampoco se han vuelto a ejecutar aquí las funciones en MATLAB. La raíz del
MSE, aproximadamente 5,88 niveles de muestra, puede dar una escala del error,
pero no significa que todos los píxeles difieran esa cantidad.

Una RC tan alta respecto a un BMP puede ser razonable porque el BMP contiene
muchos datos sin compresión. No demuestra que el resultado supere a JPEG ni
que custom siempre mejore dflt. Si comprimes un JPEG de entrada, TO ya será
el tamaño de un archivo comprimido y la comparación tendrá otra referencia.
''')
section('La comprobación exacta de Huffman',r'''
La igualdad importante es $XScanrec=XScan$, no necesariamente $Xrec=X$.
Para comprobar la codificación sin implicar el archivo ni la cuantización inversa,
puedes ejecutar esta prueba en un script separado:
''')
code('''[~, Xamp] = imlee('Img00.bmp');
XScan = scan(quantmat(imdct(Xamp), 100));
[a, b, c, bydc, hydc, byac, hyac, bcdc, hcdc, bcac, hcac] = ...
    EncodeScans_custom(XScan);
rec = DecodeScans_custom(a, b, c, ...
    [size(XScan,1) size(XScan,2)], ...
    bydc, hydc, byac, hyac, bcdc, hcdc, bcac, hcac);
assert(isequal(XScan, rec), ...
    'La codificacion Huffman no recupera las etiquetas exactamente.');''')
add(r'''
Este script es una prueba propuesta, no un resultado ya obtenido. Para comprobar
también escritura, lectura y empaquetado, puede usarse el depurador de MATLAB:
detener el compresor después de scan, guardar XScan en una variable del espacio
base y detener el descompresor después de DecodeScans\_custom para comparar.
Es importante guardar la misma imagen y caliQ y no confundir las variables
locales de funciones diferentes.
''')
section('Un detalle de las auxiliares que conviene revisar',r'''
La intención JPEG y DecodeSingleScan establecen que C=0 no lleva bits de
posición; lo mismo sucede con ZRL. Sin embargo, la copia consultada de
EncodeSingleScan llama a \texttt{dec2bin(P,C)} sin una condición C>0 para
DC y para símbolos AC internos. No se debe dar por hecho que pedir ancho
cero produzca una cadena vacía: MATLAB puede devolver un carácter para el cero.
Si se añade un bit no esperado, se desincroniza el lector.

Esto no se ha corregido al generar la guía y no se afirma que haya fallado
en la ejecución comunicada. Es una limitación a verificar, especialmente con
bloques de DC repetidos y rachas ZRL. La forma conceptual robusta es añadir
los bits de P únicamente si C>0, manteniendo el mismo convenio en ambos lados.
El resultado exacto de etiquetas propuesto arriba permite detectar problemas
que una imagen visualmente parecida o la igualdad de RC no revelan.
''')
section('Errores encontrados durante el desarrollo',r'''
\textbf{BITS con menos de 16 posiciones.} No era un error del árbol: AdjustBits
recorta la cola. Se completó con ceros al serializar para mantener 32 bytes
por tabla. Cambiar solo el lector o solo el tamaño previsto habría roto el contrato.

\textbf{Variable X no reconocida.} Se había colocado la figura dentro de
DecodeScans\_custom. Cada función tiene su propio espacio de variables;
el bloque se trasladó a jdes\_custom, donde existen X y Xrec.

\textbf{Aviso OpenGL.} El cambio al renderizado por software afecta a la
visualización. No explica por sí mismo un error de variables o de Huffman.

\textbf{Cobertura limitada.} Las comprobaciones de tamaños, duplicados y rangos
no constituyen un validador completo de archivos malformados. Se asume el
formato producido por este proyecto. La implementación concatena vectores
en bucles y representa bits como texto en memoria, de modo que no está
optimizada para imágenes grandes.
''')
add(r'\chapter{Preparar la entrevista con el profesor}')
section('Explicación de dos minutos',r'''
\begin{quote}
Mi compresor empieza leyendo la imagen y convirtiéndola a YCbCr. Amplía los
bordes a múltiplos de ocho porque trabaja por bloques de 8 por 8. Aplica la DCT
para representar cada bloque mediante frecuencias y cuantiza los coeficientes;
esa es la etapa principal de pérdida.

Después reordena las etiquetas en zigzag. Representa los DC como diferencias
y los AC mediante rachas de ceros y categorías. Cuenta los símbolos y genera
cuatro tablas Huffman canónicas: DC y AC de Y, y DC y AC compartidas por Cb y Cr.
Codifica, empaqueta en bytes y escribe los metadatos, las especificaciones
Huffman y los tres flujos en un archivo propio .huc.

El descompresor lee ese contrato en el mismo orden, reconstruye las tablas,
recupera las etiquetas, deshace el zigzag, descuantiza y aplica la DCT inversa.
Convierte a RGB, recorta los bordes y guarda el BMP. Finalmente compara con
la imagen original para obtener el MSE y calcula el ahorro RC. Huffman debe
recuperar las etiquetas exactamente, aunque la imagen final difiera por la
cuantización y los redondeos.
\end{quote}
''')
qa=[
('¿Dónde se pierde información?', 'Principalmente al cuantizar: varios coeficientes se convierten en una misma etiqueta. La DCT, el zigzag y Huffman no están diseñados para introducir pérdida. Las conversiones de color y a uint8 también pueden introducir redondeos o saturación.'),
('¿Por qué no aplicas Huffman directamente a RGB?', 'Esta cadena busca una representación más favorable: la transformación concentra información, la cuantización genera ceros y DC diferencial y rachas reducen los símbolos a categorías útiles. Huffman se aplica a esos símbolos, no a intensidades originales.'),
('¿Cuantizas también el DC?', 'Sí. Se cuantizan las 64 posiciones del bloque, cada una con su escalón. DC no queda exento. Después se calculan diferencias entre las etiquetas DC de bloques sucesivos.'),
('¿Por qué cuatro tablas y no tres o seis?', 'Se separan DC y AC porque tienen alfabetos y estadísticas distintos. Y dispone de ambas tablas propias; Cb y Cr comparten las otras dos. Son cuatro familias para tres secuencias.'),
('¿Qué diferencia hay entre C y P?', 'C indica la cantidad de bits de amplitud; P selecciona el valor concreto, incluido su signo, dentro de esa categoría. Huffman codifica C para DC o ZCdec para AC; P se añade por separado.'),
('¿Qué significa BITS(3)=2?', 'Existen dos palabras de longitud tres. No dice que el símbolo 3 aparezca dos veces ni que su código tenga longitud dos. La frecuencia y el recuento por longitud son tablas diferentes.'),
('¿Cómo reconstruyes códigos sin guardar el árbol?', 'Guardo BITS y HUFFVAL. El algoritmo canónico asigna códigos de forma determinista según las longitudes y el orden de los símbolos. No necesita las frecuencias originales.'),
('¿El descompresor necesita la imagen original?', 'No para recuperar los datos del .huc. Mi función completa la solicita porque también calcula MSE y muestra la comparación. Son responsabilidades de evaluación que podrían separarse.'),
('¿Por qué guardas caliQ?', 'Porque el descompresor necesita reproducir los escalones QY y QC antes de multiplicar las etiquetas. No se puede descuantizar correctamente con un caliQ distinto.'),
('¿Por qué guardas TO si ya conoces m y n?', 'TO es el tamaño real del archivo de origen y permite calcular RC según el contrato. No siempre coincide con 3mn: puede incluir cabecera, paleta o compresión del archivo de entrada.'),
('¿Qué representa ultl=0?', 'Que la secuencia ocupa bytes completos sin un grupo residual. No significa que el último byte sea inválido ni que haya cero bits en toda la secuencia.'),
('¿Custom siempre ocupa menos que dflt?', 'No. Puede ahorrar bits de datos, pero debe almacenar cuatro especificaciones. El balance total depende de la imagen y del coste de las tablas.'),
('¿Por qué coinciden las RC y el MSE no es cero?', 'Las RC usan los mismos tamaños de archivos. El MSE mide muestras de imagen y puede ser positivo por la cuantización. Son métricas de fenómenos distintos.'),
('¿Cómo demostrarías que Huffman funciona?', 'Compararía exactamente XScan antes de codificar con XScanrec después de decodificar. Una imagen reconocible o un ahorro alto no sustituyen esa igualdad.'),
('¿Qué has implementado y qué has reutilizado?', 'He coordinado los dos procesos, adaptado EncodeScans y DecodeScans a las tablas a medida, definido la serialización y añadido controles y métricas. He reutilizado las auxiliares de imagen, símbolos y Huffman de la librería, explicando su contrato y sus límites.'),
('¿Qué mejorarías?', 'Separaría evaluación y descompresión, permitiría nombres de salida configurables, añadiría identificación de formato y validación más completa, comprobaría C=0 en el codificador y ampliaría las pruebas. Son mejoras propuestas, no trabajo ya ejecutado.')]
for q,a in qa: sub(q,a)
section('Ejercicios para comprobar que lo entiendes',r'''
Antes de mirar, calcula: (1) ampliación de una imagen de 17 filas y 9 columnas;
(2) categoría y posición de -6; (3) símbolo para 4 ceros antes de 5;
(4) bytes y ultl para 19 bits; (5) RC si TO=2000 y TC=600.

\textbf{Soluciones razonadas:} (1) $24\times16$, con $3\cdot2=6$ bloques
por componente. (2) C=3, P=7-6=1, bits 001. (3) C=3 y símbolo $16\cdot4+3=67$;
P=5 aporta 101. (4) Tres bytes, ultl=3 y cinco bits de relleno.
(5) RC=70\%, proporción ocupada=30\% y factor de compresión $2000/600\simeq3,33$.

Si no puedes explicar una solución, vuelve a la etapa correspondiente del
capítulo 2 y sigue un bloque con papel y lápiz. En la entrevista conviene
justificar las decisiones antes de citar los nombres de funciones.
''')
add(r'\chapter{Correspondencia con el diario y fuentes}')
section('Cómo encajan los pasos de desarrollo',r'''
El diario de compresión distribuye el trabajo en 16 pasos: 1 a 5 preparan
la imagen; 6 a 10 desarrollan EncodeScans\_custom; 11 empaqueta; 12 define
el formato; 13 escribe; 14 calcula RC; 15 y 16 documentan pruebas y correcciones.
El código principal agrupa esas responsabilidades en diez comentarios PASO.
No son dos algoritmos diferentes: cambia el nivel de detalle.

En descompresión, los pasos 1 a 6 preparan la referencia y leen el contenedor;
7 y 8 reconstruyen tablas y decodifican dentro de DecodeScans\_custom;
9 a 12 reconstruyen la imagen; 13 a 15 evalúan y visualizan; 16 prueba el conjunto.
Los capítulos 3 y 5 explican cada uno de esos pasos y sus auxiliares.
''')
section('Material utilizado y alcance',r'''
\begin{enumerate}
\item \texttt{desarrollo\_ejercicio2.md}: diario completo de implementación,
correcciones y prueba comunicada.
\item \texttt{jcom\_custom.m}, \texttt{jdes\_custom.m},
\texttt{EncodeScans\_custom.m} y \texttt{DecodeScans\_custom.m}:
código real consultado, reproducido en los apéndices.
\item Auxiliares del proyecto: imlee, imdct, quantmat, quant88, scan,
CollectScan, catpos, zercatpos, Freq256, HSpecTables, AdjustBits,
HCodeTables, HCodingTables, EncodeSingleScan, bits2bytes, bytes2bits,
HDecodingTables, DecodeWord, DecodeSingleScan e imidct. Se contrastaron
también las rutas dflt disponibles para interpretar la adaptación.
\item Material docente consultado en el desarrollo: guion4, apartado 2;
Pract4, en particular el encargo custom y la ampliación de interfaces;
plan de construcción aportado. Las explicaciones de esta guía se ajustan
al código local; el formato binario concreto es una decisión del proyecto.
\end{enumerate}
No se han modificado los archivos MATLAB ni el diario para generar esta guía.
Los fragmentos de prueba y posibles mejoras están identificados como propuestas.
En los listados siguientes solo se transliteran acentos de comentarios para
su composición tipográfica; las instrucciones ejecutables y sus líneas se conservan.
''')
add(r'\appendix')
for f,title in [('jcom_custom.m','Código completo del compresor'),('EncodeScans_custom.m','Código completo de la auxiliar de codificación'),('jdes_custom.m','Código completo del descompresor'),('DecodeScans_custom.m','Código completo de la auxiliar de decodificación')]:
    text=(root/f).read_text(encoding='utf-8-sig')
    # Keep line numbers, transliterate only for stable listings encoding.
    text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode()
    add('\\chapter{'+title+'}\\label{src:'+f+'}\n')
    add('Archivo: \\texttt{'+f.replace('_',r'\_')+'}. Las líneas corresponden a la copia consultada.\n')
    code(text)
add(r'\end{document}')
(out/'guia_ejercicio2.tex').write_text('\n'.join(parts),encoding='utf-8')
print('TeX generated:', len('\n'.join(parts)), 'characters')
