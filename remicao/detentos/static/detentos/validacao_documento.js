document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form[enctype="multipart/form-data"]');
    const inputArquivo = document.querySelector('input[type="file"]');

    if (!form || !inputArquivo) {
        return;
    }

    const TAMANHO_MAXIMO_MB = 5;
    const TAMANHO_MAXIMO_BYTES = TAMANHO_MAXIMO_MB * 1024 * 1024;
    const EXTENSOES_PERMITIDAS = ['.pdf', '.jpg', '.jpeg', '.png'];

    form.addEventListener('submit', function (evento) {
        const arquivo = inputArquivo.files[0];

        if (!arquivo) {
            return;
        }

        const nomeArquivo = arquivo.name.toLowerCase();
        const extensaoValida = EXTENSOES_PERMITIDAS.some(function (ext) {
            return nomeArquivo.endsWith(ext);
        });

        if (!extensaoValida) {
            evento.preventDefault();
            alert('Erro: apenas arquivos PDF, JPG ou PNG são aceitos.');
            return;
        }

        if (arquivo.size > TAMANHO_MAXIMO_BYTES) {
            evento.preventDefault();
            alert('Erro: o arquivo excede o tamanho máximo de ' + TAMANHO_MAXIMO_MB + ' MB.');
            return;
        }

        if (!nomeArquivo.endsWith('.pdf')) {
            const confirmou = confirm(
                'Atenção: imagens não passam por verificação de assinatura digital ' +
                'e serão marcadas como "Sem Assinatura" automaticamente. ' +
                'Prefira enviar em PDF sempre que possível. Deseja continuar mesmo assim?'
            );
            if (!confirmou) {
                evento.preventDefault();
            }
        }
    });
});