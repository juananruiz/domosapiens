document.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('/templates/header.html');
        const headerHtml = await response.text();
        
        // Crear un contenedor para el header
        const headerContainer = document.createElement('div');
        headerContainer.innerHTML = headerHtml;
        
        // Insertar el header al principio del body
        document.body.insertBefore(headerContainer, document.body.firstChild);
        
        // Marcar el ítem de menú activo
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    } catch (error) {
        console.error('Error cargando el header:', error);
    }
});
