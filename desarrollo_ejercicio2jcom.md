# Ejercicio 2: compresión con tablas Huffman a medida

## Paso 1. Preparar jcom_custom

Creo el archivo jcom_custom.m con dos entradas: fname y caliQ,
y una salida: RC.

Valido que caliQ sea un entero positivo. Obtengo mediante dir
el tamaño del archivo original en bytes y lo guardo en TO,
para calcular el porcentaje de ahorro al terminar la compresión.

Establezco comprimido.huc como nombre del archivo de salida.
En este paso todavía no se crea el archivo ni se calcula RC.

## Paso 2. Leer y acondicionar la imagen

Utilizo imlee para leer la imagen y obtener X en RGB.
La función también convierte la imagen a YCbCr y amplía
sus dimensiones a múltiplos de ocho repitiendo los bordes.

El resultado preparado se guarda en Xamp. Conservo las
dimensiones originales y ampliadas para las etapas posteriores.

## Paso 3. Aplicar la DCT

Aplico imdct a Xamp, que ya está en YCbCr y tiene dimensiones
múltiplos de ocho.

La función resta 128 a las muestras y transforma cada componente
por bloques de 8×8. Obtengo Xtrans, que contiene un coeficiente
DC y 63 coeficientes AC por bloque.

## Paso 4. Cuantizar los coeficientes

Utilizo quantmat con Xtrans y caliQ para obtener Xlab.

La función cuantiza por bloques de 8×8 usando tablas distintas
para luminancia y crominancia. El resultado contiene etiquetas
enteras y muchos coeficientes pueden quedar a cero.

Esta etapa introduce pérdida de precisión. Se mantiene igual
que en jcom_dflt: las tablas Huffman a medida se aplicarán después.

Cuantizar consiste en dividir cada coeficiente (DC y los 63 AC) por su escalón de cuantización y convertir el resultado en un entero. caliQ ajusta esos escalones. El redondeo o truncamiento concreto depende de quant88; ahí se pierde precisión y aparecen muchos ceros.

Huffman solo codifica sin pérdida: asigna códigos binarios más cortos a los símbolos frecuentes. No cuantiza ni añade pérdida de calidad.

## Paso 5. Reordenar las etiquetas en zigzag

Después de cuantizar, cada bloque de 8×8 contiene 64 etiquetas:
una corresponde al coeficiente DC y las otras 63 a los AC.

Utilizo la función scan para reordenar las etiquetas de cada
bloque siguiendo un recorrido en zigzag:

    XScan = scan(Xlab);

El recorrido comienza por el DC y continúa por los AC, desde
las frecuencias más bajas hacia las más altas. Como los
coeficientes de frecuencias altas suelen quedar a cero tras
la cuantización, este orden favorece que aparezcan rachas
de ceros, especialmente al final del bloque.

Estas rachas se aprovecharán en la codificación posterior
para representar los ceros de forma compacta.

El resultado, XScan, conserva las dimensiones y las tres
componentes de Xlab: Y, Cb y Cr. Solo cambia el orden de las
etiquetas dentro de cada bloque; sus valores no se modifican
y no se introduce pérdida adicional.

## Paso 6. Preparar los símbolos para la codificación Huffman

Creo la función auxiliar EncodeScans_custom, que recibirá
XScan y se encargará de construir las tablas Huffman a medida
y codificar las tres componentes.

Primero separo XScan en sus tres planos: YScan, CbScan y CrScan.
Después aplico CollectScan a cada uno por separado.

### Preparación de los DC

Para cada bloque, CollectScan calcula la diferencia entre su
etiqueta DC y la del bloque anterior. En el primer bloque de
cada componente se toma cero como DC anterior.

Cada diferencia se representa mediante dos valores:

- C: categoría, que indica cuántos bits se necesitan para
  representar su amplitud.
- P: posición dentro de la categoría, que permite identificar
  el valor concreto y su signo.

Estos pares se guardan en DC_CP, con una fila por bloque:
la primera columna contiene C y la segunda contiene P.

### Preparación de los AC

Para los 63 AC de cada bloque, CollectScan aprovecha las
rachas de ceros. Para cada AC no nulo representa:

- Z: cantidad de ceros anteriores.
- C: categoría del AC.
- P: posición del valor dentro de su categoría.

