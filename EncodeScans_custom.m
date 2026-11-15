function [CodedY, CodedCb, CodedCr, ...
    BITS_Y_DC, HUFFVAL_Y_DC, BITS_Y_AC, HUFFVAL_Y_AC, ...
    BITS_C_DC, HUFFVAL_C_DC, BITS_C_AC, HUFFVAL_C_AC] ...
    = EncodeScans_custom(XScan)

    % Separar las tres componentes.
    YScan  = XScan(:,:,1);
    CbScan = XScan(:,:,2);
    CrScan = XScan(:,:,3);

    % Preparar los símbolos DC y AC de cada componente.
    [Y_DC_CP, Y_AC_ZCP]   = CollectScan(YScan);
    [Cb_DC_CP, Cb_AC_ZCP] = CollectScan(CbScan);
    [Cr_DC_CP, Cr_AC_ZCP] = CollectScan(CrScan);

    % Contar las frecuencias de luminancia.
    FREQ_Y_DC = Freq256(Y_DC_CP(:,1));
    FREQ_Y_AC = Freq256(Y_AC_ZCP(:,1));

    % Contar conjuntamente las frecuencias de Cb y Cr.
    FREQ_C_DC = Freq256([Cb_DC_CP(:,1); Cr_DC_CP(:,1)]);
    FREQ_C_AC = Freq256([Cb_AC_ZCP(:,1); Cr_AC_ZCP(:,1)]);

    % Generar las especificaciones Huffman de luminancia.
    [BITS_Y_DC, HUFFVAL_Y_DC] = HSpecTables(FREQ_Y_DC);
    [BITS_Y_AC, HUFFVAL_Y_AC] = HSpecTables(FREQ_Y_AC);

    % Generar las especificaciones Huffman de crominancia.
    [BITS_C_DC, HUFFVAL_C_DC] = HSpecTables(FREQ_C_DC);
    [BITS_C_AC, HUFFVAL_C_AC] = HSpecTables(FREQ_C_AC);

    % Tabla de codificacion DC de luminancia.
    [HUFFSIZE, HUFFCODE] = HCodeTables(BITS_Y_DC, HUFFVAL_Y_DC);
    [EHUFCO, EHUFSI] = HCodingTables(HUFFSIZE, HUFFCODE, HUFFVAL_Y_DC);
    ehuf_Y_DC = [EHUFCO EHUFSI];

    % Tabla de codificacion AC de luminancia.
    [HUFFSIZE, HUFFCODE] = HCodeTables(BITS_Y_AC, HUFFVAL_Y_AC);
    [EHUFCO, EHUFSI] = HCodingTables(HUFFSIZE, HUFFCODE, HUFFVAL_Y_AC);
    ehuf_Y_AC = [EHUFCO EHUFSI];

    % Tabla de codificacion DC de crominancia.
    [HUFFSIZE, HUFFCODE] = HCodeTables(BITS_C_DC, HUFFVAL_C_DC);
    [EHUFCO, EHUFSI] = HCodingTables(HUFFSIZE, HUFFCODE, HUFFVAL_C_DC);
    ehuf_C_DC = [EHUFCO EHUFSI];

    % Tabla de codificacion AC de crominancia.
    [HUFFSIZE, HUFFCODE] = HCodeTables(BITS_C_AC, HUFFVAL_C_AC);
    [EHUFCO, EHUFSI] = HCodingTables(HUFFSIZE, HUFFCODE, HUFFVAL_C_AC);
    ehuf_C_AC = [EHUFCO EHUFSI];

    % Codificar luminancia con sus tablas DC y AC.
    CodedY = EncodeSingleScan( ...
        YScan, Y_DC_CP, Y_AC_ZCP, ehuf_Y_DC, ehuf_Y_AC);

    % Codificar ambas crominancias con las tablas compartidas.
    CodedCb = EncodeSingleScan( ...
        CbScan, Cb_DC_CP, Cb_AC_ZCP, ehuf_C_DC, ehuf_C_AC);

    CodedCr = EncodeSingleScan( ...
        CrScan, Cr_DC_CP, Cr_AC_ZCP, ehuf_C_DC, ehuf_C_AC);

end