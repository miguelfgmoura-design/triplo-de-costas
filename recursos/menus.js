(function () {
  var paineis = Array.prototype.slice.call(document.querySelectorAll('.painel'));
  var links = Array.prototype.slice.call(document.querySelectorAll('.menus a'));
  var posicoes = {};
  var atual = null;

  function subir(y) {
    window.scrollTo({ top: y, behavior: 'instant' });
  }
  function mostrar() {
    var pedido = location.hash.slice(1);
    var id = paineis.some(function (p) { return p.id === pedido; }) ? pedido : paineis[0].id;
    if (id === atual) return;
    if (atual) posicoes[atual] = window.pageYOffset;
    paineis.forEach(function (p) { p.classList.toggle('ativo', p.id === id); });
    links.forEach(function (a) {
      if (a.getAttribute('href') === '#' + id) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    atual = id;
    subir(posicoes[id] || 0);
  }
  window.addEventListener('hashchange', mostrar);
  links.forEach(function (a) {
    a.addEventListener('click', function () {
      if (a.getAttribute('href') === '#' + atual) subir(0);
    });
  });
  mostrar();

  var escolha = document.getElementById('escolha-equipa');
  if (!escolha) return;
  var fichas = Array.prototype.slice.call(document.querySelectorAll('.ficha'));
  var ponto = document.getElementById('escolha-ponto');
  var nome = document.getElementById('escolha-nome');
  function mostrarEquipa() {
    var opcao = escolha.options[escolha.selectedIndex];
    fichas.forEach(function (f) { f.classList.toggle('ativa', f.getAttribute('data-equipa') === escolha.value); });
    ponto.className = 'ponto ' + opcao.getAttribute('data-classe');
    nome.textContent = opcao.textContent;
  }
  escolha.addEventListener('change', mostrarEquipa);
  mostrarEquipa();
})();