Z y C se combinan en un único símbolo: ZCdec = 16*Z + C.
La matriz AC_ZCP guarda ZCdec en la primera columna y P
en la segunda. También incluye símbolos especiales para
el final de bloque (EOB) y las rachas de 16 ceros (ZRL).

### Resultado de esta etapa

Obtengo dos matrices por componente, seis en total.
Todavía no he contado frecuencias ni aplicado Huffman.

En los siguientes pasos contaré las categorías C de los DC
y los símbolos ZCdec de los AC para construir las tablas.
Las posiciones P se conservarán para añadir sus bits durante
la codificación.

## Paso 7. Contar las frecuencias de los símbolos

Después de preparar los datos con CollectScan, necesito saber
cuántas veces aparece cada símbolo. Estas frecuencias permitirán
construir tablas Huffman adaptadas a la imagen: los símbolos
más frecuentes tenderán a recibir códigos más cortos.

Utilizo Freq256 sobre la primera columna de las matrices
obtenidas en el paso anterior:

- En DC_CP cuento las categorías C de las diferencias DC.
- En AC_ZCP cuento los símbolos ZCdec, que combinan la cantidad
  de ceros anteriores y la categoría del coeficiente AC.

No cuento las posiciones P de la segunda columna, porque
se representarán mediante sus propios bits durante la codificación.

### Las cuatro distribuciones

Calculo cuatro vectores de frecuencias:

- FREQ_Y_DC: categorías DC de luminancia.
- FREQ_Y_AC: símbolos AC de luminancia.
- FREQ_C_DC: categorías DC de Cb y Cr juntas.
- FREQ_C_AC: símbolos AC de Cb y Cr juntos.

Cb y Cr comparten tablas Huffman. Por eso reúno sus símbolos
antes de contarlos, manteniendo separados los DC de los AC.

### Cómo interpretar Freq256

Freq256 devuelve un vector columna con 256 posiciones.
Cada posición contiene el número de apariciones de un símbolo.

Como MATLAB empieza a indexar en 1, el símbolo 0 se cuenta
en FREQ(1), el símbolo 1 en FREQ(2), y así sucesivamente.
En general, la frecuencia del símbolo s está en FREQ(s+1).

Estos valores son recuentos absolutos, no probabilidades.
Todavía no he generado los códigos Huffman: solo he obtenido
las frecuencias necesarias para construirlos.

## Paso 8. Generar las especificaciones Huffman

Utilizo HSpecTables para transformar cada vector de frecuencias
en dos vectores: BITS y HUFFVAL.

La función construye una distribución de longitudes de códigos
adaptada a las frecuencias de los símbolos y limita la longitud
máxima de los códigos a 16 bits.

### Qué contiene BITS

BITS indica cuántos códigos tienen cada longitud.

Por ejemplo, BITS(3) = 2 significa que hay dos códigos de
3 bits. No significa que el símbolo 3 tenga un código de 2 bits:
el índice representa una longitud, no un símbolo.

### Qué contiene HUFFVAL

HUFFVAL contiene los símbolos que recibirán los códigos,
agrupados en orden creciente de longitud.

BITS permite saber cuántos símbolos de HUFFVAL pertenecen
a cada grupo: primero los que tendrán códigos de 1 bit,
después los de 2 bits, y así sucesivamente.

Por tanto, debe cumplirse que la suma de BITS sea igual
al número de elementos de HUFFVAL.

### Las cuatro especificaciones

Aplico HSpecTables a las cuatro distribuciones de frecuencias
y obtengo un par BITS/HUFFVAL para cada tabla:

- Y_DC: diferencias DC de luminancia.
- Y_AC: símbolos AC de luminancia.
- C_DC: diferencias DC de Cb y Cr conjuntamente.
- C_AC: símbolos AC de Cb y Cr conjuntamente.

Estos cuatro pares deberán guardarse en el archivo .huc,
porque el descompresor los necesitará para reconstruir
las mismas tablas Huffman.

En esta etapa ya he definido las especificaciones de las
tablas, pero todavía falta generar los códigos binarios
concretos y preparar las tablas que utilizará el codificador.

## Paso 9. Construir las tablas de codificación Huffman

A partir de cada par BITS/HUFFVAL construyo la tabla que
permitirá consultar el código de un símbolo y su longitud.

Lo hago en dos etapas.

### Generar los códigos

Utilizo HCodeTables con BITS y HUFFVAL. Obtengo:

