# Factory State & Artifact Index

A FlashSoft mantém o histórico de entregas aprovadas em actory_state/. Cada run bem-sucedido gera:

- actory_state/releases/<run_id>.json: manifesto com hash SHA256, branch, pacote zipado e testes executados.
- actory_state/state.json: índice agregado apontando para o último release (latest) e para todos os manifestos.

## Como funciona o pacote

1. Após o pipeline passar por todos os gates, criamos um zip em dist/autobot_<run_id>.zip contendo rtifacts/ e logs/ daquela execução.
2. O SHA256 desse pacote é calculado e escrito no manifesto.
3. Para publicar oficialmente, faça upload do zip num GitHub Release com a elease_tag indicada no manifesto (por exemplo staging-<run_id>) e use o mesmo nome de asset.
4. Atualize (opcionalmente) o campo elease_asset no manifesto para apontar para o URL definitivo do Release.

Assim garantimos integridade (hash), rastreabilidade (manifests versionados) e reuso seguro de artefatos.
