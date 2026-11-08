(function () {
  function formatar(v) {
    var s = Math.abs(v).toFixed(1).replace(/\.0$/, '').replace('.', ',');
    s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return (v < 0 ? '−' : '') + s;
  }
  document.querySelectorAll('.grafico').forEach(function (f) {
    var d = JSON.parse(f.getAttribute('data-d'));
    var svg = f.querySelector('svg'), mira = f.querySelector('.mira'), dica = f.querySelector('.dica');
    var atual = -1;
    function esconder() {
      atual = -1;
      mira.style.visibility = 'hidden';
      dica.hidden = true;
    }
    function mostrar(i) {
      atual = i;
      var pos = d.x0 + (d.x1 - d.x0) * (d.n > 1 ? i / (d.n - 1) : 0.5);
      mira.setAttribute('x1', pos);
      mira.setAttribute('x2', pos);
      mira.style.visibility = 'visible';
      dica.textContent = '';
      var dia = document.createElement('div');
      dia.className = 'd-dia';
      dia.textContent = d.datas[i];
      dica.appendChild(dia);
      d.series.slice().sort(function (a, b) { return b.v[i] - a.v[i]; }).forEach(function (s) {
        var linha = document.createElement('div');
        var chave = document.createElement('i');
        chave.className = 'chave ' + s.classe;
        var valor = document.createElement('b');
        valor.textContent = formatar(s.v[i]);
        var nome = document.createElement('span');
        nome.className = 'd-nome';
        nome.textContent = s.nome;
        linha.appendChild(chave);
        linha.appendChild(valor);
        linha.appendChild(nome);
        dica.appendChild(linha);
      });
      dica.hidden = false;
      var largura = svg.getBoundingClientRect().width;
      var px = pos * largura / d.largura;
      var esquerda = px + 10;
      if (esquerda + dica.offsetWidth > largura) esquerda = px - 10 - dica.offsetWidth;
      dica.style.left = Math.max(0, esquerda) + 'px';
    }
    function doPonteiro(ev) {
      var r = svg.getBoundingClientRect();
      var x = (ev.clientX - r.left) * d.largura / r.width;
      var i = d.n > 1 ? Math.round((x - d.x0) / (d.x1 - d.x0) * (d.n - 1)) : 0;
      mostrar(Math.max(0, Math.min(d.n - 1, i)));
    }
    svg.addEventListener('pointerdown', doPonteiro);
    svg.addEventListener('pointermove', doPonteiro);
    svg.addEventListener('pointerleave', function (ev) { if (ev.pointerType === 'mouse') esconder(); });
    document.addEventListener('pointerdown', function (ev) { if (!svg.contains(ev.target)) esconder(); });
    svg.addEventListener('focus', function () { mostrar(d.n - 1); });
    svg.addEventListener('blur', esconder);
    svg.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowLeft' && atual > 0) mostrar(atual - 1);
      if (ev.key === 'ArrowRight' && atual < d.n - 1) mostrar(atual + 1);
    });
  });
})();
