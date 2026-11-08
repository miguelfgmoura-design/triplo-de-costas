(function () {
  var raiz = document.getElementById('comentario-navega');
  if (!raiz) return;
  var entradas = JSON.parse(raiz.getAttribute('data-entradas'));
  var texto = document.getElementById('comentario-texto');
  var rotulo = raiz.querySelector('.cn-dia');
  var antes = raiz.querySelector('.cn-antes');
  var depois = raiz.querySelector('.cn-depois');
  var recente = document.getElementById('comentario-recente');
  var ultimo = entradas.length - 1;
  var atual = ultimo;
  var guardados = {};
  var pedido = 0;
  guardados[ultimo] = texto.innerHTML;

  function botoes() {
    rotulo.textContent = entradas[atual].r;
    antes.disabled = atual === 0;
    depois.disabled = atual === ultimo;
    recente.hidden = atual === ultimo;
  }
  function mostrar(html) {
    texto.innerHTML = html;
    texto.classList.remove('a-carregar');
  }
  function ir(n) {
    if (n < 0 || n > ultimo) return;
    atual = n;
    botoes();
    var este = ++pedido;
    if (guardados[n] !== undefined) {
      mostrar(guardados[n]);
      return;
    }
    texto.classList.add('a-carregar');
    fetch('comentarios/' + entradas[n].d + '.json')
      .then(function (r) {
        if (!r.ok) throw new Error('falhou');
        return r.json();
      })
      .then(function (d) {
        guardados[n] = d.html;
        if (este === pedido) mostrar(d.html);
      })
      .catch(function () {
        if (este === pedido) mostrar('<p class="nota">Não foi possível abrir o comentário deste dia. Tenta outra vez.</p>');
      });
  }
  antes.addEventListener('click', function () { ir(atual - 1); });
  depois.addEventListener('click', function () { ir(atual + 1); });
  recente.addEventListener('click', function () { ir(ultimo); });
  raiz.hidden = false;
  botoes();
})();
