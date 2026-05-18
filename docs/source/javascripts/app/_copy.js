function copyToClipboard(container) {
  const el = document.createElement('textarea');
  el.value = container.textContent.replace(/\n$/, '');
  document.body.appendChild(el);
  el.select();
  document.execCommand('copy');
  document.body.removeChild(el);
}

function setupCodeCopy() {
  $('pre.highlight').prepend('<div class="copy-clipboard"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><title>Copy to Clipboard</title><path d="M18 6v-6h-18v18h6v6h18v-18h-6zm-12 10h-4v-14h14v4h-10v10zm16 6h-14v-14h14v14z"></path></svg></div>');
  $('.copy-clipboard').on('click', function() {
    copyToClipboard(this.parentNode.children[1]);
    // Flash "Copied" feedback so the user knows the click registered —
    // CSS handles the visuals via .is-copied; we just toggle the class.
    var btn = this;
    btn.classList.add('is-copied');
    if (btn._copyTimer) { clearTimeout(btn._copyTimer); }
    btn._copyTimer = setTimeout(function () {
      btn.classList.remove('is-copied');
      btn._copyTimer = null;
    }, 1400);
  });
}
