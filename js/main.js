document.addEventListener('DOMContentLoaded', () => {
  const copyButtons = document.querySelectorAll('[data-copy-code]');
  copyButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const code = btn.getAttribute('data-copy-code');
      if (code) {
        copyCodeToClipboard(code, btn);
      }
    });
  });
});

function copyCodeToClipboard(codeText, buttonElement) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(codeText)
      .then(() => handleCopySuccess(codeText, buttonElement))
      .catch(() => fallbackCopyText(codeText, buttonElement));
  } else {
    fallbackCopyText(codeText, buttonElement);
  }
}

function fallbackCopyText(text, buttonElement) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    const successful = document.execCommand('copy');
    if (successful) {
      handleCopySuccess(text, buttonElement);
    }
  } catch (err) {
    console.error('Fallback copy command failed', err);
  }
  document.body.removeChild(textArea);
}

function handleCopySuccess(codeText, buttonElement) {
  const originalHtml = buttonElement.innerHTML;
  
  buttonElement.classList.add('copied');
  buttonElement.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <span>Copied!</span>
  `;

  let toast = document.getElementById('copy-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'copy-toast';
    toast.className = 'toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#34D399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      <span id="toast-message"></span>
    `;
    document.body.appendChild(toast);
  }

  const toastMessage = toast.querySelector('#toast-message');
  if (toastMessage) {
    toastMessage.textContent = `Code "${codeText}" copied to clipboard`;
  }
  
  toast.classList.add('show');

  setTimeout(() => {
    buttonElement.classList.remove('copied');
    buttonElement.innerHTML = originalHtml;
  }, 2500);

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}
