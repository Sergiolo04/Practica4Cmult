function RC = jcom_custom(fname, caliQ)
    % Comprime una imagen utilizando tablas Huffman a medida.
    % fname: nombre del archivo de imagen.
    % caliQ: factor de cuantizacion, entero positivo.
    % RC: porcentaje de espacio ahorrado.

    % PASO 1: validar la calidad y preparar los archivos.
    validateattributes(caliQ, {'numeric'}, ...
        {'scalar', 'real', 'finite', 'integer', 'positive'});

    % Tamaño original en bytes, necesario para calcular RC al final.
    info = dir(fname);
    TO = info.bytes;

    % Nombre del archivo comprimido.
    archivo = 'comprimido.huc';

    % PASO 2: leer y acondicionar la imagen.
    [X, Xamp, tipo, m, n, mamp, namp] = imlee(fname);

    % PASO 3: transformar la imagen mediante DCT.
    Xtrans = imdct(Xamp);

    % PASO 4: cuantizar los coeficientes DCT.
    Xlab = quantmat(Xtrans, caliQ);

    % PASO 5: recorrer los bloques en zigzag.
    XScan = scan(Xlab);

    % PASO 6: construir las tablas a medida y codificar.
    [CodedY, CodedCb, CodedCr, ...
        BITS_Y_DC, HUFFVAL_Y_DC, BITS_Y_AC, HUFFVAL_Y_AC, ...
        BITS_C_DC, HUFFVAL_C_DC, BITS_C_AC, HUFFVAL_C_AC] ...
        = EncodeScans_custom(XScan);


    % PASO 7: empaquetar las secuencias binarias en bytes.
    [bytesY, ultlY]   = bits2bytes(CodedY);
    [bytesCb, ultlCb] = bits2bytes(CodedCb);
    [bytesCr, ultlCr] = bits2bytes(CodedCr);

    % Numero de bytes de cada componente.
    LY  = numel(bytesY);
    LCb = numel(bytesCb);
    LCr = numel(bytesCr);
    
    % PASO 8: preparar la cabecera y las especificaciones Huffman.

    % Comprobar que los datos generales caben en uint32.
    campos32 = [m n caliQ TO LY LCb LCr];

    validateattributes(campos32, {'numeric'}, ...
        {'real', 'finite', 'integer', 'nonnegative', ...
         '<=', double(intmax('uint32'))});

    % Datos generales de la imagen.
    cabecera = uint32([m n caliQ TO]);

    % Agrupar las cuatro especificaciones en un orden fijo:
    % Y_DC, Y_AC, C_DC, C_AC.
    tablasBITS = {BITS_Y_DC, BITS_Y_AC, BITS_C_DC, BITS_C_AC};
    tablasHUFFVAL = {HUFFVAL_Y_DC, HUFFVAL_Y_AC, ...
                     HUFFVAL_C_DC, HUFFVAL_C_AC};

    % Comprobar y completar las especificaciones.
    for k = 1:4
        b = tablasBITS{k};
        b = b(:);  % Asegurar formato columna.

        assert(numel(b) <= 16, ...
            'BITS no puede superar 16 elementos.');

        % Completar con ceros hasta tener 16 posiciones.
        b(end+1:16, 1) = 0;
        tablasBITS{k} = b;

        assert(sum(b) == numel(tablasHUFFVAL{k}), ...
            'BITS y HUFFVAL no son coherentes.');
    end


    % PASO 9: escribir el archivo comprimido.
    fid = fopen(archivo, 'wb', 'ieee-le');

    if fid == -1
        error('No se ha podido crear el archivo comprimido.');
    end

    % Tamaño esperado: cabecera, tablas y componentes.
    % Cabecera: 16 bytes.
    % Cuatro BITS: 4 * 16 * 2 = 128 bytes.
    % Longitud e indicador por componente: 3 * (4 + 1) = 15 bytes.
    TCprevisto = 16 + 128 + 15 + LY + LCb + LCr;

    for k = 1:4
        TCprevisto = TCprevisto + numel(tablasHUFFVAL{k});
    end

    try
        % Datos generales: m, n, caliQ y TO.
        escritos = 4 * fwrite(fid, cabecera, 'uint32');

        % Especificaciones Huffman: Y_DC, Y_AC, C_DC, C_AC.
        for k = 1:4
            escritos = escritos + ...
                2 * fwrite(fid, uint16(tablasBITS{k}), 'uint16');

            escritos = escritos + ...
                fwrite(fid, uint8(tablasHUFFVAL{k}), 'uint8');
        end

        % Componente Y.
        escritos = escritos + 4 * fwrite(fid, uint32(LY), 'uint32');
        escritos = escritos + fwrite(fid, uint8(ultlY), 'uint8');
        escritos = escritos + fwrite(fid, bytesY, 'uint8');

        % Componente Cb.
        escritos = escritos + 4 * fwrite(fid, uint32(LCb), 'uint32');
        escritos = escritos + fwrite(fid, uint8(ultlCb), 'uint8');
        escritos = escritos + fwrite(fid, bytesCb, 'uint8');

        % Componente Cr.
        escritos = escritos + 4 * fwrite(fid, uint32(LCr), 'uint32');
        escritos = escritos + fwrite(fid, uint8(ultlCr), 'uint8');
        escritos = escritos + fwrite(fid, bytesCr, 'uint8');

        % Comprobar que se han escrito todos los bytes.
        if escritos ~= TCprevisto
            error('La escritura del archivo ha quedado incompleta.');
        end

    catch fallo
        fclose(fid);
        rethrow(fallo);
    end

    estado = fclose(fid);

    if estado ~= 0
        error('No se ha podido cerrar correctamente el archivo.');
    end

    % PASO 10: medir el archivo comprimido y calcular RC.
    infoComprimido = dir(archivo);
    TC = infoComprimido.bytes;

    % Comprobar el tamaño real del archivo.
    if TC ~= TCprevisto
        error('El tamaño del archivo no coincide con el previsto.');
    end

    % Porcentaje de espacio ahorrado.
    RC = 100 * (TO - TC) / TO;

end