- HUFFSIZE: longitud en bits del código de cada símbolo.
- HUFFCODE: valor numérico de ese código.

Estos vectores siguen el mismo orden que HUFFVAL. Por tanto,
HUFFVAL(k) identifica el símbolo cuyo código es HUFFCODE(k)
y cuya longitud es HUFFSIZE(k).

Los códigos se generan siguiendo las reglas de Huffman
canónico: las longitudes y el orden de los símbolos permiten
determinar los códigos de forma reproducible.

### Organizar los códigos por símbolo

Utilizo HCodingTables para reorganizar esa información
en dos vectores de 256 posiciones:

- EHUFCO: código asignado a cada símbolo.
- EHUFSI: longitud en bits de ese código.

Como MATLAB empieza a indexar en 1, la información del
símbolo s se consulta en la posición s+1.

Después junto ambos vectores en una matriz:

    ehuf = [EHUFCO EHUFSI];

Cada fila corresponde a un símbolo. La primera columna
contiene su código numérico y la segunda, su longitud.

Es necesario guardar la longitud porque el valor numérico
no conserva los ceros iniciales. Por ejemplo, el código
binario 001 tiene valor numérico 1, pero ocupa 3 bits.

### Resultado de esta etapa

Obtengo cuatro tablas de codificación:

- ehuf_Y_DC: para los símbolos DC de Y.
- ehuf_Y_AC: para los símbolos AC de Y.
- ehuf_C_DC: para los símbolos DC de Cb y Cr.
- ehuf_C_AC: para los símbolos AC de Cb y Cr.

Estas tablas se utilizarán para codificar los datos.
Para reconstruirlas al descomprimir bastará con almacenar
los cuatro pares BITS/HUFFVAL en el archivo .huc.

## Paso 10. Codificar las tres componentes en binario

Una vez construidas las cuatro tablas Huffman, utilizo
EncodeSingleScan para codificar cada componente por separado.

Y utiliza las tablas ehuf_Y_DC y ehuf_Y_AC.
Cb y Cr utilizan las mismas tablas de crominancia:
ehuf_C_DC y ehuf_C_AC.

Compartir tablas no significa mezclar los datos: cada componente
produce su propia secuencia binaria.

### Cómo se representa cada bloque

La codificación mantiene el orden de los bloques. Dentro
de cada bloque se representa primero el DC y después los AC.

Para el DC se utiliza el código Huffman de la categoría
de su diferencia y la información de posición necesaria
para recuperar el valor concreto.

Para los AC se utiliza el código Huffman del símbolo ZCdec,
que combina los ceros anteriores y la categoría. También
se incorpora la información de posición correspondiente.
Los símbolos especiales permiten representar las rachas
de 16 ceros y el final de bloque.

Huffman no introduce pérdida adicional: representa en binario
la información obtenida después de la cuantización.

### Resultados que devuelve la auxiliar

EncodeScans_custom devuelve tres secuencias de caracteres
'0' y '1':

- CodedY: componente Y codificada.
- CodedCb: componente Cb codificada.
- CodedCr: componente Cr codificada.

También devuelve los cuatro pares BITS/HUFFVAL, necesarios
para reconstruir las tablas al descomprimir.

Añado la llamada a esta auxiliar en jcom_custom, justo después
de obtener XScan. Todavía no escribo el archivo: primero
tendré que empaquetar las secuencias binarias en bytes.

## Paso 11. Empaquetar las secuencias binarias en bytes

Las variables CodedY, CodedCb y CodedCr contienen caracteres
'0' y '1'. Para almacenarlas de forma compacta, utilizo
bits2bytes sobre cada componente por separado.

La función agrupa los caracteres de ocho en ocho e interpreta
cada grupo como un número entre 0 y 255, almacenado como uint8.

Por ejemplo, la secuencia '10110010' se convierte en un único
byte de valor 178. Así, ocho bits de información quedan
representados en un byte.

### Tratamiento del último grupo

La longitud de una secuencia puede no ser múltiplo de ocho.
En ese caso, bits2bytes completa el último grupo añadiendo
ceros a la derecha.

La función devuelve el indicador ultl para poder distinguir
los bits originales de esos ceros de relleno:

- Si ultl está entre 1 y 7, indica cuántos bits válidos
  contiene el último byte.
- Si ultl vale 0, todos los bytes están completos y
  no se ha añadido relleno.

