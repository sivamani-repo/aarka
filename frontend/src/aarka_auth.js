
document.addEventListener("DOMContentLoaded", function () {

    const authPage = document.getElementById("aarkaAuth");

    if (!authPage) return;

    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    const showRegister = document.getElementById("showRegister");
    const showLogin = document.getElementById("showLogin");

    // Switch to registration
    showRegister.addEventListener("click", function () {

        authPage.classList.add("is-register");

        loginForm.hidden = true;
        registerForm.hidden = false;

        registerForm.querySelector("input").focus();
    });

    // Switch back to login
    showLogin.addEventListener("click", function () {

        authPage.classList.remove("is-register");

        registerForm.hidden = true;
        loginForm.hidden = false;

        loginForm.querySelector("input").focus();
    });

    // Show / Hide passwords
    document.querySelectorAll(".password-toggle")
        .forEach(function (button) {

            button.addEventListener("click", function () {

                const input = document.getElementById(
                    button.dataset.target
                );

                if (!input) return;

                const isPassword = input.type === "password";

                input.type = isPassword ? "text" : "password";
                button.textContent = isPassword ? "Hide" : "Show";
            });
        });

    // Confirm password validation
    const password = document.getElementById("registerPassword");
    const confirmPassword = document.getElementById("confirmPassword");

    function validatePassword() {

        if (!password || !confirmPassword) return;

        if (password.value !== confirmPassword.value) {
            confirmPassword.setCustomValidity(
                "Passwords do not match."
            );
        } else {
            confirmPassword.setCustomValidity("");
        }
    }

    password.addEventListener("input", validatePassword);
    confirmPassword.addEventListener("input", validatePassword);

});
