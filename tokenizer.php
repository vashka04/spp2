<?php
if ($argc < 2) {
    die("Error: No input file specified\n");
}

$filename = $argv[1];
if (!file_exists($filename)) {
    die("Error: File not found\n");
}

$code = file_get_contents($filename);
$tokens = token_get_all($code);

foreach ($tokens as $token) {
    if (is_array($token)) {
        // $token[0] — это ID токена (например, T_VARIABLE, T_ECHO)
        // token_name() переводит ID в понятную строку (например, "T_IF")
        // $token[1] — сам текст токена (например, "$my_var", "if")
        $tokenName = token_name($token[0]);
        $tokenText = $token[1];
        //if ($tokenName === 'T_WHITESPACE' || $tokenName === 'T_OPEN_TAG' || $tokenName === 'T_CLOSE_TAG') {
        //    continue;
        //}
        // Выводим в формате: ИМЯ_ТОКЕНА===ТЕКСТ
        echo $tokenName . "===" . $tokenText . "\n";
    } else {
        // Если это одиночный символ (например, ';', '+', '{', ')')
        // Выводим в формате: CHARACTER===символ
        echo "CHARACTER===" . $token . "\n";
    }
}
?>