Por ejemplo, '101' se almacena como '10100000' y ultl vale 3.
Al descomprimir, solo deben recuperarse los tres primeros bits.

### Datos obtenidos

Obtengo los vectores bytesY, bytesCb y bytesCr, junto con
sus indicadores ultlY, ultlCb y ultlCr.

También calculo LY, LCb y LCr mediante numel. Estas variables
indican cuántos bytes ocupa cada componente empaquetada.

Guardaré las longitudes y los indicadores junto con los datos,
para que el descompresor pueda separar las tres componentes
y recuperar sus secuencias binarias sin incluir el relleno.

Este paso no introduce pérdida: únicamente cambia la forma
de almacenar los bits.

## Paso 12. Definir la estructura del archivo .huc

Antes de escribir el archivo, establezco el orden y el tipo
de sus campos. El descompresor deberá respetar exactamente
esta misma estructura al leerlo.

### Datos generales

El archivo comenzará con cuatro valores, en este orden:

1. m: altura original de la imagen.
2. n: anchura original de la imagen.
3. caliQ: factor utilizado para cuantizar.
4. TO: tamaño del archivo original en bytes.

Cada valor se almacenará como uint32, ocupando cuatro bytes.
Compruebo previamente que los valores caben en este tipo.

Las dimensiones ampliadas no se almacenan porque se pueden
calcular a partir de m y n, redondeándolas hacia arriba
al siguiente múltiplo de ocho.

### Especificaciones Huffman

Después de los datos generales guardaré las cuatro tablas
en este orden fijo:

1. Y_DC.
2. Y_AC.
3. C_DC.
4. C_AC.

Para cada tabla escribiré primero BITS y después HUFFVAL.

BITS contiene 16 recuentos, uno por longitud de código,
y cada recuento se almacenará como uint16, de dos bytes.
Este tipo permite representar también un recuento de 256.

HUFFVAL contiene símbolos entre 0 y 255, por lo que cada
símbolo se almacenará como uint8, de un byte.

No necesito guardar por separado la longitud de HUFFVAL:
el descompresor podrá calcularla sumando los valores de BITS.

Antes de escribir, compruebo que cada BITS tenga 16 elementos
y que su suma coincida con la cantidad de símbolos de HUFFVAL.

### Datos de las componentes

Después de las cuatro especificaciones guardaré las
componentes en el orden Y, Cb y Cr.

Para cada componente escribiré:

1. Su cantidad de bytes, como uint32.
2. Su indicador ultl, como uint8.
3. Sus bytes empaquetados, como uint8.

La longitud permite saber cuántos bytes leer y ultl permite
eliminar el relleno del último byte cuando sea necesario.

### Orden de bytes

Al abrir el archivo para escribir utilizaré little-endian.
El descompresor deberá utilizar el mismo orden para interpretar
correctamente los valores uint16 y uint32.

## Paso 13. Escribir el archivo comprimido

Abro el archivo indicado por archivo mediante fopen, utilizando
el modo 'wb' para escritura binaria y el orden little-endian.

Si fopen devuelve -1, no se ha podido abrir el archivo y
detengo la función con un error.

### Orden de escritura

Utilizo fwrite para guardar los datos siguiendo el formato
definido en el paso anterior:

1. La cabecera: m, n, caliQ y TO, como uint32.
2. Los cuatro pares BITS/HUFFVAL, en el orden Y_DC, Y_AC,
   C_DC y C_AC. Cada BITS se escribe como uint16 y cada
   HUFFVAL como uint8.
3. La componente Y: cantidad de bytes, indicador ultl
   y bytes empaquetados.
4. La componente Cb, con la misma estructura.
5. La componente Cr, con la misma estructura.

Las tablas deben acompañar a los datos porque son específicas
de esta imagen. El descompresor las necesitará para interpretar
las secuencias comprimidas.

### Comprobar la escritura

Calculo TCprevisto, que es el tamaño esperado del archivo:

- 16 bytes de cabecera.
- 128 bytes correspondientes a los cuatro vectores BITS.
- Un byte por cada símbolo de los cuatro vectores HUFFVAL.
- 15 bytes para las longitudes y los indicadores de las
  tres componentes.
- LY + LCb + LCr bytes de datos empaquetados.

