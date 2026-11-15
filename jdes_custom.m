function [MSE, RC] = jdes_custom(fname)
    % Descomprime un archivo .huc con tablas Huffman a medida.
    % fname: nombre del archivo comprimido.
    % MSE: error cuadratico medio de la reconstruccion.
    % RC: porcentaje de espacio ahorrado.

    % PASO 1: comprobar el archivo y obtener su tamaño.
    if ~isfile(fname)
        error('No se encuentra el archivo comprimido.');
    end

    info = dir(fname);
    TC = info.bytes;

    % Nombre de la imagen que se guardara al descomprimir.
    archivoSalida = 'comprimido_des_cus.bmp';

    % PASO 2: obtener la imagen original para la comparacion.
    nombreOriginal = input( ...
        'Introduce el nombre de la imagen original: ', 's');

    if ~isfile(nombreOriginal)
        error('No se encuentra la imagen original.');
    end

    % Leer la imagen original en RGB.
    [X, ~, ~, mOriginal, nOriginal] = imlee(nombreOriginal);

    if size(X, 3) ~= 3 || ~isa(X, 'uint8')
        error('La imagen original debe estar en RGB de 8 bits.');
    end

    % PASO 3: abrir el archivo y leer la cabecera.
    fid = fopen(fname, 'rb', 'ieee-le');

    if fid == -1
        error('No se ha podido abrir el archivo comprimido.');
    end

    % Cerrar automaticamente el archivo al terminar la funcion,
    % incluso si ocurre un error.
    cierreArchivo = onCleanup(@() fclose(fid));

    % Leer los cuatro valores uint32 de la cabecera.
    datos = fread(fid, 4, '*uint32');

    if numel(datos) ~= 4
        error('La cabecera del archivo .huc esta incompleta.');
    end

    % Convertir a double para los calculos posteriores.
    m     = double(datos(1));
    n     = double(datos(2));
    caliQ = double(datos(3));
    TO    = double(datos(4));

    if any([m n caliQ TO] == 0)
        error('La cabecera contiene valores no validos.');
    end

    % Recuperar las dimensiones ampliadas.
    mamp = 8 * ceil(m / 8);
    namp = 8 * ceil(n / 8);

    % Comprobar las dimensiones de la imagen de referencia.
    if mOriginal ~= m || nOriginal ~= n
        error('La imagen original no coincide en dimensiones.');
    end

    % PASO 4: leer las cuatro especificaciones Huffman.
    % Orden: Y_DC, Y_AC, C_DC, C_AC.
    tablasBITS = cell(1, 4);
    tablasHUFFVAL = cell(1, 4);

    for k = 1:4
        % Cada BITS contiene 16 valores uint16.
        b = fread(fid, 16, '*uint16');

        if numel(b) ~= 16
            error('Lectura incompleta de BITS en la tabla %d.', k);
        end

        b = double(b);

        % La suma de BITS indica cuantos simbolos leer.
        cantidadSimbolos = sum(b);

        if cantidadSimbolos < 1 || cantidadSimbolos > 256
            error('Cantidad de simbolos no valida en la tabla %d.', k);
        end

        % Cada simbolo de HUFFVAL ocupa un uint8.
        h = fread(fid, cantidadSimbolos, '*uint8');

        if numel(h) ~= cantidadSimbolos
            error('Lectura incompleta de HUFFVAL en la tabla %d.', k);
        end

        h = double(h);

        if numel(unique(h)) ~= cantidadSimbolos
            error('HUFFVAL contiene simbolos repetidos en la tabla %d.', k);
        end

        tablasBITS{k} = b;
        tablasHUFFVAL{k} = h;
    end

    % Identificar las especificaciones de cada tabla.
    BITS_Y_DC = tablasBITS{1};
    HUFFVAL_Y_DC = tablasHUFFVAL{1};

    BITS_Y_AC = tablasBITS{2};
    HUFFVAL_Y_AC = tablasHUFFVAL{2};

    BITS_C_DC = tablasBITS{3};
    HUFFVAL_C_DC = tablasHUFFVAL{3};

    BITS_C_AC = tablasBITS{4};
    HUFFVAL_C_AC = tablasHUFFVAL{4};


    % PASO 5: leer las tres componentes comprimidas.
    nombres = {'Y', 'Cb', 'Cr'};
    bytesComponentes = cell(1, 3);
    longitudes = zeros(1, 3);
    indicadores = zeros(1, 3);

    for k = 1:3
        % Leer la cantidad de bytes de la componente.
        longitud = fread(fid, 1, '*uint32');

        if isempty(longitud)
            error('No se ha podido leer la longitud de %s.', nombres{k});
        end

        % Leer el indicador del ultimo byte.
        ultl = fread(fid, 1, '*uint8');

        if isempty(ultl)
            error('No se ha podido leer ultl de %s.', nombres{k});
        end

        longitud = double(longitud);
        ultl = double(ultl);

        if ultl > 7
            error('Indicador ultl no valido en %s.', nombres{k});
        end

        if longitud == 0 || longitud > TC - ftell(fid)
            error('Longitud no valida en %s.', nombres{k});
        end

        % Leer los bytes empaquetados.
        bytes = fread(fid, longitud, '*uint8');

        if numel(bytes) ~= longitud
            error('Lectura incompleta de %s.', nombres{k});
        end

        longitudes(k) = longitud;
        indicadores(k) = ultl;
        bytesComponentes{k} = bytes;
    end

    % Recuperar las variables de cada componente.
    LY  = longitudes(1);
    LCb = longitudes(2);
    LCr = longitudes(3);

    ultlY  = indicadores(1);
    ultlCb = indicadores(2);
    ultlCr = indicadores(3);

    bytesY  = bytesComponentes{1};
    bytesCb = bytesComponentes{2};
    bytesCr = bytesComponentes{3};

    % Debemos haber consumido exactamente todo el archivo.
    if ftell(fid) ~= TC
        error('El archivo contiene datos adicionales no previstos.');
    end

    % Cerrar ahora el archivo mediante el objeto onCleanup.
    clear cierreArchivo

    % PASO 6: recuperar las secuencias binarias.
    CodedY  = bytes2bits(bytesY, ultlY);
    CodedCb = bytes2bits(bytesCb, ultlCb);
    CodedCr = bytes2bits(bytesCr, ultlCr);

    % PASO 8: decodificar con las tablas Huffman a medida.
    XScanrec = DecodeScans_custom( ...
        CodedY, CodedCb, CodedCr, [mamp namp], ...
        BITS_Y_DC, HUFFVAL_Y_DC, BITS_Y_AC, HUFFVAL_Y_AC, ...
        BITS_C_DC, HUFFVAL_C_DC, BITS_C_AC, HUFFVAL_C_AC);

    % PASO 9: deshacer el orden zigzag.
    Xlabrec = invscan(XScanrec);

    % PASO 10: descuantizar las etiquetas.
    Xtransrec = desquantmat(Xlabrec, caliQ);

    % PASO 11: aplicar la DCT inversa.
    Xamprec = imidct(Xtransrec, m, n);

    % PASO 12: convertir a RGB, recortar y guardar.
    Xrgb = uint8(round(ycbcr2rgb(Xamprec / 255) * 255));

    % Eliminar las filas y columnas añadidas al comprimir.
    Xrec = Xrgb(1:m, 1:n, :);

    % Guardar la imagen reconstruida.
    imwrite(Xrec, archivoSalida, 'bmp');

    % PASO 13: calcular el error cuadratico medio.
    errorImagen = double(X) - double(Xrec);
    erroresCuadrados = errorImagen .^ 2;
    MSE = mean(erroresCuadrados(:));

    % PASO 14: calcular el porcentaje de espacio ahorrado.
    RC = 100 * (TO - TC) / TO;
    
end