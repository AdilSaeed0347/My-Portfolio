function loadComponent(containerId, filePath) {
    fetch(filePath)
        .then(res => res.text())
        .then(data => document.getElementById(containerId).innerHTML = data)
        .catch(err => console.error(`Error loading ${filePath}:`, err));
}

function loadComponent(containerId, filePath) {
    fetch(filePath)
        .then(res => res.text())
        .then(data => document.getElementById(containerId).innerHTML = data)
        .catch(err => console.error(`Error loading ${filePath}:`, err));
}

// Load Footer for all pages
loadComponent('footer-container', '../components/Footer.html');


