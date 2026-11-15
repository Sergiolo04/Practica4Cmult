
function [MSE, RC] = jdes_dflt(fname)

    % jdes_dflt: Descompresor con tablas Huffman por defecto.
    %
    % Entrada:
    % fname: Nombre del archivo comprimido .hud.
    %
    % Salidas:
    % MSE: Error cuadratico medio.
    % RC: Porcentaje de espacio ahorrado.


    % --------------- PASO 1 ----------------
    % Comprobar la existencia del archivo y obtener su tamaño.

    if ~isfile(fname)
        error('No se encuentra el archivo comprimido.');
    end

    info = dir(fname);
    TC = info.bytes;

    archivoSalida = 'comprimido_des_def.bmp';


    % --------------- PASO 2 ----------------
    % Obtener la imagen original para calcular posteriormente el MSE.

    nombreOriginal = input( ...
        'Introduce el nombre de la imagen original: ', 's');

    if ~isfile(nombreOriginal)
        error('No se encuentra la imagen original.');
    end

    [X, ~, ~, mOriginal, nOriginal] = imlee(nombreOriginal);

    if size(X, 3) ~= 3
        error('La imagen original no tiene tres canales RGB.');
    end

    if ~isa(X, 'uint8')
        error('La imagen original debe estar representada en RGB de 8 bits.');
    end


    % --------------- PASO 3 ----------------
    % Leer el archivo comprimido usando el mismo formato
    % binario que utilizamos en jcom_dflt.m.

    % Abrir el archivo en lectura binaria little-endian.
    fid = fopen(fname, 'rb', 'ieee-le');

    if fid == -1
        error('No se ha podido abrir el archivo comprimido.');
    end

    try

        % ---- LEER METADATOS GENERALES ----

        % Leer cuatro uint32: m, n, caliQ y TO.
        datos = fread(fid, 4, '*uint32');

        if numel(datos) ~= 4
            error('Cabecera incompleta del archivo .hud.');
        end

        m = datos(1);
        n = datos(2);
        caliQ = datos(3);
        TO = datos(4);


        % ---- LEER COMPONENTE Y ----

        % Longitud de la componente Y.
        LY = fread(fid, 1, '*uint32');

        if numel(LY) ~= 1
            error('No se ha podido leer LY.');
        end

        % Indicador de bits validos del ultimo byte.
        ultlY = fread(fid, 1, '*uint8');

        if numel(ultlY) ~= 1
            error('No se ha podido leer ultlY.');
        end

        % Comprobar que la longitud cabe en el archivo restante.
        if double(LY) > TC - ftell(fid)
            error('Longitud LY incompatible con el archivo.');
        end

        % Leer los bytes comprimidos de Y.
        bytesY = fread(fid, double(LY), '*uint8');

        if numel(bytesY) ~= double(LY)
            error('Lectura incompleta de la componente Y.');
        end


        % ---- LEER COMPONENTE Cb ----

        % Longitud de la componente Cb.
        LCb = fread(fid, 1, '*uint32');

        if numel(LCb) ~= 1
            error('No se ha podido leer LCb.');
        end

        % Indicador del ultimo byte.
        ultlCb = fread(fid, 1, '*uint8');

        if numel(ultlCb) ~= 1
            error('No se ha podido leer ultlCb.');
        end

        if double(LCb) > TC - ftell(fid)
            error('Longitud LCb incompatible con el archivo.');
        end

        % Leer los bytes comprimidos de Cb.
        bytesCb = fread(fid, double(LCb), '*uint8');

        if numel(bytesCb) ~= double(LCb)
            error('Lectura incompleta de la componente Cb.');
        end


        % ---- LEER COMPONENTE Cr ----

        % Longitud de la componente Cr.
        LCr = fread(fid, 1, '*uint32');

        if numel(LCr) ~= 1
            error('No se ha podido leer LCr.');
        end

        % Indicador del ultimo byte.
        ultlCr = fread(fid, 1, '*uint8');

        if numel(ultlCr) ~= 1
            error('No se ha podido leer ultlCr.');
        end

        if double(LCr) > TC - ftell(fid)
            error('Longitud LCr incompatible con el archivo.');
        end

        % Leer los bytes comprimidos de Cr.
        bytesCr = fread(fid, double(LCr), '*uint8');

        if numel(bytesCr) ~= double(LCr)
            error('Lectura incompleta de la componente Cr.');
        end


    catch fallo

        % Si falla alguna lectura, cerrar y comunicar el error.
        fclose(fid);
        rethrow(fallo);

    end

    % Cerrar el archivo despues de leerlo.
    estado = fclose(fid);

    if estado ~= 0
        error('No se ha podido cerrar el archivo comprimido.');
    end


    % ---- COMPROBAR LOS METADATOS ----

    % Las dimensiones y el factor de calidad deben ser positivos.
    if m == 0 || n == 0
        error('Las dimensiones guardadas no son validas.');
    end

    if caliQ == 0
        error('El factor caliQ guardado no es valido.');
    end

    % El tamaño original debe ser positivo.
    if TO == 0
        error('El tamaño original TO no es valido.');
    end

    % Los indicadores solo pueden valer entre 0 y 7.
    if ultlY > 7 || ultlCb > 7 || ultlCr > 7
        error('Indicadores del ultimo byte no validos.');
    end

    % Comprobar el tamaño total del archivo.
    TCprevisto = 31 + double(LY) + double(LCb) + double(LCr);

    if TC ~= TCprevisto
        error('El tamaño del .hud no coincide con el previsto.');
    end


    % ---- RECUPERAR DIMENSIONES AMPLIADAS ----

    mamp = 8 * ceil(double(m) / 8);
    namp = 8 * ceil(double(n) / 8);


    % ---- COMPROBAR DIMENSIONES DEL ORIGINAL ----

    if mOriginal ~= m || nOriginal ~= n
        error('La imagen original no coincide en dimensiones.');
    end


    % --------------- PASO 4 ----------------
    % Recuperar las secuencias binarias originales
    % a partir de los bytes comprimidos.
    %
    % bytes2bits elimina los bits de relleno del ultimo byte
    % usando el indicador ultl de cada componente.

    % Recuperar los bits de luminancia Y.
    CodedY = bytes2bits(bytesY, ultlY);

    % Recuperar los bits de crominancia Cb.
    CodedCb = bytes2bits(bytesCb, ultlCb);

    % Recuperar los bits de crominancia Cr.
    CodedCr = bytes2bits(bytesCr, ultlCr);

    
    % --------------- PASO 5 ----------------
    % Decodificar las tres secuencias binarias con las
    % tablas Huffman por defecto.
    %
    % Se recuperan las etiquetas cuantizadas de Y, Cb y Cr.
    % Los bloques siguen ordenados internamente en zigzag.

    XScanrec = DecodeScans_dflt(CodedY, CodedCb, CodedCr, [mamp namp]);

    % --------------- PASO 6 ----------------
    % Deshacer el orden zigzag de cada bloque 8x8.
    %
    % XScanrec contiene las etiquetas cuantizadas en zigzag.
    % invscan devuelve cada etiqueta a su posicion natural
    % dentro del bloque de coeficientes DCT.
    %
    % Se mantienen las dimensiones mamp x namp x 3
    % y el orden de las componentes Y, Cb y Cr.

    Xlabrec = invscan(XScanrec);


    % --------------- PASO 7 ----------------
    % Descuantizar las etiquetas recuperadas.
    %
    % Xlabrec contiene las etiquetas cuantizadas de Y, Cb y Cr.
    % desquantmat utiliza las tablas QY y QC ajustadas con caliQ.
    % Cada etiqueta se multiplica por su escalon de cuantificacion.
    %
    % Xtransrec contiene los coeficientes DCT reconstruidos
    % aproximadamente, de tamaño mamp x namp x 3.

    Xtransrec = desquantmat(Xlabrec, double(caliQ));


    % --------------- PASO 8 ----------------
    % Aplicar la DCT inversa a los coeficientes reconstruidos.
    %
    % Xtransrec contiene los coeficientes DCT de Y, Cb y Cr.
    % imidct aplica la IDCT por bloques de 8x8 y suma 128
    % para deshacer el centrado que realizo imdct.
    %
    % Xamprec contiene las muestras YCbCr reconstruidas.
    % Mantiene las dimensiones ampliadas mamp x namp x 3.

    Xamprec = imidct(Xtransrec, double(m), double(n));


    % --------------- PASO 9 ----------------
    % Convertir la imagen reconstruida a RGB, recuperar
    % sus dimensiones originales y guardarla como BMP.
    %
    % Xamprec contiene las muestras reconstruidas en YCbCr,
    % con dimensiones ampliadas mamp x namp x 3.
    %
    % Xrec sera la imagen final RGB de tamaño m x n x 3.

    % Convertir de YCbCr a RGB.
    % Normalizamos a [0,1], convertimos a RGB y volvemos
    % a la escala [0,255], redondeando a uint8.
    Xrgb = uint8(round(ycbcr2rgb(Xamprec / 255) * 255));

    % Eliminar las filas y columnas añadidas en la compresion.
    % Conservar las m primeras filas, las n primeras columnas
    % y las tres componentes RGB.
    Xrec = Xrgb(1:double(m), 1:double(n), :);

    % Guardar la imagen reconstruida como BMP real.
    imwrite(Xrec, archivoSalida, 'bmp');


    % --------------- PASO 10 ----------------
    % Calcular el error cuadratico medio (MSE).
    %
    % X contiene la imagen RGB original.
    % Xrec contiene la imagen RGB reconstruida.
    % Ambas tienen dimensiones m x n x 3.
    %
    % Convertimos a double para evitar errores al restar
    % y elevar al cuadrado valores de tipo uint8.

    % Calcular las diferencias entre las dos imagenes.
    errorImagen = double(X) - double(Xrec);

    % Elevar cada diferencia al cuadrado.
    erroresCuadrados = errorImagen .^ 2;

    % Sumar los errores cuadrados de todos los canales.
    sumaErrores = sum(erroresCuadrados(:));

    % Dividir entre el numero total de muestras RGB.
    MSE = sumaErrores / (double(m) * double(n) * 3);


    % --------------- PASO 11 ----------------
    % Calcular el porcentaje de espacio ahorrado.
    %
    % TO: tamaño original guardado en la cabecera del .hud.
    % TC: tamaño real del archivo comprimido .hud.
    %
    % Utilizamos la misma formula que jcom_dflt.

    RC = 100 * (double(TO) - double(TC)) / double(TO);


    % --------------- PASO 12 ----------------
    % Visualizar la imagen original y la reconstruida.
    %
    % X contiene la imagen RGB original.
    % Xrec contiene la imagen RGB descomprimida.
    % Mostramos ambas imagenes una al lado de la otra
    % para poder compararlas visualmente.

    % Crear una ventana grafica.
    figure;

    % Mostrar la imagen original a la izquierda.
    subplot(1, 2, 1);
    imshow(X);
    title('Imagen original');

    % Mostrar la imagen reconstruida a la derecha.
    subplot(1, 2, 2);
    imshow(Xrec);
    title('Imagen descomprimida');

end
