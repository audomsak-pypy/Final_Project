/**
 * theme.js — ตรวจจับ prefers-color-scheme และส่ง event เข้าระบบธีม
 */
(function() {
    function getSystemTheme() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    window.getSystemTheme = getSystemTheme;

    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            var themeStore = document.getElementById('store-theme');
            if (themeStore) {
                // Trigger an input event or let Dash clientside callback handle it
                window.dispatchEvent(new CustomEvent('themeChanged', { detail: e.matches ? 'dark' : 'light' }));
            }
        });
    }
})();
