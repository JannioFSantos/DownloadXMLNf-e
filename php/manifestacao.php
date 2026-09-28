<?php
declare(strict_types=1);
require dirname(__DIR__) . '/vendor/autoload.php';
use NFePHP\Common\Certificate;
use NFePHP\NFe\Tools;

function a(array $v,string $n):string{$k=array_search("--$n",$v,true);if($k===false||!isset($v[$k+1]))throw new InvalidArgumentException("Parâmetro ausente: --$n");return(string)$v[$k+1];}
function out(array $v):void{echo json_encode($v,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES).PHP_EOL;}
try{
 $cnpj=preg_replace('/\D+/','',a($argv,'cnpj')); $uf=strtoupper(a($argv,'uf')); $cert=a($argv,'cert'); $pass=a($argv,'password'); $chave=preg_replace('/\D+/','',a($argv,'chave'));
 if(strlen($cnpj)!==14||strlen($chave)!==44)throw new RuntimeException('CNPJ ou chave inválida.');
 $config=['atualizacao'=>date('Y-m-d H:i:s'),'tpAmb'=>1,'razaosocial'=>'DownloadXMLNf-e','siglaUF'=>$uf,'cnpj'=>$cnpj,'schemes'=>'PL_009_V4','versao'=>'4.00','tokenIBPT'=>'','CSC'=>'','CSCid'=>'','proxyConf'=>['proxyIp'=>'','proxyPort'=>'','proxyUser'=>'','proxyPass'=>'']];
 $tools=new Tools(json_encode($config,JSON_UNESCAPED_UNICODE),Certificate::readPfx((string)file_get_contents($cert),$pass));
 $tools->model('55'); $tools->setEnvironment(1);
 // 210210 = Ciência da Operação. A chamada só ocorre após confirmação explícita na interface.
 $resp=$tools->sefazManifesta($chave,1,'',date('Y-m-d\TH:i:sP'));
 $dom=new DOMDocument(); $dom->loadXML($resp);
 $c=$dom->getElementsByTagName('cStat'); $m=$dom->getElementsByTagName('xMotivo');
 out(['status'=>'concluido','cStat'=>$c->length?$c->item($c->length-1)->nodeValue:'','xMotivo'=>$m->length?$m->item($m->length-1)->nodeValue:'','chave'=>$chave]);
}catch(Throwable $e){out(['status'=>'erro','mensagem'=>$e->getMessage()]);exit(1);}
