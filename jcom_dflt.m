function RC = jcom_dflt(fname, caliQ)
    % Comprime la imagen y genera comprimido.hud.
    % RC: porcentaje de espacio ahorrado respecto al archivo original.
    % RC = 100 * (TO - TC) / TO.
    validateattributes(caliQ, {'numeric'}, ...
    {'scalar', 'real', 'finite', 'integer', 'positive'});

    %---------------PASO 1----------------:
    % La función recibe el nombre de la imagen y el factor de cuantización. 
    % Primero guardo el tamaño original en bytes para calcular después la relación de compresión
    % y establezco un nombre fijo para el archivo de salida: comprimido.hud
    % Tamaño del archivo original en bytes.
    info = dir(fname);
    TO = info.bytes;
    archivo = 'comprimido.hud';     % Nombre fijo del futuro archivo comprimido.


    % -------------PASO 2----------------:
    % Utilizo imlee para leer la imagen y obtener su representación RGB. 
    % La auxiliar la convierte a YCbCr y amplía sus dimensiones a múltiplos de ocho repitiendo los bordes. 
    % Conservo también las dimensiones originales. 
    % Así obtengo Xamp, preparada para aplicar después la DCT por bloques

    [X, Xamp, tipo, m, n, mamp, namp] = imlee(fname);
    % X - Imagen original representada en RGB
    % Xamp - La imagen convertida a YCbCr y ampliada a múltiplos de 8 (tiene 3 capas: Y, Cb, Cr)
    % tipo - 0 si la entrada era indexada; 1 si era truecolor
    % m - numero original de filas: altura
    % n - Numero original de coumnas: anchura
    % mamp - Numero de filas despues de ampliar
    % namp - Numero de columnas despues de ampliar

    % -------------PASO 3----------------:
    % Aplico imdct a la imagen ya acondicionada. 
    % La auxiliar resta 128 para centrar las muestras, separa Y, Cb y Cr 
    % y transforma cada componente por bloques de ocho por ocho. 
    % Obtengo una matriz del mismo tamaño, pero ahora contiene coeficientes: un DC y 63 AC por bloque

    Xtrans = imdct(Xamp); %no le pasamos X porque Xamp ya tiene el color y las dimensiones que necesita esta etapa

    %Los numero sde Xtrans ya no son valores de píxeles.
    %Son las cantidades de los patrones básciso que describen cada bloque

    % -------------PASO 4----------------:

    % Cuantizo los coeficientes DCT mediante quantmat. 
    % Utiliza QY para luminancia y QC para ambas crominancias, ajustadas por caliQ. 
    % Cada coeficiente se divide por su escalón y se transforma en una etiqueta mediante la regla de quant88. 
    % Obtengo Xlab, del mismo tamaño, con etiquetas enteras con signo. 
    % Esta operación reduce la precisión y puede convertir muchos coeficientes en cero

    Xlab = quantmat(Xtrans, caliQ);
    %Devuelve las etiquetas enteras obtenidas al cuantizar esos coeficientes

    % -------------PASO 5----------------:
    % Aplico scan a las etiquetas cuantizadas. 
    % Esta función utiliza zigzag64 para reordenar cada bloque de ocho por ocho, 
    % manteniendo el DC primero. 
    % El resultado conserva las dimensiones de la matriz y sus valores, 
    % pero cada bloque queda preparado para leer por filas su secuencia zigzag. 
    % Este orden facilita aprovechar las rachas de ceros en la codificación posterior

    XScan = scan(Xlab);

    % ---------------PASOS 6, 7 Y 8------------------:
    % Preparar los datos, las tablas Huffman y codificar los scans.
    [CodedY, CodedCb, CodedCr] = EncodeScans_dflt(XScan);

    % ---------------PASO 9 ---------------
    % Empaquetar cada componente en bytes.
    [bytesY, ultlY] = bits2bytes(CodedY);
    [bytesCb, ultlCb] = bits2bytes(CodedCb);
    [bytesCr, ultlCr] = bits2bytes(CodedCr);

    % Numero de bytes de cada componente.
    LY = length(bytesY);
    LCb = length(bytesCb);
    LCr = length(bytesCr);

    % --------------- PASO 10 ---------------
    % Preparar los campos del formato .hud.
    %
    % Orden de almacenamiento:
    % m, n, caliQ, TO,
    % LY, ultlY, bytesY,
    % LCb, ultlCb, bytesCb,
    % LCr, ultlCr, bytesCr.

    % Comprobar los campos antes de convertirlos a uint32.
    campos32 = [m n caliQ TO LY LCb LCr];

    validateattributes(campos32, {'numeric'}, ...
        {'real', 'finite', 'integer', 'nonnegative', ...
        '<=', double(intmax('uint32'))});

    % Comprobar los indicadores del ultimo byte.
    validateattributes([ultlY ultlCb ultlCr], {'numeric'}, ...
        {'real', 'finite', 'integer', '>=', 0, '<=', 7});

    % Datos generales: 4 bytes por valor.
    um = uint32(m);
    un = uint32(n);
    ucaliQ = uint32(caliQ);
    uTO = uint32(TO);

    % Longitudes de las componentes: 4 bytes por valor.
    uLY = uint32(LY);
    uLCb = uint32(LCb);
    uLCr = uint32(LCr);

    % Indicadores del ultimo byte: 1 byte por valor.
    uultlY = uint8(ultlY);
    uultlCb = uint8(ultlCb);
    uultlCr = uint8(ultlCr);

    % Tamaño esperado del archivo completo en bytes.
    TCprevisto = 31 + LY + LCb + LCr;

    % ---------------PASO 11---------------
    % Crear el archivo binario en little-endian.
    fid = fopen(archivo, 'wb', 'ieee-le');

    if fid == -1
        error('No se ha podido crear el archivo comprimido.');
    end

    try
        % Datos generales: m, n, caliQ y TO.
        escritos = 4 * fwrite(fid, [um un ucaliQ uTO], 'uint32');

        % Componente Y.
        escritos = escritos + 4 * fwrite(fid, uLY, 'uint32');
        escritos = escritos + fwrite(fid, uultlY, 'uint8');
        escritos = escritos + fwrite(fid, bytesY, 'uint8');

        % Componente Cb.
        escritos = escritos + 4 * fwrite(fid, uLCb, 'uint32');
        escritos = escritos + fwrite(fid, uultlCb, 'uint8');
        escritos = escritos + fwrite(fid, bytesCb, 'uint8');

        % Componente Cr.
        escritos = escritos + 4 * fwrite(fid, uLCr, 'uint32');
        escritos = escritos + fwrite(fid, uultlCr, 'uint8');
        escritos = escritos + fwrite(fid, bytesCr, 'uint8');

        % Comprobar que se han escrito todos los bytes previstos.
        if escritos ~= TCprevisto
            error('La escritura del archivo ha quedado incompleta.');
        end

    catch fallo
        fclose(fid);
        rethrow(fallo);
    end

    % Cerrar el archivo y comprobar el cierre.
    estado = fclose(fid);

    if estado ~= 0
        error('No se ha podido cerrar correctamente el archivo.');
    end
    
    % ---------------PASO 12--------------- 
    % Medir el archivo comprimido y calcular RC.
    infoComprimido = dir(archivo);
    TC = infoComprimido.bytes;

    % Contrastar el tamaño real con el previsto.
    if TC ~= TCprevisto
        error('El tamaño del archivo no coincide con el previsto.');
    end

    % RC: porcentaje de espacio ahorrado.
    RC = 100 * (TO - TC) / TO;
end