También acumulo en escritos la cantidad de bytes que fwrite
ha escrito realmente. Si no coincide con TCprevisto,
considero que la escritura está incompleta.

### Cerrar el archivo

Utilizo try/catch para cerrar el archivo si ocurre un error
durante la escritura y después comunicar ese error.

Si la escritura termina correctamente, cierro el archivo
y compruebo que fclose devuelve cero.

El archivo debe quedar cerrado antes de medir su tamaño
real y calcular RC.

## Paso 14. Calcular el porcentaje de compresión

Después de cerrar el archivo comprimido, consulto su tamaño
real mediante dir y lo guardo en TC.

Este tamaño incluye todo el contenido del .huc: la cabecera,
las cuatro especificaciones Huffman, las longitudes y los
indicadores de las componentes, y los datos empaquetados.

Compruebo que TC coincide con TCprevisto, calculado antes
de la escritura. Si son diferentes, detengo la función
porque el archivo no tiene el tamaño esperado.

### Cálculo de RC

Utilizo el tamaño original TO y el tamaño comprimido TC:

    RC = 100 * (TO - TC) / TO;

La diferencia TO - TC indica cuántos bytes se han ahorrado.
Al dividirla entre TO y multiplicar por 100, obtengo
el porcentaje de ahorro respecto al archivo original.

Por ejemplo, si TO vale 1000 bytes y TC vale 400 bytes,
el ahorro es de 600 bytes y RC vale 60 %.

El resultado se interpreta así:

- RC positiva: el archivo comprimido ocupa menos.
- RC igual a cero: ambos archivos ocupan lo mismo.
- RC negativa: el archivo comprimido ocupa más.

Una RC negativa puede ocurrir si el coste de almacenar
la cabecera y las tablas supera el ahorro de los datos,
especialmente en imágenes pequeñas.

Finalmente, jcom_custom devuelve RC como resultado.

## Paso 15. Primera prueba del compresor

Guardo jcom_custom.m y EncodeScans_custom.m y ejecuto
el compresor con una imagen de la librería y caliQ = 100.

Este factor utiliza las tablas de cuantización estándar.
La función debe terminar sin errores, generar comprimido.huc
y devolver el porcentaje de ahorro RC.

### Comprobaciones

Compruebo que existe comprimido.huc y consulto mediante dir
los tamaños reales del archivo original y del comprimido.

Después calculo de forma independiente:

    RCcomprobada = 100 * (TO - TC) / TO;

Comparo este resultado con el valor devuelto por jcom_custom.
Ambos deben coincidir, admitiendo una pequeña tolerancia
por trabajar con números de coma flotante.

### Resultados de la prueba

- Imagen utilizada: pendiente.
- Factor caliQ: 100.
- Tamaño original: pendiente.
- Tamaño del archivo .huc: pendiente.
- RC obtenida: pendiente.
- Errores observados: pendiente.

### Alcance de esta comprobación

Esta prueba confirma que el compresor termina, crea el archivo
y calcula RC de acuerdo con los tamaños reales.

Todavía no demuestra que los datos puedan descomprimirse
correctamente. Esa comprobación se realizará al implementar
jdes_custom y verificar la reconstrucción.

## Corrección detectada en la primera prueba

La ejecución se detuvo porque se esperaba que cada vector
BITS tuviera exactamente 16 elementos.

Al revisar AdjustBits, compruebo que devuelve únicamente
las posiciones hasta la mayor longitud utilizada. Por tanto,
un vector BITS con menos de 16 elementos es válido.

Antes de escribir las tablas, completo cada BITS con ceros
hasta obtener 16 posiciones. Los ceros añadidos indican
que no existen códigos de esas longitudes.

Esta adaptación no modifica los códigos ni HUFFVAL.
Permite mantener el formato del archivo, que reserva
16 valores uint16 para cada vector BITS.

## Resultado de la primera prueba

Ejecuto jcom_custom con Img00.bmp y caliQ = 100.

La imagen tiene 480 píxeles de ancho y 640 de alto.
No necesita ampliación, porque ambas dimensiones son
múltiplos de ocho.

La función termina sin errores y devuelve un ahorro
del 97,80 %. Por tanto, el archivo .huc ocupa aproximadamente
el 2,20 % del tamaño del BMP original.

Se superan las comprobaciones de escritura y tamaño.
Queda pendiente verificar la reconstrucción de la imagen
cuando se implemente jdes_custom.
