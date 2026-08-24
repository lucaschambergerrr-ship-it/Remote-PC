let socket = null;

const authView = document.getElementById('auth-view');
const dashboardView = document.getElementById('dashboard-view');
const authForm = document.getElementById('auth-form');
const passcodeInput = document.getElementById('passcode-input');
const authError = document.getElementById('auth-error');

const remoteStream = document.getElementById('remote-stream');
const viewportContainer = document.getElementById('viewport-container');
const btnToggleFs = document.getElementById('btn-toggle-fs');

// Manejo de Inicio de Sesión
authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    authError.classList.add('hidden');
    
    const code = passcodeInput.value.trim();

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });

        const data = await response.json();

        if (data.success) {
            // Cambiar vista
            authView.classList.remove('view-active');
            authView.classList.add('view-hidden');
            
            dashboardView.classList.remove('view-hidden');
            dashboardView.classList.add('view-active');

            // Conectar sockets
            connectSocket();
        } else {
            authError.textContent = "Código incorrecto. Inténtalo de nuevo.";
            authError.classList.remove('hidden');
        }
    } catch (err) {
        authError.textContent = "No se pudo conectar con la PC.";
        authError.classList.remove('hidden');
    }
});

function connectSocket() {
    socket = io();

    // Recibir transmisión de video
    socket.on('screen_frame', (data) => {
        remoteStream.src = 'data:image/jpeg;base64,' + data.image;
    });

    // Touchpad Relativo
    let lastX = 0;
    let lastY = 0;
    let activeTouch = false;

    viewportContainer.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            activeTouch = true;
            lastX = e.touches[0].clientX;
            lastY = e.touches[0].clientY;
        }
    }, { passive: true });

    viewportContainer.addEventListener('touchmove', (e) => {
        if (!activeTouch || e.touches.length !== 1) return;

        const currentX = e.touches[0].clientX;
        const currentY = e.touches[0].clientY;

        const dx = currentX - lastX;
        const dy = currentY - lastY;

        lastX = currentX;
        lastY = currentY;

        if (Math.abs(dx) > 0 || Math.abs(dy) > 0) {
            socket.emit('mouse_move', { dx, dy });
        }
    }, { passive: true });

    viewportContainer.addEventListener('touchend', () => {
        activeTouch = false;
    });

    // Botones del Ratón
    document.getElementById('click-left').onclick = () => socket.emit('mouse_click', { action: 'left' });
    document.getElementById('click-right').onclick = () => socket.emit('mouse_click', { action: 'right' });
    document.getElementById('click-double').onclick = () => socket.emit('mouse_click', { action: 'double' });

    // Rueda del Ratón (Scroll)
    let scrollTimer = null;
    function triggerScroll(dir) {
        socket.emit('mouse_scroll', { direction: dir });
    }

    const scrollUpBtn = document.getElementById('scroll-up');
    const scrollDownBtn = document.getElementById('scroll-down');

    ['mousedown', 'touchstart'].forEach(evt => {
        scrollUpBtn.addEventListener(evt, (e) => {
            e.preventDefault();
            triggerScroll('up');
            scrollTimer = setInterval(() => triggerScroll('up'), 100);
        });
        scrollDownBtn.addEventListener(evt, (e) => {
            e.preventDefault();
            triggerScroll('down');
            scrollTimer = setInterval(() => triggerScroll('down'), 100);
        });
    });

    ['mouseup', 'mouseleave', 'touchend', 'touchcancel'].forEach(evt => {
        scrollUpBtn.addEventListener(evt, () => clearInterval(scrollTimer));
        scrollDownBtn.addEventListener(evt, () => clearInterval(scrollTimer));
    });

    // Teclas del Teclado
    document.querySelectorAll('.key-btn').forEach(btn => {
        btn.onclick = () => {
            const key = btn.getAttribute('data-key');
            socket.emit('key_press', { key });
        };
    });
}

// Pantalla Completa
btnToggleFs.addEventListener('click', () => {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().then(() => {
            document.body.classList.add('fullscreen-mode');
        }).catch(() => {});
    } else {
        document.exitFullscreen().then(() => {
            document.body.classList.remove('fullscreen-mode');
        }).catch(() => {});
    }
});