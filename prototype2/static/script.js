// Initialize AOS (Animate On Scroll)
AOS.init({
    duration: 800, // animation duration in milliseconds
    once: true, // whether animation should happen only once - while scrolling down
});

// Navbar scroll effect
const navbar = document.getElementById('mainNavbar');
const signInBtn = document.getElementById('signInBtn');
window.onscroll = () => {
    if (window.scrollY > 50) {
        navbar.classList.add('navbar-scrolled');
        // Change navbar text color scheme for light background
        navbar.classList.remove('navbar-dark');
        navbar.classList.add('navbar-light');
        // Change sign-in button style
        signInBtn.classList.remove('btn-outline-primary', 'text-white');
        signInBtn.classList.add('btn-primary');
    } else {
        navbar.classList.remove('navbar-scrolled');
            // Change navbar text color scheme for dark background
        navbar.classList.remove('navbar-light');
        navbar.classList.add('navbar-dark');
        // Revert sign-in button style
        signInBtn.classList.remove('btn-primary');
        signInBtn.classList.add('btn-outline-primary', 'text-white');
    }
};

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        // Do not prevent default for external links or non-anchor links
        if (this.getAttribute('href').startsWith('#')) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});
// Initialize AOS (Animate On Scroll)
AOS.init({
    duration: 800,
    once: true,
});
