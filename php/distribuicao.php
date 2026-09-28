<?php
declare(strict_types=1);

require dirname(__DIR__) . '/vendor/autoload.php';

use NFePHP\Common\Certificate;
use NFePHP\NFe\Tools;

function arg(array $args, string $name): string {
    $key = array_search("--{$name}", $args, true);
    if ($key === false || !isset($args[$key + 1])) {
        throw new InvalidArgumentException("Parâmetro obrigatório ausente: --{$name}");
    }
    return (string)$args[$key + 1];
}

function emit(array $data): void {
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . PHP_EOL;
}

function onlyDigits(string $value): string {
    return preg_replace('/\D+/', '', $value) ?? '';
}

$ufCodes = [
    'RO'=>'11','AC'=>'12','AM'=>'13','RR'=>'14','PA'=>'15','AP'=>'16','TO'=>'17',
    'MA'=>'21','PI'=>'22','CE'=>'23','RN'=>'24','PB'=>'25','PE'=>'26','AL'=>'27',
    'SE'=>'28','BA'=>'29','MG'=>'31','ES'=>'32','RJ'=>'33','SP'=>'35','PR'=>'41',
    'SC'=>'42','RS'=>'43','MS'=>'50','MT'=>'51','GO'=>'52','DF'=>'53'
];

try {
    $cnpj = onlyDigits(arg($argv, 'cnpj'));
    $uf = strtoupper(arg($argv, 'uf'));
    $certPath = arg($argv, 'cert');
    $password = arg($argv, 'password');
    $output = rtrim(arg($argv, 'output'), DIRECTORY_SEPARATOR);

    if (strlen($cnpj) !== 14) throw new RuntimeException('CNPJ inválido.');
    if (!isset($ufCodes[$uf])) throw new RuntimeException('UF inválida.');
    if (!is_file($certPath)) throw new RuntimeException('Certificado não encontrado.');
    if (!is_dir($output) && !mkdir($output, 0775, true) && !is_dir($output)) {
        throw new RuntimeException('Não foi possível criar a pasta de saída.');
    }

    $stateFile = $output . DIRECTORY_SEPARATOR . '.nfe-state-' . $cnpj . '.json';
    $state = is_file($stateFile) ? json_decode((string)file_get_contents($stateFile), true) : [];
    $ultNSU = str_pad((string)($state['ultNSU'] ?? '0'), 15, '0', STR_PAD_LEFT);

    $config = [
        'atualizacao' => date('Y-m-d H:i:s'),
        'tpAmb' => 1,
        'razaosocial' => 'DownloadXMLNf-e',
        'siglaUF' => $uf,
        'cnpj' => $cnpj,
        'schemes' => 'PL_009_V4',
        'versao' => '4.00',
        'tokenIBPT' => '',
        'CSC' => '',
        'CSCid' => '',
        'proxyConf' => ['proxyIp'=>'','proxyPort'=>'','proxyUser'=>'','proxyPass'=>'']
    ];

    $certificate = Certificate::readPfx((string)file_get_contents($certPath), $password);
    $tools = new Tools(json_encode($config, JSON_UNESCAPED_UNICODE), $certificate);
    $tools->model('55');
    $tools->setEnvironment(1);

    $maxNSU = $ultNSU;
    $loops = 0;
    $xmlCompletos = 0;
    $resumos = 0;
    $eventos = 0;
    $loopLimit = 12;

    emit(['status'=>'inicio','ultNSU'=>$ultNSU]);

    do {
        $loops++;
        if ($loops > $loopLimit) break;

        $resp = $tools->sefazDistDFe((int)$ultNSU);
        $dom = new DOMDocument();
        if (!$dom->loadXML($resp)) throw new RuntimeException('Resposta XML inválida da SEFAZ.');

        $node = $dom->getElementsByTagName('retDistDFeInt')->item(0);
        if (!$node) throw new RuntimeException('Retorno retDistDFeInt não encontrado.');

        $value = static fn(string $tag): string => $node->getElementsByTagName($tag)->item(0)?->nodeValue ?? '';
        $cStat = $value('cStat');
        $xMotivo = $value('xMotivo');
        $novoUltNSU = $value('ultNSU') ?: $ultNSU;
        $maxNSU = $value('maxNSU') ?: $novoUltNSU;

        emit(['status'=>'consulta','cStat'=>$cStat,'motivo'=>$xMotivo,'ultNSU'=>$novoUltNSU,'maxNSU'=>$maxNSU]);

        $lote = $node->getElementsByTagName('loteDistDFeInt')->item(0);
        if ($lote) {
            foreach ($lote->getElementsByTagName('docZip') as $doc) {
                $nsu = $doc->getAttribute('NSU');
                $schema = $doc->getAttribute('schema');
                $decoded = base64_decode(trim($doc->nodeValue), true);
                $content = $decoded === false ? false : gzdecode($decoded);
                if ($content === false) continue;

                $type = str_starts_with($schema, 'procNFe') ? 'xml' :
                    (str_starts_with($schema, 'resNFe') ? 'resumos' : 'eventos');
                $dir = $output . DIRECTORY_SEPARATOR . $type;
                if (!is_dir($dir)) mkdir($dir, 0775, true);

                $name = $nsu . '-' . preg_replace('/[^A-Za-z0-9_.-]/', '_', $schema) . '.xml';
                file_put_contents($dir . DIRECTORY_SEPARATOR . $name, $content);

                if ($type === 'xml') $xmlCompletos++;
                elseif ($type === 'resumos') $resumos++;
                else $eventos++;
            }
        }

        $ultNSU = str_pad($novoUltNSU, 15, '0', STR_PAD_LEFT);
        file_put_contents($stateFile, json_encode([
            'ultNSU'=>$ultNSU,
            'maxNSU'=>$maxNSU,
            'updated_at'=>date(DATE_ATOM)
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));

        if (in_array($cStat, ['137', '656'], true) || $ultNSU === str_pad($maxNSU, 15, '0', STR_PAD_LEFT)) break;
        sleep(2);
    } while (true);

    emit([
        'status'=>'concluido','xml_completos'=>$xmlCompletos,'resumos'=>$resumos,
        'eventos'=>$eventos,'ultNSU'=>$ultNSU,'maxNSU'=>$maxNSU,'consultas'=>$loops
    ]);
    exit(0);
} catch (Throwable $e) {
    emit(['status'=>'erro','mensagem'=>$e->getMessage()]);
    exit(1);
}
