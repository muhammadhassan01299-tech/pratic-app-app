const form = document.querySelector('#authForm');
const loginTab = document.querySelector('#loginTab');
const signupTab = document.querySelector('#signupTab');
const nameLabel = document.querySelector('#nameLabel');
const nameInput = document.querySelector('#fullName');
const emailInput = document.querySelector('#email');
const passwordInput = document.querySelector('#password');
const title = document.querySelector('#formTitle');
const subtitle = document.querySelector('#formSubtitle');
const submitText = document.querySelector('#submitText');
const submitBtn = document.querySelector('#submitBtn');
const message = document.querySelector('#message');
let mode = 'login';

function setMode(next) {
  mode = next;
  const signup = mode === 'signup';
  loginTab.classList.toggle('active', !signup);
  signupTab.classList.toggle('active', signup);
  nameLabel.classList.toggle('hidden', !signup);
  nameInput.required = signup;
  passwordInput.autocomplete = signup ? 'new-password' : 'current-password';
  title.textContent = signup ? 'Create your account' : 'Welcome back';
  subtitle.textContent = signup ? 'A fresh start is just one step away.' : 'Sign in to continue to your space.';
  submitText.textContent = signup ? 'Create account' : 'Sign in';
  message.textContent = '';
  message.className = 'message';
}
loginTab.addEventListener('click', () => setMode('login'));
signupTab.addEventListener('click', () => setMode('signup'));
document.querySelector('#togglePassword').addEventListener('click', () => {
  passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  message.textContent = '';
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  if (mode === 'signup' && nameInput.value.trim().length < 2) {
    message.textContent = 'Please enter your full name.'; return;
  }
  if (password.length < 8) {
    message.textContent = 'Password must be at least 8 characters.'; return;
  }
  submitBtn.disabled = true;
  submitText.textContent = mode === 'signup' ? 'Creating account…' : 'Signing in…';
  try {
    const response = await fetch(`/api/auth/${mode}`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(mode === 'signup'
        ? {full_name: nameInput.value.trim(), email, password}
        : {email, password})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
    if (document.querySelector('#remember').checked) {
      localStorage.setItem('luma_token', data.access_token);
      sessionStorage.removeItem('luma_token');
    } else {
      sessionStorage.setItem('luma_token', data.access_token);
      localStorage.removeItem('luma_token');
    }
    message.className = 'message success';
    message.textContent = `${data.message} Hello, ${data.user.full_name}!`;
    form.reset();
    passwordInput.type = 'password';
  } catch (error) {
    message.className = 'message';
    message.textContent = error.message || 'Could not connect to the server.';
  } finally {
    submitBtn.disabled = false;
    submitText.textContent = mode === 'signup' ? 'Create account' : 'Sign in';
  }
});
